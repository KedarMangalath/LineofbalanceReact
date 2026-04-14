"""Bottleneck analysis endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from hospital_lob.data.store import get_store
from hospital_lob.tools.bottleneck_analyzer import analyze_bottlenecks
from hospital_lob.tools.metrics_calculator import compute_lob_metrics

router = APIRouter()


@router.get("/bottlenecks")
def get_bottlenecks(hours: int = Query(24, ge=1, le=168)):
    store = get_store()
    patients = store.get_patients(start_time=datetime.now() - timedelta(hours=hours))
    capacities = store.get_stage_capacities()
    metrics = compute_lob_metrics(patients, capacities, hours)
    return analyze_bottlenecks(metrics)
