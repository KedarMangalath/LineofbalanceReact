"""Chat endpoint."""

from datetime import datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel

from hospital_lob.config.settings import STAGE_DISPLAY_NAMES
from hospital_lob.data.store import get_store
from hospital_lob.tools.bottleneck_analyzer import analyze_bottlenecks
from hospital_lob.tools.metrics_calculator import compute_lob_metrics

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(req: ChatRequest):
    response = _handle_query(req.message)
    return {"response": response}


def _handle_query(query: str) -> str:
    query_lower = query.lower()
    store = get_store()
    patients = store.get_patients(start_time=datetime.now() - timedelta(hours=24))
    capacities = store.get_stage_capacities()
    metrics = compute_lob_metrics(patients, capacities)

    if "bottleneck" in query_lower or "constraint" in query_lower:
        analysis = analyze_bottlenecks(metrics)
        return analysis["analysis"]

    elif "alos" in query_lower or "length of stay" in query_lower:
        return f"**Average Length of Stay:** {metrics.alos_hours:.1f} hours\n\nCalculated across all discharged patients in the last 24 hours."

    elif "wip" in query_lower or "queue" in query_lower or "work in progress" in query_lower:
        wip = metrics.wip_by_stage
        lines = ["**Work In Progress by Stage:**\n"]
        for stage, count in wip.items():
            name = STAGE_DISPLAY_NAMES.get(stage, stage.value)
            lines.append(f"- {name}: **{count}** patients")
        max_stage = max(wip, key=wip.get)
        lines.append(f"\n**Highest WIP:** {STAGE_DISPLAY_NAMES.get(max_stage, max_stage.value)} with {wip[max_stage]} patients")
        return "\n".join(lines)

    elif "metric" in query_lower or "summary" in query_lower or "overview" in query_lower:
        bn = STAGE_DISPLAY_NAMES.get(metrics.bottleneck_stage, "None") if metrics.bottleneck_stage else "None detected"
        return (
            f"**LOB Metrics Summary (24h window)**\n\n"
            f"- **ALOS:** {metrics.alos_hours:.1f} hours\n"
            f"- **Bed Turnover:** {metrics.bed_turnover_rate:.3f}\n"
            f"- **ED Wait:** {metrics.ed_door_to_provider_minutes:.0f} minutes\n"
            f"- **OR Utilization:** {metrics.or_utilization_percent:.1f}%\n"
            f"- **Overall Throughput:** {metrics.overall_throughput_per_hour:.1f} pts/hr\n"
            f"- **Balance Score:** {metrics.balance_score:.3f}\n"
            f"- **Bottleneck:** {bn}"
        )

    elif "recommend" in query_lower or "action" in query_lower or "fix" in query_lower:
        analysis = analyze_bottlenecks(metrics)
        primary = analysis.get("primary_bottleneck")
        if primary:
            return (
                f"**Recommended Corrective Actions:**\n\n"
                f"The primary constraint is **{primary['display_name']}** "
                f"(throughput: {primary['actual_throughput']:.1f} vs target {primary['target_throughput']:.1f} pts/hr).\n\n"
                f"1. **Add capacity** to {primary['display_name']}\n"
                f"2. **Reduce service time** - streamline protocols\n"
                f"3. **Smooth upstream demand** - stagger admissions\n"
                f"4. **Review discharge processes** if discharge is the bottleneck\n"
                f"5. **Rebalance staff** from over-capacity stages to the constraint"
            )
        return "No significant bottleneck detected. The system appears reasonably balanced."

    else:
        return (
            "I can answer questions about:\n"
            "- **Bottlenecks** - current constraints in patient flow\n"
            "- **ALOS** - average length of stay\n"
            "- **WIP** - work in progress / queue sizes\n"
            "- **Metrics** - overall LOB metrics summary\n"
            "- **Recommendations** - corrective actions\n\n"
            "Try asking: *What is the current bottleneck?*"
        )
