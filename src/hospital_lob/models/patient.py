"""Patient and stage data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from hospital_lob.config.settings import PriorityEnum, StageEnum


class StageTimestamp(BaseModel):
    """Timestamp record for a patient at a specific stage."""

    stage: StageEnum
    entered_at: datetime
    exited_at: Optional[datetime] = None
    assigned_resource: Optional[str] = None

    @property
    def duration_minutes(self) -> Optional[float]:
        if self.exited_at and self.entered_at:
            return (self.exited_at - self.entered_at).total_seconds() / 60
        return None


class Patient(BaseModel):
    """A patient flowing through the hospital LOB pipeline."""

    patient_id: str
    admission_time: datetime
    current_stage: StageEnum
    stage_timestamps: dict[StageEnum, StageTimestamp] = Field(default_factory=dict)
    priority: PriorityEnum = PriorityEnum.STANDARD
    department: str = "General"
    diagnosis_category: str = "General"
    discharge_time: Optional[datetime] = None
    is_active: bool = True
    requires_surgery: bool = False

    @property
    def alos_hours(self) -> Optional[float]:
        if self.discharge_time and self.admission_time:
            return (self.discharge_time - self.admission_time).total_seconds() / 3600
        return None

    @property
    def total_stages_completed(self) -> int:
        return sum(
            1 for ts in self.stage_timestamps.values() if ts.exited_at is not None
        )


class StageCapacity(BaseModel):
    """Capacity and utilization info for a single stage."""

    stage: StageEnum
    total_capacity: int
    current_occupancy: int = 0
    staff_count: int = 0
    target_throughput_per_hour: float = 0.0
    actual_throughput_per_hour: float = 0.0

    @property
    def utilization_percent(self) -> float:
        if self.total_capacity == 0:
            return 0.0
        return (self.current_occupancy / self.total_capacity) * 100

    @property
    def throughput_deviation(self) -> float:
        if self.target_throughput_per_hour == 0:
            return 0.0
        return (
            self.actual_throughput_per_hour - self.target_throughput_per_hour
        ) / self.target_throughput_per_hour
