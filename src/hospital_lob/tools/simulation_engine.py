"""SimPy-based discrete-event simulation for patient flow."""

import json
import random
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import simpy
from hospital_lob.tools._compat import BaseTool
from pydantic import BaseModel, Field

from hospital_lob.config.settings import (
    PATIENT_FLOW_STAGES,
    STAGE_DISPLAY_NAMES,
    STAGE_SERVICE_TIMES,
    SURGICAL_PROBABILITY,
    StageEnum,
)


class SimulationInput(BaseModel):
    duration_hours: int = Field(default=168, description="Simulation duration in hours (default: 1 week)")
    arrival_rate: float = Field(default=8.0, description="Average patient arrivals per hour")
    capacity_overrides: str = Field(
        default="{}",
        description='JSON dict of stage capacity overrides, e.g. {"diagnostics": 20, "discharge": 10}',
    )
    service_time_multipliers: str = Field(
        default="{}",
        description='JSON dict of service time multipliers, e.g. {"diagnostics": 0.7} to reduce by 30%',
    )


@dataclass
class SimStats:
    """Simulation statistics collector."""

    completed: int = 0
    total_wait_time: float = 0
    stage_throughput: dict = field(default_factory=dict)
    stage_wait_times: dict = field(default_factory=dict)
    stage_utilization: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "patients_completed": self.completed,
            "avg_total_time_hours": round(self.total_wait_time / max(self.completed, 1) / 60, 2),
            "stage_throughput_per_hour": {
                k: round(v, 2) for k, v in self.stage_throughput.items()
            },
            "stage_avg_wait_minutes": {
                k: round(sum(v) / len(v), 1) if v else 0
                for k, v in self.stage_wait_times.items()
            },
        }


class SimulationEngineTool(BaseTool):
    name: str = "simulation_engine"
    description: str = (
        "Runs a discrete-event simulation of hospital patient flow using SimPy. "
        "Accepts capacity overrides and service time multipliers for what-if analysis. "
        "Returns projected throughput, wait times, and bottleneck predictions."
    )
    args_schema: type[BaseModel] = SimulationInput

    def _run(
        self,
        duration_hours: int = 168,
        arrival_rate: float = 8.0,
        capacity_overrides: str = "{}",
        service_time_multipliers: str = "{}",
    ) -> str:
        cap_overrides = json.loads(capacity_overrides)
        st_multipliers = json.loads(service_time_multipliers)

        results = run_simulation(
            duration_hours=duration_hours,
            arrival_rate=arrival_rate,
            capacity_overrides=cap_overrides,
            service_time_multipliers=st_multipliers,
        )
        return json.dumps(results, indent=2)


def run_simulation(
    duration_hours: int = 168,
    arrival_rate: float = 8.0,
    capacity_overrides: dict[str, int] | None = None,
    service_time_multipliers: dict[str, float] | None = None,
) -> dict:
    """Run a discrete-event simulation of the hospital patient flow."""
    from hospital_lob.config.settings import DEFAULT_STAGE_CAPACITY

    cap_overrides = capacity_overrides or {}
    st_mults = service_time_multipliers or {}

    env = simpy.Environment()
    stats = SimStats()

    # Create resources for each stage
    resources = {}
    for stage in PATIENT_FLOW_STAGES:
        cap = cap_overrides.get(stage.value, DEFAULT_STAGE_CAPACITY[stage]["capacity"])
        resources[stage] = simpy.Resource(env, capacity=cap)
        stats.stage_throughput[stage.value] = 0
        stats.stage_wait_times[stage.value] = []

    def patient_process(env, patient_id):
        arrival_time = env.now
        requires_surgery = random.random() < SURGICAL_PROBABILITY

        for stage in PATIENT_FLOW_STAGES:
            if stage == StageEnum.SURGICAL and not requires_surgery:
                continue
            if stage == StageEnum.RECOVERY_PACU and not requires_surgery:
                continue

            # Get service time
            params = STAGE_SERVICE_TIMES[stage]
            mean = params["mean"]
            std = params["std"]

            # Apply multiplier
            mult = st_mults.get(stage.value, 1.0)
            mean *= mult

            mu = np.log(mean**2 / np.sqrt(std**2 + mean**2))
            sigma = np.sqrt(np.log(1 + (std**2 / mean**2)))
            service_time = max(1.0, float(np.random.lognormal(mu, sigma)))

            # Wait for resource
            with resources[stage].request() as req:
                wait_start = env.now
                yield req
                wait_time = env.now - wait_start
                stats.stage_wait_times[stage.value].append(wait_time)

                # Service
                yield env.timeout(service_time)
                stats.stage_throughput[stage.value] += 1

        total_time = env.now - arrival_time
        stats.total_wait_time += total_time
        stats.completed += 1

    def patient_generator(env):
        patient_id = 0
        while True:
            inter_arrival = np.random.exponential(60 / arrival_rate)
            yield env.timeout(inter_arrival)
            patient_id += 1
            env.process(patient_process(env, patient_id))

    env.process(patient_generator(env))
    env.run(until=duration_hours * 60)  # Convert to minutes

    # Calculate per-hour throughput
    for stage_name in stats.stage_throughput:
        stats.stage_throughput[stage_name] /= duration_hours

    result = stats.to_dict()
    result["simulation_params"] = {
        "duration_hours": duration_hours,
        "arrival_rate": arrival_rate,
        "capacity_overrides": cap_overrides,
        "service_time_multipliers": st_mults,
    }

    # Identify simulated bottleneck
    min_stage = min(
        stats.stage_throughput.items(),
        key=lambda x: x[1],
    )
    result["predicted_bottleneck"] = {
        "stage": min_stage[0],
        "throughput_per_hour": round(min_stage[1], 2),
    }

    return result
