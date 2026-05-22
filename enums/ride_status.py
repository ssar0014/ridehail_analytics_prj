from enum import StrEnum

class RideStatus(StrEnum):
    REQUESTED         = "requested"
    ACCEPTED          = "accepted"
    EN_ROUTE_PICKUP   = "en_route_to_pickup"
    ARRIVED_PICKUP    = "arrived_at_pickup"
    IN_PROGRESS       = "in_progress"
    COMPLETED         = "completed"
    CANCELLED         = "cancelled"
