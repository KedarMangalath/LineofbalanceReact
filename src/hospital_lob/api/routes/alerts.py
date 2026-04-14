"""Alert endpoints."""

from fastapi import APIRouter

from hospital_lob.config.settings import ALERT_THRESHOLDS

try:
    from hospital_lob.crews.alerting_crew import check_alerts_direct
except (ImportError, ModuleNotFoundError):
    # Fallback when crewai is not installed — inline the logic
    import uuid
    from datetime import datetime
    from hospital_lob.config.settings import SeverityEnum, StageEnum
    from hospital_lob.models.alert import Alert

    def check_alerts_direct() -> list:
        from hospital_lob.data.store import get_store
        from hospital_lob.tools.metrics_calculator import compute_lob_metrics

        store = get_store()
        patients = store.get_patients()
        capacities = store.get_stage_capacities()
        metrics = compute_lob_metrics(patients, capacities)
        alerts = []

        if metrics.ed_door_to_provider_minutes > ALERT_THRESHOLDS["ed_wait_minutes"]["critical"]:
            alerts.append(Alert(alert_id=str(uuid.uuid4())[:8], timestamp=datetime.now(), severity=SeverityEnum.CRITICAL, metric_name="ED Door-to-Provider Time", current_value=metrics.ed_door_to_provider_minutes, threshold_value=ALERT_THRESHOLDS["ed_wait_minutes"]["critical"], stage=StageEnum.TRIAGE, message=f"ED wait time is {metrics.ed_door_to_provider_minutes:.0f} min (critical threshold: {ALERT_THRESHOLDS['ed_wait_minutes']['critical']} min)"))
        elif metrics.ed_door_to_provider_minutes > ALERT_THRESHOLDS["ed_wait_minutes"]["warning"]:
            alerts.append(Alert(alert_id=str(uuid.uuid4())[:8], timestamp=datetime.now(), severity=SeverityEnum.WARNING, metric_name="ED Door-to-Provider Time", current_value=metrics.ed_door_to_provider_minutes, threshold_value=ALERT_THRESHOLDS["ed_wait_minutes"]["warning"], stage=StageEnum.TRIAGE, message=f"ED wait time is {metrics.ed_door_to_provider_minutes:.0f} min (warning threshold: {ALERT_THRESHOLDS['ed_wait_minutes']['warning']} min)"))

        if metrics.alos_hours > ALERT_THRESHOLDS["alos_hours"]["critical"]:
            alerts.append(Alert(alert_id=str(uuid.uuid4())[:8], timestamp=datetime.now(), severity=SeverityEnum.CRITICAL, metric_name="Average Length of Stay", current_value=metrics.alos_hours, threshold_value=ALERT_THRESHOLDS["alos_hours"]["critical"], message=f"ALOS is {metrics.alos_hours:.1f} hours (critical: {ALERT_THRESHOLDS['alos_hours']['critical']}h)"))
        elif metrics.alos_hours > ALERT_THRESHOLDS["alos_hours"]["warning"]:
            alerts.append(Alert(alert_id=str(uuid.uuid4())[:8], timestamp=datetime.now(), severity=SeverityEnum.WARNING, metric_name="Average Length of Stay", current_value=metrics.alos_hours, threshold_value=ALERT_THRESHOLDS["alos_hours"]["warning"], message=f"ALOS is {metrics.alos_hours:.1f} hours (warning: {ALERT_THRESHOLDS['alos_hours']['warning']}h)"))

        if metrics.or_utilization_percent > ALERT_THRESHOLDS["or_utilization_percent"]["critical"]:
            alerts.append(Alert(alert_id=str(uuid.uuid4())[:8], timestamp=datetime.now(), severity=SeverityEnum.CRITICAL, metric_name="OR Utilization", current_value=metrics.or_utilization_percent, threshold_value=ALERT_THRESHOLDS["or_utilization_percent"]["critical"], stage=StageEnum.SURGICAL, message=f"OR utilization at {metrics.or_utilization_percent:.1f}% (critical: {ALERT_THRESHOLDS['or_utilization_percent']['critical']}%)"))

        for stage, sm in metrics.stage_metrics.items():
            if sm.utilization_percent > ALERT_THRESHOLDS["stage_utilization_percent"]["critical"]:
                alerts.append(Alert(alert_id=str(uuid.uuid4())[:8], timestamp=datetime.now(), severity=SeverityEnum.CRITICAL, metric_name=f"Stage Utilization - {stage.value}", current_value=sm.utilization_percent, threshold_value=ALERT_THRESHOLDS["stage_utilization_percent"]["critical"], stage=stage, message=f"{stage.value} utilization at {sm.utilization_percent:.1f}% (critical: 95%)"))
            elif sm.utilization_percent > ALERT_THRESHOLDS["stage_utilization_percent"]["warning"]:
                alerts.append(Alert(alert_id=str(uuid.uuid4())[:8], timestamp=datetime.now(), severity=SeverityEnum.WARNING, metric_name=f"Stage Utilization - {stage.value}", current_value=sm.utilization_percent, threshold_value=ALERT_THRESHOLDS["stage_utilization_percent"]["warning"], stage=stage, message=f"{stage.value} utilization at {sm.utilization_percent:.1f}% (warning: 85%)"))

        return alerts

router = APIRouter()


@router.get("/alerts")
def get_alerts():
    alerts = check_alerts_direct()
    return {
        "alerts": [a.model_dump(mode="json") for a in alerts],
        "summary": {
            "total": len(alerts),
            "critical": sum(1 for a in alerts if a.severity.value == "critical"),
            "warning": sum(1 for a in alerts if a.severity.value == "warning"),
            "info": sum(1 for a in alerts if a.severity.value == "info"),
        },
    }


@router.get("/alerts/thresholds")
def get_thresholds():
    return ALERT_THRESHOLDS
