"""Hospital LOB configuration and constants."""

from enum import Enum


class StageEnum(str, Enum):
    ADMISSION = "admission"
    TRIAGE = "triage"
    DIAGNOSTICS = "diagnostics"
    SURGICAL = "surgical"
    RECOVERY_PACU = "recovery_pacu"
    WARD_ICU = "ward_icu"
    DISCHARGE = "discharge"


class PriorityEnum(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    STANDARD = "standard"


class SeverityEnum(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PharmacyOrderType(str, Enum):
    STANDARD = "standard"
    STAT = "stat"
    IV_COMPOUND = "iv_compound"


class PharmacyStageEnum(str, Enum):
    ORDER_RECEIPT = "order_receipt"
    VERIFICATION = "verification"
    COMPOUNDING = "compounding"
    LABELLING = "labelling"
    ADMINISTRATION = "administration"


# Ordered list of patient flow stages
PATIENT_FLOW_STAGES = list(StageEnum)

# Display names
STAGE_DISPLAY_NAMES = {
    StageEnum.ADMISSION: "Admission & Registration",
    StageEnum.TRIAGE: "Triage & Assessment",
    StageEnum.DIAGNOSTICS: "Diagnostics (Labs/Imaging)",
    StageEnum.SURGICAL: "Surgical / Procedure",
    StageEnum.RECOVERY_PACU: "Recovery (PACU)",
    StageEnum.WARD_ICU: "Ward / ICU Stay",
    StageEnum.DISCHARGE: "Discharge & Handoff",
}

# Mean service times in minutes (log-normal distribution parameters)
STAGE_SERVICE_TIMES = {
    StageEnum.ADMISSION: {"mean": 15, "std": 5},
    StageEnum.TRIAGE: {"mean": 20, "std": 10},
    StageEnum.DIAGNOSTICS: {"mean": 90, "std": 45},
    StageEnum.SURGICAL: {"mean": 120, "std": 60},
    StageEnum.RECOVERY_PACU: {"mean": 60, "std": 20},
    StageEnum.WARD_ICU: {"mean": 2880, "std": 1440},  # 48 hours
    StageEnum.DISCHARGE: {"mean": 90, "std": 60},
}

# Default capacity per stage (beds/slots)
DEFAULT_STAGE_CAPACITY = {
    StageEnum.ADMISSION: {"capacity": 10, "staff": 5},
    StageEnum.TRIAGE: {"capacity": 8, "staff": 4},
    StageEnum.DIAGNOSTICS: {"capacity": 15, "staff": 8},
    StageEnum.SURGICAL: {"capacity": 6, "staff": 12},
    StageEnum.RECOVERY_PACU: {"capacity": 12, "staff": 6},
    StageEnum.WARD_ICU: {"capacity": 100, "staff": 30},
    StageEnum.DISCHARGE: {"capacity": 5, "staff": 3},
}

# Probability that a patient requires surgical intervention
SURGICAL_PROBABILITY = 0.30

# Alert thresholds
ALERT_THRESHOLDS = {
    "ed_wait_minutes": {"warning": 30, "critical": 60},
    "alos_hours": {"warning": 72, "critical": 120},
    "bed_occupancy_percent": {"warning": 85, "critical": 95},
    "or_utilization_percent": {"warning": 90, "critical": 98},
    "mtat_minutes": {"warning": 45, "critical": 90},
    "stage_utilization_percent": {"warning": 85, "critical": 95},
}

# Target throughput per hour (patients)
DEFAULT_TARGET_THROUGHPUT = 10

# Dashboard settings
DASHBOARD_REFRESH_SECONDS = 30
