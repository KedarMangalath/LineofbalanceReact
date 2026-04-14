"""LOB metrics data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from hospital_lob.config.settings import StageEnum


class StageMetrics(BaseModel):
    """Metrics for a single LOB stage."""

    stage: StageEnum
    actual_throughput_per_hour: float
    target_throughput_per_hour: float
    avg_service_time_minutes: float
    current_wip: int
    utilization_percent: float
    takt_time_minutes: float

    @property
    def deviation_from_target(self) -> float:
        if self.target_throughput_per_hour == 0:
            return 0.0
        return (
            self.actual_throughput_per_hour - self.target_throughput_per_hour
        ) / self.target_throughput_per_hour

    @property
    def is_bottleneck_candidate(self) -> bool:
        return self.deviation_from_target < -0.1


class LOBMetrics(BaseModel):
    """Complete Line of Balance metrics snapshot."""

    timestamp: datetime
    stage_metrics: dict[StageEnum, StageMetrics]
    alos_hours: float
    bed_turnover_rate: float
    ed_door_to_provider_minutes: float
    or_utilization_percent: float
    overall_throughput_per_hour: float
    bottleneck_stage: Optional[StageEnum] = None
    balance_score: float = 0.0  # 0=perfect, higher=worse

    @property
    def wip_by_stage(self) -> dict[StageEnum, int]:
        return {s: m.current_wip for s, m in self.stage_metrics.items()}


class LOBChartData(BaseModel):
    """Data structure for rendering LOB charts."""

    stages: list[str]
    target_throughput: list[float]
    actual_throughput: list[float]
    cumulative_target: list[float]
    cumulative_actual: list[float]
    timestamp: datetime
