"""Alert data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from hospital_lob.config.settings import SeverityEnum, StageEnum


class Alert(BaseModel):
    """An alert triggered by threshold breach."""

    alert_id: str
    timestamp: datetime
    severity: SeverityEnum
    metric_name: str
    current_value: float
    threshold_value: float
    stage: Optional[StageEnum] = None
    message: str
    acknowledged: bool = False


class AlertThreshold(BaseModel):
    """Configurable alert threshold."""

    metric_name: str
    warning_threshold: float
    critical_threshold: float
    stage: Optional[StageEnum] = None
    enabled: bool = True
