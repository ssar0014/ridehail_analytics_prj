from enum import StrEnum

class DriverStatus(StrEnum):
    AVAILABLE  = "available"
    ON_TRIP    = "on_trip"
    OFF_DUTY   = "off_duty"
    OFFLINE    = "offline"
    SUSPENDED  = "suspended"