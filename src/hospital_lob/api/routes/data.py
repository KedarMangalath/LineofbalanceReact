"""Data management endpoints."""

import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from hospital_lob.config.settings import STAGE_DISPLAY_NAMES
from hospital_lob.data.store import get_store

router = APIRouter()


@router.get("/summary")
def get_summary(hours: int = Query(24, ge=1, le=168)):
    store = get_store()
    start = datetime.now() - timedelta(hours=hours)
    patients = store.get_patients(start_time=start)
    caps = store.get_stage_capacities()
    active = [p for p in patients if p.is_active]
    discharged = [p for p in patients if p.discharge_time]

    by_stage = {}
    for p in patients:
        key = p.current_stage.value
        by_stage[key] = by_stage.get(key, 0) + 1

    by_priority = {}
    for p in patients:
        key = p.priority.value
        by_priority[key] = by_priority.get(key, 0) + 1

    return {
        "time_window_hours": hours,
        "total_patients": len(patients),
        "active_patients": len(active),
        "discharged_patients": len(discharged),
        "patients_by_stage": by_stage,
        "patients_by_priority": by_priority,
        "total_beds": sum(c.total_capacity for c in caps.values()),
        "occupied_beds": sum(c.current_occupancy for c in caps.values()),
        "stage_display_names": {k.value: v for k, v in STAGE_DISPLAY_NAMES.items()},
    }


@router.post("/refresh")
def refresh_data():
    store = get_store()
    store.refresh()
    return {"status": "ok"}
