"""Pharmacy metrics endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from hospital_lob.data.store import get_store
from hospital_lob.tools.pharmacy_metrics import compute_pharmacy_metrics

router = APIRouter()


@router.get("/metrics")
def get_pharmacy_metrics(hours: int = Query(24, ge=1, le=168)):
    store = get_store()
    orders = store.get_pharmacy_orders(start_time=datetime.now() - timedelta(hours=hours))
    metrics = compute_pharmacy_metrics(orders, hours)
    return metrics.model_dump(mode="json")
