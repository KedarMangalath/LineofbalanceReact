"""LOB metrics endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from hospital_lob.data.store import get_store
from hospital_lob.tools.lob_chart_generator import build_lob_chart_data
from hospital_lob.tools.metrics_calculator import compute_lob_metrics

router = APIRouter()


@router.get("/lob")
def get_lob_metrics(hours: int = Query(24, ge=1, le=168)):
    store = get_store()
    patients = store.get_patients(start_time=datetime.now() - timedelta(hours=hours))
    capacities = store.get_stage_capacities()
    metrics = compute_lob_metrics(patients, capacities, hours)
    return metrics.model_dump(mode="json")


@router.get("/chart-data")
def get_chart_data(hours: int = Query(24, ge=1, le=168)):
    store = get_store()
    patients = store.get_patients(start_time=datetime.now() - timedelta(hours=hours))
    capacities = store.get_stage_capacities()
    metrics = compute_lob_metrics(patients, capacities, hours)
    chart_data = build_lob_chart_data(metrics)
    return chart_data.model_dump(mode="json")
