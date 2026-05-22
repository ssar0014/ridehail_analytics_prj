from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from enums.ride_event_type import RideEventType


@dataclass
class RideEvent:
    ride_id:    UUID
    event_type: RideEventType
    latitude:   float
    longitude:  float
    event_id:   UUID        = field(default_factory=uuid4)
    occurred_at: datetime   = field(default_factory=lambda: datetime.now(timezone.utc))


if __name__ == "__main__":
    ride_id = uuid4()

    events = [
        RideEvent(
            ride_id=ride_id,
            event_type=RideEventType.STATUS_CHANGED,
            latitude=37.7749,
            longitude=-122.4194,
        ),
        RideEvent(
            ride_id=ride_id,
            event_type=RideEventType.LOCATION_UPDATE,
            latitude=37.7800,
            longitude=-122.4150,
        ),
        RideEvent(
            ride_id=ride_id,
            event_type=RideEventType.LOCATION_UPDATE,
            latitude=37.7850,
            longitude=-122.4100,
        ),
    ]

    for event in events:
        print(event)
