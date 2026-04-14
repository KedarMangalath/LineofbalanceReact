"""Pharmacy LOB metrics tool."""

import json
from datetime import datetime, timedelta

from hospital_lob.tools._compat import BaseTool
from pydantic import BaseModel, Field

from hospital_lob.config.settings import PharmacyStageEnum
from hospital_lob.models.pharmacy import PharmacyMetrics, PharmacyOrder


class PharmacyInput(BaseModel):
    time_window_hours: int = Field(default=24, description="Time window for analysis")


class PharmacyMetricsTool(BaseTool):
    name: str = "pharmacy_metrics"
    description: str = (
        "Calculates pharmacy Line of Balance metrics including MTAT, "
        "verification wait times, compounding times, and queue depths per stage."
    )
    args_schema: type[BaseModel] = PharmacyInput

    def _run(self, time_window_hours: int = 24) -> str:
        from hospital_lob.data.store import get_store

        store = get_store()
        now = datetime.now()
        orders = store.get_pharmacy_orders(start_time=now - timedelta(hours=time_window_hours))

        metrics = compute_pharmacy_metrics(orders, time_window_hours)
        return metrics.model_dump_json(indent=2)


def compute_pharmacy_metrics(
    orders: list[PharmacyOrder],
    time_window_hours: int = 24,
) -> PharmacyMetrics:
    """Compute pharmacy LOB metrics."""
    now = datetime.now()

    # MTAT
    completed = [o for o in orders if o.is_complete and o.mtat_minutes]
    mtat_values = [o.mtat_minutes for o in completed if o.mtat_minutes]
    avg_mtat = sum(mtat_values) / len(mtat_values) if mtat_values else 0

    # Verification wait
    verify_waits = [o.verification_wait_minutes for o in orders if o.verification_wait_minutes]
    avg_verify = sum(verify_waits) / len(verify_waits) if verify_waits else 0

    # Compounding time
    compound_times = []
    for o in orders:
        if o.compounding_start and o.compounding_end:
            dur = (o.compounding_end - o.compounding_start).total_seconds() / 60
            compound_times.append(dur)
    avg_compound = sum(compound_times) / len(compound_times) if compound_times else 0

    # Queue depths
    queues = {stage: 0 for stage in PharmacyStageEnum}
    for o in orders:
        if not o.is_complete:
            queues[o.current_stage] += 1

    # Throughput per stage per hour
    throughput = {stage: 0.0 for stage in PharmacyStageEnum}
    for o in completed:
        throughput[PharmacyStageEnum.ORDER_RECEIPT] += 1
        if o.verification_time:
            throughput[PharmacyStageEnum.VERIFICATION] += 1
        if o.compounding_end:
            throughput[PharmacyStageEnum.COMPOUNDING] += 1
        if o.dispensed_time:
            throughput[PharmacyStageEnum.LABELLING] += 1
        if o.administered_time:
            throughput[PharmacyStageEnum.ADMINISTRATION] += 1

    for stage in throughput:
        throughput[stage] /= max(time_window_hours, 1)

    # Find pharmacy bottleneck
    active_orders = [o for o in orders if not o.is_complete]
    if active_orders:
        stage_counts = {}
        for o in active_orders:
            stage_counts[o.current_stage] = stage_counts.get(o.current_stage, 0) + 1
        bottleneck = max(stage_counts, key=stage_counts.get) if stage_counts else None
    else:
        bottleneck = None

    return PharmacyMetrics(
        timestamp=now,
        avg_mtat_minutes=round(avg_mtat, 1),
        avg_verification_wait_minutes=round(avg_verify, 1),
        avg_compounding_time_minutes=round(avg_compound, 1),
        orders_in_queue=queues,
        throughput_per_hour=throughput,
        bottleneck_stage=bottleneck,
    )
