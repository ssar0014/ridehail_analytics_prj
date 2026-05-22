from enum import StrEnum

class RideEventType(StrEnum):
    LOCATION_UPDATE = "location_update"
    STATUS_CHANGED  = "status_changed"
    FARE_UPDATED    = "fare_updated"
