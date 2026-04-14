"""Data query tool for CrewAI agents."""

import json
from datetime import datetime, timedelta
from typing import Optional

from hospital_lob.tools._compat import BaseTool
from pydantic import BaseModel, Field

from hospital_lob.config.settings import StageEnum


class QueryInput(BaseModel):
    query_type: str = Field(
        description="Type of query: 'patients', 'capacities', 'pharmacy', 'summary'"
    )
    time_window_hours: int = Field(default=24, description="Time window for query")
    stage_filter: Optional[str] = Field(default=None, description="Filter by stage name")
    active_only: bool = Field(default=False, description="Only return active patients")


class DataQueryTool(BaseTool):
    name: str = "data_query"
    description: str = (
        "Queries the hospital data store for patient flow data, stage capacities, "
        "and pharmacy orders. Supports filtering by time window, stage, and status."
    )
    args_schema: type[BaseModel] = QueryInput

    def _run(
        self,
        query_type: str = "summary",
        time_window_hours: int = 24,
        stage_filter: Optional[str] = None,
        active_only: bool = False,
    ) -> str:
        from hospital_lob.data.store import get_store

        store = get_store()
        now = datetime.now()
        start = now - timedelta(hours=time_window_hours)

        stage = None
        if stage_filter:
            try:
                stage = StageEnum(stage_filter)
            except ValueError:
                pass

        if query_type == "patients":
            patients = store.get_patients(
                start_time=start, stage=stage, active_only=active_only
            )
            return json.dumps({
                "total_patients": len(patients),
                "active_patients": sum(1 for p in patients if p.is_active),
                "discharged": sum(1 for p in patients if p.discharge_time),
                "by_stage": _count_by_stage(patients),
                "by_priority": _count_by_priority(patients),
            }, indent=2)

        elif query_type == "capacities":
            caps = store.get_stage_capacities()
            return json.dumps({
                stage.value: {
                    "capacity": cap.total_capacity,
                    "occupancy": cap.current_occupancy,
                    "utilization": f"{cap.utilization_percent:.1f}%",
                    "staff": cap.staff_count,
                }
                for stage, cap in caps.items()
            }, indent=2)

        elif query_type == "pharmacy":
            orders = store.get_pharmacy_orders(start_time=start)
            completed = [o for o in orders if o.is_complete]
            mtat_values = [o.mtat_minutes for o in completed if o.mtat_minutes]
            avg_mtat = sum(mtat_values) / len(mtat_values) if mtat_values else 0
            return json.dumps({
                "total_orders": len(orders),
                "completed": len(completed),
                "in_progress": len(orders) - len(completed),
                "avg_mtat_minutes": round(avg_mtat, 1),
            }, indent=2)

        else:  # summary
            patients = store.get_patients(start_time=start)
            caps = store.get_stage_capacities()
            active = [p for p in patients if p.is_active]
            discharged = [p for p in patients if p.discharge_time]
            return json.dumps({
                "time_window_hours": time_window_hours,
                "total_patients": len(patients),
                "active_patients": len(active),
                "discharged_patients": len(discharged),
                "patients_by_stage": _count_by_stage(patients),
                "overall_bed_occupancy": f"{sum(c.current_occupancy for c in caps.values())}/{sum(c.total_capacity for c in caps.values())}",
            }, indent=2)


def _count_by_stage(patients) -> dict:
    counts = {}
    for p in patients:
        key = p.current_stage.value
        counts[key] = counts.get(key, 0) + 1
    return counts


def _count_by_priority(patients) -> dict:
    counts = {}
    for p in patients:
        key = p.priority.value
        counts[key] = counts.get(key, 0) + 1
    return counts
