"""Simulation endpoints."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from hospital_lob.tools.simulation_engine import run_simulation

router = APIRouter()


class SimulationRequest(BaseModel):
    duration_hours: int = Field(168, ge=24, le=720)
    arrival_rate: float = Field(8.0, ge=1.0, le=30.0)
    capacity_overrides: dict[str, int] = Field(default_factory=dict)
    service_time_multipliers: dict[str, float] = Field(default_factory=dict)


class SimulationCompareRequest(BaseModel):
    duration_hours: int = Field(168, ge=24, le=720)
    arrival_rate: float = Field(8.0, ge=1.0, le=30.0)
    capacity_overrides: dict[str, int] = Field(default_factory=dict)
    service_time_multipliers: dict[str, float] = Field(default_factory=dict)


@router.post("/simulation")
def run_sim(req: SimulationRequest):
    result = run_simulation(
        duration_hours=req.duration_hours,
        arrival_rate=req.arrival_rate,
        capacity_overrides=req.capacity_overrides or None,
        service_time_multipliers=req.service_time_multipliers or None,
    )
    return result


@router.post("/simulation/compare")
def compare_sim(req: SimulationCompareRequest):
    baseline = run_simulation(
        duration_hours=req.duration_hours,
        arrival_rate=req.arrival_rate,
    )
    scenario = run_simulation(
        duration_hours=req.duration_hours,
        arrival_rate=req.arrival_rate,
        capacity_overrides=req.capacity_overrides or None,
        service_time_multipliers=req.service_time_multipliers or None,
    )
    return {"baseline": baseline, "scenario": scenario}
