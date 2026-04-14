"""Synthetic patient flow data generator for hospital LOB."""

import random
import uuid
from datetime import datetime, timedelta

import numpy as np
from faker import Faker

from hospital_lob.config.settings import (
    DEFAULT_STAGE_CAPACITY,
    PATIENT_FLOW_STAGES,
    STAGE_SERVICE_TIMES,
    SURGICAL_PROBABILITY,
    PriorityEnum,
    StageEnum,
)
from hospital_lob.models.patient import Patient, StageCapacity, StageTimestamp

fake = Faker()


def _lognormal_minutes(mean: float, std: float) -> float:
    """Generate a service time from a log-normal distribution."""
    mu = np.log(mean**2 / np.sqrt(std**2 + mean**2))
    sigma = np.sqrt(np.log(1 + (std**2 / mean**2)))
    return max(5.0, float(np.random.lognormal(mu, sigma)))


def _arrival_rate(hour: int) -> float:
    """Patients per hour based on time of day (realistic ED pattern)."""
    # Peaks at 10am, 3pm, 9pm
    rates = {
        0: 3, 1: 2, 2: 2, 3: 1, 4: 1, 5: 2,
        6: 4, 7: 6, 8: 8, 9: 10, 10: 12, 11: 11,
        12: 9, 13: 8, 14: 10, 15: 11, 16: 10, 17: 9,
        18: 8, 19: 7, 20: 9, 21: 10, 22: 7, 23: 5,
    }
    return rates.get(hour, 5)


def generate_patients(
    num_days: int = 3,
    start_date: datetime | None = None,
    bottleneck_factor: float = 1.5,
) -> list[Patient]:
    """Generate synthetic patient flow data.

    Args:
        num_days: Number of days to simulate.
        start_date: Start date for generation. Defaults to 3 days ago.
        bottleneck_factor: Multiplier on diagnostics/discharge times to create bottlenecks.
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=num_days)

    patients = []
    departments = ["Emergency", "General Medicine", "Cardiology", "Orthopedics", "Neurology"]
    diagnoses = ["Chest Pain", "Fracture", "Infection", "Stroke", "Abdominal Pain",
                 "Respiratory", "Cardiac", "Trauma", "Neurological", "Other"]

    for day in range(num_days):
        day_start = start_date + timedelta(days=day)

        for hour in range(24):
            current_time = day_start + timedelta(hours=hour)
            n_arrivals = np.random.poisson(_arrival_rate(hour))

            for _ in range(n_arrivals):
                arrival_offset = random.uniform(0, 60)
                admission_time = current_time + timedelta(minutes=arrival_offset)

                patient_id = str(uuid.uuid4())[:8]
                priority = random.choices(
                    [PriorityEnum.EMERGENCY, PriorityEnum.URGENT, PriorityEnum.STANDARD],
                    weights=[0.15, 0.30, 0.55],
                )[0]
                requires_surgery = random.random() < SURGICAL_PROBABILITY

                # Generate stage timestamps sequentially
                stage_timestamps = {}
                current_ts = admission_time
                completed = True

                for stage in PATIENT_FLOW_STAGES:
                    # Skip surgical if patient doesn't need it
                    if stage == StageEnum.SURGICAL and not requires_surgery:
                        continue
                    if stage == StageEnum.RECOVERY_PACU and not requires_surgery:
                        continue

                    service_params = STAGE_SERVICE_TIMES[stage]
                    mean = service_params["mean"]
                    std = service_params["std"]

                    # Apply bottleneck factor to diagnostics and discharge
                    if stage in (StageEnum.DIAGNOSTICS, StageEnum.DISCHARGE):
                        mean *= bottleneck_factor

                    # Emergency patients get faster service
                    if priority == PriorityEnum.EMERGENCY:
                        mean *= 0.7

                    duration = _lognormal_minutes(mean, std)
                    entered = current_ts
                    exited = entered + timedelta(minutes=duration)

                    # Some recent patients are still in process
                    time_since = (datetime.now() - entered).total_seconds() / 3600
                    if time_since < 4 and random.random() < 0.3:
                        # Patient still in this stage
                        stage_timestamps[stage] = StageTimestamp(
                            stage=stage,
                            entered_at=entered,
                            exited_at=None,
                            assigned_resource=f"Resource-{random.randint(1, 20)}",
                        )
                        completed = False
                        break

                    stage_timestamps[stage] = StageTimestamp(
                        stage=stage,
                        entered_at=entered,
                        exited_at=exited,
                        assigned_resource=f"Resource-{random.randint(1, 20)}",
                    )
                    current_ts = exited

                # Determine current stage
                current_stage = StageEnum.ADMISSION
                for stage in reversed(PATIENT_FLOW_STAGES):
                    if stage in stage_timestamps:
                        if stage_timestamps[stage].exited_at is None:
                            current_stage = stage
                            break
                        current_stage = stage
                        break

                discharge_time = None
                if completed and StageEnum.DISCHARGE in stage_timestamps:
                    ts = stage_timestamps[StageEnum.DISCHARGE]
                    if ts.exited_at:
                        discharge_time = ts.exited_at

                patient = Patient(
                    patient_id=patient_id,
                    admission_time=admission_time,
                    current_stage=current_stage,
                    stage_timestamps=stage_timestamps,
                    priority=priority,
                    department=random.choice(departments),
                    diagnosis_category=random.choice(diagnoses),
                    discharge_time=discharge_time,
                    is_active=not completed,
                    requires_surgery=requires_surgery,
                )
                patients.append(patient)

    return patients


def generate_stage_capacities(
    target_throughput: float = 10.0,
) -> dict[StageEnum, StageCapacity]:
    """Generate stage capacity data."""
    capacities = {}
    for stage, config in DEFAULT_STAGE_CAPACITY.items():
        capacities[stage] = StageCapacity(
            stage=stage,
            total_capacity=config["capacity"],
            staff_count=config["staff"],
            target_throughput_per_hour=target_throughput,
        )
    return capacities
