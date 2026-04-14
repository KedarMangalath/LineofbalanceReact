"""Alerting Crew for threshold monitoring."""

import json
import uuid
from datetime import datetime

from crewai import Agent, Crew, Process, Task

from hospital_lob.config.settings import ALERT_THRESHOLDS, SeverityEnum, StageEnum
from hospital_lob.models.alert import Alert
from hospital_lob.tools.data_query_tool import DataQueryTool
from hospital_lob.tools.metrics_calculator import MetricsCalculatorTool


def check_alerts_direct() -> list[Alert]:
    """Check thresholds directly (without running a full crew) for dashboard use."""
    from hospital_lob.data.store import get_store
    from hospital_lob.tools.metrics_calculator import compute_lob_metrics

    store = get_store()
    patients = store.get_patients()
    capacities = store.get_stage_capacities()
    metrics = compute_lob_metrics(patients, capacities)

    alerts = []

    # ED wait time
    if metrics.ed_door_to_provider_minutes > ALERT_THRESHOLDS["ed_wait_minutes"]["critical"]:
        alerts.append(Alert(
            alert_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            severity=SeverityEnum.CRITICAL,
            metric_name="ED Door-to-Provider Time",
            current_value=metrics.ed_door_to_provider_minutes,
            threshold_value=ALERT_THRESHOLDS["ed_wait_minutes"]["critical"],
            stage=StageEnum.TRIAGE,
            message=f"ED wait time is {metrics.ed_door_to_provider_minutes:.0f} min (critical threshold: {ALERT_THRESHOLDS['ed_wait_minutes']['critical']} min)",
        ))
    elif metrics.ed_door_to_provider_minutes > ALERT_THRESHOLDS["ed_wait_minutes"]["warning"]:
        alerts.append(Alert(
            alert_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            severity=SeverityEnum.WARNING,
            metric_name="ED Door-to-Provider Time",
            current_value=metrics.ed_door_to_provider_minutes,
            threshold_value=ALERT_THRESHOLDS["ed_wait_minutes"]["warning"],
            stage=StageEnum.TRIAGE,
            message=f"ED wait time is {metrics.ed_door_to_provider_minutes:.0f} min (warning threshold: {ALERT_THRESHOLDS['ed_wait_minutes']['warning']} min)",
        ))

    # ALOS
    if metrics.alos_hours > ALERT_THRESHOLDS["alos_hours"]["critical"]:
        alerts.append(Alert(
            alert_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            severity=SeverityEnum.CRITICAL,
            metric_name="Average Length of Stay",
            current_value=metrics.alos_hours,
            threshold_value=ALERT_THRESHOLDS["alos_hours"]["critical"],
            message=f"ALOS is {metrics.alos_hours:.1f} hours (critical: {ALERT_THRESHOLDS['alos_hours']['critical']}h)",
        ))
    elif metrics.alos_hours > ALERT_THRESHOLDS["alos_hours"]["warning"]:
        alerts.append(Alert(
            alert_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            severity=SeverityEnum.WARNING,
            metric_name="Average Length of Stay",
            current_value=metrics.alos_hours,
            threshold_value=ALERT_THRESHOLDS["alos_hours"]["warning"],
            message=f"ALOS is {metrics.alos_hours:.1f} hours (warning: {ALERT_THRESHOLDS['alos_hours']['warning']}h)",
        ))

    # OR utilization
    if metrics.or_utilization_percent > ALERT_THRESHOLDS["or_utilization_percent"]["critical"]:
        alerts.append(Alert(
            alert_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            severity=SeverityEnum.CRITICAL,
            metric_name="OR Utilization",
            current_value=metrics.or_utilization_percent,
            threshold_value=ALERT_THRESHOLDS["or_utilization_percent"]["critical"],
            stage=StageEnum.SURGICAL,
            message=f"OR utilization at {metrics.or_utilization_percent:.1f}% (critical: {ALERT_THRESHOLDS['or_utilization_percent']['critical']}%)",
        ))

    # Per-stage utilization
    for stage, sm in metrics.stage_metrics.items():
        if sm.utilization_percent > ALERT_THRESHOLDS["stage_utilization_percent"]["critical"]:
            alerts.append(Alert(
                alert_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(),
                severity=SeverityEnum.CRITICAL,
                metric_name=f"Stage Utilization - {stage.value}",
                current_value=sm.utilization_percent,
                threshold_value=ALERT_THRESHOLDS["stage_utilization_percent"]["critical"],
                stage=stage,
                message=f"{stage.value} utilization at {sm.utilization_percent:.1f}% (critical: 95%)",
            ))
        elif sm.utilization_percent > ALERT_THRESHOLDS["stage_utilization_percent"]["warning"]:
            alerts.append(Alert(
                alert_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(),
                severity=SeverityEnum.WARNING,
                metric_name=f"Stage Utilization - {stage.value}",
                current_value=sm.utilization_percent,
                threshold_value=ALERT_THRESHOLDS["stage_utilization_percent"]["warning"],
                stage=stage,
                message=f"{stage.value} utilization at {sm.utilization_percent:.1f}% (warning: 85%)",
            ))

    return alerts


def create_alerting_crew() -> Crew:
    """Create the alerting crew for threshold monitoring."""

    metrics_calc = MetricsCalculatorTool()
    data_query = DataQueryTool()

    monitor = Agent(
        role="Real-Time Hospital Operations Monitor",
        goal="Watch key metrics against thresholds and raise alerts",
        backstory=(
            "Hospital operations center analyst who monitors KPIs in real-time. "
            "Early warning enables proactive intervention before patient care is affected."
        ),
        tools=[metrics_calc, data_query],
        verbose=True,
    )

    check = Task(
        description=(
            "Check all hospital LOB metrics against configured thresholds. "
            "Compute current metrics, then compare against these thresholds: "
            "ED wait > 30min (warning) / 60min (critical), "
            "ALOS > 72h (warning) / 120h (critical), "
            "Bed occupancy > 85% (warning) / 95% (critical), "
            "OR utilization > 90% (warning) / 98% (critical). "
            "Generate alerts for any breaches."
        ),
        expected_output=(
            "List of active alerts with metric name, current value, threshold, "
            "severity, affected stage, and recommended action."
        ),
        agent=monitor,
    )

    return Crew(
        agents=[monitor],
        tasks=[check],
        process=Process.sequential,
        verbose=True,
    )
