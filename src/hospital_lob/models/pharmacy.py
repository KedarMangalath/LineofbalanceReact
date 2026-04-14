"""Pharmacy LOB data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from hospital_lob.config.settings import PharmacyOrderType, PharmacyStageEnum


class PharmacyOrder(BaseModel):
    """A medication order flowing through the pharmacy pipeline."""

    order_id: str
    patient_id: str
    medication: str
    order_type: PharmacyOrderType = PharmacyOrderType.STANDARD
    order_time: datetime
    verification_time: Optional[datetime] = None
    compounding_start: Optional[datetime] = None
    compounding_end: Optional[datetime] = None
    dispensed_time: Optional[datetime] = None
    administered_time: Optional[datetime] = None
    current_stage: PharmacyStageEnum = PharmacyStageEnum.ORDER_RECEIPT
    is_complete: bool = False

    @property
    def mtat_minutes(self) -> Optional[float]:
        """Medication turnaround time."""
        if self.administered_time and self.order_time:
            return (self.administered_time - self.order_time).total_seconds() / 60
        return None

    @property
    def verification_wait_minutes(self) -> Optional[float]:
        if self.verification_time and self.order_time:
            return (self.verification_time - self.order_time).total_seconds() / 60
        return None


class PharmacyMetrics(BaseModel):
    """Pharmacy LOB metrics."""

    timestamp: datetime
    avg_mtat_minutes: float
    avg_verification_wait_minutes: float
    avg_compounding_time_minutes: float
    orders_in_queue: dict[PharmacyStageEnum, int]
    throughput_per_hour: dict[PharmacyStageEnum, float]
    bottleneck_stage: Optional[PharmacyStageEnum] = None
