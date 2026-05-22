import random
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from enums.ride_event_type import RideEventType
from enums.ride_status import RideStatus
from models.ride_event_model import RideEvent


def _interpolate(start: float, end: float, t: float) -> float:
    """Linear interpolation between two values at position t in [0, 1]."""
    return round(start + (end - start) * t, 6)


class RideEventGenerator:
    def __init__(self, location_update_interval_seconds: int = 15):
        self.location_update_interval_seconds = location_update_interval_seconds

    def generate_for_ride(
        self,
        ride_id:       UUID,
        pickup_lat:    float,
        pickup_lon:    float,
        dropoff_lat:   float,
        dropoff_lon:   float,
        pickup_at:     datetime,
        dropoff_at:    datetime,
    ) -> list[RideEvent]:
        """
        Generates the full event stream for one completed ride:
          - STATUS_CHANGED at pickup (IN_PROGRESS)
          - Periodic LOCATION_UPDATEs between pickup and dropoff
          - STATUS_CHANGED at dropoff (COMPLETED)
        """
        events: list[RideEvent] = []
        duration_seconds = (dropoff_at - pickup_at).total_seconds()

        # Ride starts
        events.append(RideEvent(
            event_id=uuid4(),
            ride_id=ride_id,
            event_type=RideEventType.STATUS_CHANGED,
            latitude=pickup_lat,
            longitude=pickup_lon,
            occurred_at=pickup_at,
        ))

        # Periodic location updates along the route
        elapsed = self.location_update_interval_seconds
        while elapsed < duration_seconds:
            t = elapsed / duration_seconds
            # Small random jitter simulates GPS noise
            lat = _interpolate(pickup_lat, dropoff_lat, t) + random.uniform(-0.001, 0.001)
            lon = _interpolate(pickup_lon, dropoff_lon, t) + random.uniform(-0.001, 0.001)

            events.append(RideEvent(
                event_id=uuid4(),
                ride_id=ride_id,
                event_type=RideEventType.LOCATION_UPDATE,
                latitude=round(lat, 6),
                longitude=round(lon, 6),
                occurred_at=pickup_at + timedelta(seconds=elapsed),
            ))
            elapsed += self.location_update_interval_seconds

        # Ride ends
        events.append(RideEvent(
            event_id=uuid4(),
            ride_id=ride_id,
            event_type=RideEventType.STATUS_CHANGED,
            latitude=dropoff_lat,
            longitude=dropoff_lon,
            occurred_at=dropoff_at,
        ))

        return events
