from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from enums.cancelled_by import CancelledBy
from enums.ride_status import RideStatus

@dataclass
class Ride:
    driver_id:          UUID
    customer_id:        UUID
    vehicle_id:         UUID
    ride_id:            UUID            = field(default_factory=uuid4)
    status:             RideStatus      = RideStatus.REQUESTED
    pickup_latitude:    float           = 0.0
    pickup_longitude:   float           = 0.0
    pickup_address:     str             = ""
    dropoff_latitude:   float | None    = None
    dropoff_longitude:  float | None    = None
    dropoff_address:    str | None      = None
    requested_at:       datetime        = field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_at:        datetime | None = None
    pickup_at:          datetime | None = None
    dropoff_at:         datetime | None = None
    distance_km:        float | None    = None
    duration_minutes:   float | None    = None
    cancelled_by:       CancelledBy | None = None
    created_at:         datetime        = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:         datetime        = field(default_factory=lambda: datetime.now(timezone.utc))


if __name__ == "__main__":
    ride = Ride(
        driver_id=uuid4(),
        customer_id=uuid4(),
        vehicle_id=uuid4(),
        pickup_latitude=37.7749,
        pickup_longitude=-122.4194,
        pickup_address="367 Fell St, San Francisco, CA",
        dropoff_latitude=37.8044,
        dropoff_longitude=-122.2712,
        dropoff_address="1 Lake Merritt Blvd, Oakland, CA",
    )
    print(ride)
