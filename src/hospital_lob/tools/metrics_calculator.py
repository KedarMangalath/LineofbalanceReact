"""LOB metrics calculation tool for CrewAI."""

from datetime import datetime, timedelta
from typing import Any, Optional

from hospital_lob.tools._compat import BaseTool
from pydantic import BaseModel, Field

from hospital_lob.config.settings import PATIENT_FLOW_STAGES, StageEnum
from hospital_lob.models.metrics import LOBMetrics, StageMetrics
from hospital_lob.models.patient import Patient, StageCapacity


class MetricsInput(BaseModel):
    time_window_hours: int = Field(default=24, description="Time window for metrics calculation")


class MetricsCalculatorTool(BaseTool):
    name: str = "metrics_calculator"
    description: str = (
        "Calculates all Line of Balance metrics for hospital patient flow: "
        "takt time, ALOS, bed turnover, ED door-to-provider time, OR utilization, "
        "and per-stage throughput. Returns a complete LOBMetrics snapshot."
    )
    args_schema: type[BaseModel] = MetricsInput

    def _run(self, time_window_hours: int = 24) -> str:
        from hospital_lob.data.store import get_store

        store = get_store()
        now = datetime.now()
        window_start = now - timedelta(hours=time_window_hours)

        patients = store.get_patients(start_time=window_start)
        capacities = store.get_stage_capacities()

        metrics = compute_lob_metrics(patients, capacities, time_window_hours)
        return metrics.model_dump_json(indent=2)


def compute_lob_metrics(
    patients: list[Patient],
    capacities: dict[StageEnum, StageCapacity],
    time_window_hours: int = 24,
) -> LOBMetrics:
    """Compute all LOB metrics from patient data."""
    now = datetime.now()
    stage_metrics = {}

    for stage in PATIENT_FLOW_STAGES:
        # Count patients who completed this stage in the window
        completed = 0
        service_times = []
        wip = 0

        for p in patients:
            if stage in p.stage_timestamps:
                ts = p.stage_timestamps[stage]
                if ts.exited_at:
                    completed += 1
                    dur = ts.duration_minutes
                    if dur and dur > 0:
                        service_times.append(dur)
                elif ts.entered_at and not ts.exited_at:
                    wip += 1

        actual_throughput = completed / max(time_window_hours, 1)
        cap = capacities.get(stage)
        target_throughput = cap.target_throughput_per_hour if cap else 10.0
        avg_service = sum(service_times) / len(service_times) if service_times else 0
        utilization = (cap.current_occupancy / cap.total_capacity * 100) if cap and cap.total_capacity > 0 else 0
        takt = (time_window_hours * 60) / max(completed, 1)

        stage_metrics[stage] = StageMetrics(
            stage=stage,
            actual_throughput_per_hour=round(actual_throughput, 2),
            target_throughput_per_hour=target_throughput,
            avg_service_time_minutes=round(avg_service, 1),
            current_wip=wip,
            utilization_percent=round(utilization, 1),
            takt_time_minutes=round(takt, 1),
        )

    # ALOS
    discharged = [p for p in patients if p.discharge_time and p.alos_hours]
    alos = sum(p.alos_hours for p in discharged) / len(discharged) if discharged else 0

    # Bed turnover
    total_beds = sum(c.total_capacity for c in capacities.values())
    bed_turnover = len(discharged) / max(total_beds, 1) if discharged else 0

    # ED door-to-provider (admission to triage exit)
    ed_times = []
    for p in patients:
        if StageEnum.TRIAGE in p.stage_timestamps:
            ts = p.stage_timestamps[StageEnum.TRIAGE]
            if ts.exited_at:
                wait = (ts.exited_at - p.admission_time).total_seconds() / 60
                ed_times.append(wait)
    ed_wait = sum(ed_times) / len(ed_times) if ed_times else 0

    # OR utilization
    surgical_patients = [p for p in patients if StageEnum.SURGICAL in p.stage_timestamps]
    or_cap = capacities.get(StageEnum.SURGICAL)
    if or_cap and surgical_patients:
        total_or_minutes = sum(
            p.stage_timestamps[StageEnum.SURGICAL].duration_minutes or 0
            for p in surgical_patients
        )
        available_or_minutes = or_cap.total_capacity * time_window_hours * 60
        or_util = (total_or_minutes / max(available_or_minutes, 1)) * 100
    else:
        or_util = 0

    # Overall throughput
    overall = len(discharged) / max(time_window_hours, 1)

    # Find bottleneck (stage with worst deviation from target)
    bottleneck = min(
        stage_metrics.values(),
        key=lambda m: m.deviation_from_target,
    )

    # Balance score (mean absolute deviation)
    deviations = [abs(m.deviation_from_target) for m in stage_metrics.values()]
    balance_score = sum(deviations) / len(deviations) if deviations else 0

    return LOBMetrics(
        timestamp=now,
        stage_metrics=stage_metrics,
        alos_hours=round(alos, 2),
        bed_turnover_rate=round(bed_turnover, 3),
        ed_door_to_provider_minutes=round(ed_wait, 1),
        or_utilization_percent=round(or_util, 1),
        overall_throughput_per_hour=round(overall, 2),
        bottleneck_stage=bottleneck.stage if bottleneck.deviation_from_target < -0.1 else None,
        balance_score=round(balance_score, 3),
    )
