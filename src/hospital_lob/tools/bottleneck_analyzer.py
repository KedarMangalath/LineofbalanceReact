"""Bottleneck detection tool using Theory of Constraints approach."""

import json
from datetime import datetime, timedelta

from hospital_lob.tools._compat import BaseTool
from pydantic import BaseModel, Field

from hospital_lob.config.settings import PATIENT_FLOW_STAGES, STAGE_DISPLAY_NAMES, StageEnum
from hospital_lob.models.metrics import LOBMetrics, StageMetrics


class BottleneckInput(BaseModel):
    time_window_hours: int = Field(default=24, description="Time window for analysis")


class BottleneckAnalyzerTool(BaseTool):
    name: str = "bottleneck_analyzer"
    description: str = (
        "Identifies the binding constraint in the hospital patient flow pipeline "
        "using Theory of Constraints (TOC). Analyzes throughput deviation, WIP "
        "accumulation, and utilization to find the bottleneck stage."
    )
    args_schema: type[BaseModel] = BottleneckInput

    def _run(self, time_window_hours: int = 24) -> str:
        from hospital_lob.data.store import get_store
        from hospital_lob.tools.metrics_calculator import compute_lob_metrics

        store = get_store()
        now = datetime.now()
        patients = store.get_patients(start_time=now - timedelta(hours=time_window_hours))
        capacities = store.get_stage_capacities()
        metrics = compute_lob_metrics(patients, capacities, time_window_hours)

        analysis = analyze_bottlenecks(metrics)
        return json.dumps(analysis, indent=2, default=str)


def analyze_bottlenecks(metrics: LOBMetrics) -> dict:
    """Perform bottleneck analysis on LOB metrics.

    Uses three signals:
    1. Throughput deviation: stage with largest negative gap from target
    2. WIP accumulation: high WIP indicates downstream constraint
    3. Utilization: stages near 100% are at capacity
    """
    stage_scores = {}

    for stage in PATIENT_FLOW_STAGES:
        sm = metrics.stage_metrics.get(stage)
        if not sm:
            continue

        # Throughput deviation score (0 to 1, higher = worse)
        deviation = abs(min(0, sm.deviation_from_target))

        # WIP score (normalized)
        wip_score = min(1.0, sm.current_wip / 20.0)

        # Utilization score (above 85% is concerning)
        util_score = max(0, (sm.utilization_percent - 70) / 30)

        # Combined constraint score (weighted)
        constraint_score = (deviation * 0.5) + (wip_score * 0.25) + (util_score * 0.25)

        stage_scores[stage] = {
            "stage": stage.value,
            "display_name": STAGE_DISPLAY_NAMES.get(stage, stage.value),
            "throughput_deviation": round(sm.deviation_from_target, 3),
            "wip_count": sm.current_wip,
            "utilization_percent": sm.utilization_percent,
            "constraint_score": round(constraint_score, 3),
            "actual_throughput": sm.actual_throughput_per_hour,
            "target_throughput": sm.target_throughput_per_hour,
            "avg_service_time_min": sm.avg_service_time_minutes,
        }

    # Rank by constraint score
    ranked = sorted(stage_scores.values(), key=lambda x: x["constraint_score"], reverse=True)

    # Primary bottleneck
    primary = ranked[0] if ranked else None
    secondary = ranked[1] if len(ranked) > 1 else None

    # Generate analysis text
    analysis_text = _generate_analysis_text(primary, secondary, metrics)

    return {
        "primary_bottleneck": primary,
        "secondary_bottleneck": secondary,
        "all_stages_ranked": ranked,
        "balance_score": metrics.balance_score,
        "overall_throughput": metrics.overall_throughput_per_hour,
        "analysis": analysis_text,
    }


def _generate_analysis_text(
    primary: dict | None,
    secondary: dict | None,
    metrics: LOBMetrics,
) -> str:
    """Generate human-readable bottleneck analysis."""
    if not primary:
        return "No bottleneck data available."

    lines = []
    lines.append(f"## Bottleneck Analysis Report")
    lines.append(f"**Generated:** {metrics.timestamp.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Balance Score:** {metrics.balance_score:.3f} (0 = perfect balance)")
    lines.append("")

    lines.append(f"### Primary Constraint: {primary['display_name']}")
    lines.append(f"- **Constraint Score:** {primary['constraint_score']:.3f}")
    lines.append(f"- **Throughput:** {primary['actual_throughput']:.1f} vs target {primary['target_throughput']:.1f} pts/hr")
    lines.append(f"- **Deviation:** {primary['throughput_deviation']:.1%}")
    lines.append(f"- **WIP:** {primary['wip_count']} patients queued")
    lines.append(f"- **Utilization:** {primary['utilization_percent']:.1f}%")
    lines.append(f"- **Avg Service Time:** {primary['avg_service_time_min']:.0f} minutes")
    lines.append("")

    if secondary:
        lines.append(f"### Secondary Constraint: {secondary['display_name']}")
        lines.append(f"- **Constraint Score:** {secondary['constraint_score']:.3f}")
        lines.append(f"- **Throughput:** {secondary['actual_throughput']:.1f} vs target {secondary['target_throughput']:.1f} pts/hr")
        lines.append("")

    lines.append("### Impact")
    lines.append(f"The primary bottleneck at **{primary['display_name']}** is capping system throughput at "
                 f"**{metrics.overall_throughput_per_hour:.1f} pts/hr**. All upstream capacity beyond this "
                 f"rate is effectively waste until this constraint is resolved.")

    return "\n".join(lines)
