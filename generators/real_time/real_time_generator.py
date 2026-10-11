import heapq
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Generator
from uuid import UUID

from models.fare_model import Fare
from models.rating_model import Rating
from models.ride_event_model import RideEvent
from models.ride_model import Ride

from generators.entity_generators.customer_generator import CustomerGenerator
from generators.entity_generators.driver_generator import DriverGenerator
from generators.entity_generators.fare_generator import FareGenerator
from generators.entity_generators.rating_generator import RatingGenerator
from generators.entity_generators.ride_event_generator import RideEventGenerator
from generators.entity_generators.ride_generator import RideGenerator
from generators.entity_generators.vehicle_generator import VehicleGenerator

from enums.ride_status import RideStatus


@dataclass
class ActiveRide:
    """Tracks a single in-flight ride and its remaining event queue."""
    ride:    Ride
    events:  list[RideEvent]  # pre-computed, sorted by occurred_at
    fare:    Fare
    ratings: list[Rating]
    _cursor: int = field(default=0, init=False, repr=False)

    @property
    def peek(self) -> RideEvent | None:
        return self.events[self._cursor] if self._cursor < len(self.events) else None

    def pop(self) -> RideEvent:
        event = self.events[self._cursor]
        self._cursor += 1
        return event

    @property
    def done(self) -> bool:
        return self._cursor >= len(self.events)

    def __lt__(self, other: "ActiveRide") -> bool:
        if self.peek is None:
            return False
        if other.peek is None:
            return True
        return self.peek.occurred_at < other.peek.occurred_at


# Type alias for anything the real-time stream can emit
StreamPayload = RideEvent | Fare | Rating


class RealTimeGenerator:
    """
    Maintains a pool of n_concurrent active rides and yields their events in
    wall-clock order. After the final STATUS_CHANGED (COMPLETED) event for a
    ride, the associated Fare and Ratings are yielded immediately.

    Callers are responsible for sleeping until each event's occurred_at before
    forwarding downstream (e.g. to a Kafka producer).
    """

    def __init__(
        self,
        n_concurrent:                     int = 5,
        n_drivers:                        int = 20,
        n_customers:                      int = 50,
        location_update_interval_seconds: int = 15,
    ):
        self.n_concurrent = n_concurrent

        drivers   = DriverGenerator().generate_many(n_drivers)
        customers = CustomerGenerator().generate_many(n_customers)
        vehicles  = VehicleGenerator().generate_many([d.driver_id for d in drivers])

        self._driver_ids   = [d.driver_id   for d in drivers]
        self._customer_ids = [c.customer_id for c in customers]
        self._vehicle_ids  = [v.vehicle_id  for v in vehicles]

        self._ride_gen  = RideGenerator()
        self._fare_gen  = FareGenerator()
        self._rating_gen = RatingGenerator()
        self._event_gen  = RideEventGenerator(
            location_update_interval_seconds=location_update_interval_seconds
        )

    def _new_active_ride(self) -> ActiveRide:
        ride = self._ride_gen.generate(
            driver_id=random.choice(self._driver_ids),
            customer_id=random.choice(self._customer_ids),
            vehicle_id=random.choice(self._vehicle_ids),
        )

        # Override timestamps: ride starts right now
        now = datetime.now(timezone.utc)
        ride.status       = RideStatus.IN_PROGRESS
        ride.requested_at = now
        ride.accepted_at  = now
        ride.pickup_at    = now
        ride.dropoff_at   = now + timedelta(minutes=ride.duration_minutes or 1.0)

        events = self._event_gen.generate_for_ride(
            ride_id=ride.ride_id,
            pickup_lat=ride.pickup_latitude,
            pickup_lon=ride.pickup_longitude,
            dropoff_lat=ride.dropoff_latitude,
            dropoff_lon=ride.dropoff_longitude,
            pickup_at=ride.pickup_at,
            dropoff_at=ride.dropoff_at,
        )
        fare    = self._fare_gen.generate(ride.ride_id, ride.distance_km)
        ratings = list(self._rating_gen.generate_pair(
            ride.ride_id, ride.driver_id, ride.customer_id,
        ))

        return ActiveRide(ride=ride, events=events, fare=fare, ratings=ratings)

    def stream(self, max_rides: int | None = None) -> Generator[StreamPayload, None, None]:
        """
        Yields RideEvent, Fare, and Rating objects in chronological order.

        Args:
            max_rides: stop after this many completed rides (None = run forever)

        Usage:
            for payload in gen.stream(max_rides=10):
                wait_until(payload.occurred_at)   # caller sleeps
                emit_to_kafka(payload)
        """
        rides_completed = 0
        heap: list[ActiveRide] = []

        for _ in range(self.n_concurrent):
            heapq.heappush(heap, self._new_active_ride())

        while heap:
            active = heapq.heappop(heap)
            yield active.pop()

            if active.done:
                yield active.fare
                yield from active.ratings
                rides_completed += 1
                if max_rides is not None and rides_completed >= max_rides:
                    break
                heapq.heappush(heap, self._new_active_ride())
            else:
                heapq.heappush(heap, active)


if __name__ == "__main__":
    import time

    # 2-second intervals so you can watch events arrive without waiting 15s each
    gen = RealTimeGenerator(
        n_concurrent=3,
        n_drivers=10,
        n_customers=20,
        location_update_interval_seconds=2,
    )
    print("Streaming real-time (Ctrl+C to stop):\n")

    event_count = fare_count = rating_count = 0

    for payload in gen.stream():
        now = datetime.now(timezone.utc)

        if isinstance(payload, RideEvent):
            wait = (payload.occurred_at - now).total_seconds()
            if wait > 0:
                time.sleep(wait)
            print(f"  [{datetime.now(timezone.utc).isoformat(timespec='seconds')}]  "
                  f"RideEvent  {payload.event_type:<20s}  ride={str(payload.ride_id)[:8]}"
                  f"  lat={payload.latitude:.4f}  lon={payload.longitude:.4f}")
            event_count += 1

        elif isinstance(payload, Fare):
            print(f"  [{datetime.now(timezone.utc).isoformat(timespec='seconds')}]  "
                  f"Fare       total=${payload.total:6.2f}  surge={payload.surge_multiplier}x"
                  f"  ride={str(payload.ride_id)[:8]}")
            fare_count += 1

        elif isinstance(payload, Rating):
            print(f"  [{datetime.now(timezone.utc).isoformat(timespec='seconds')}]  "
                  f"Rating     {payload.rated_entity_type:<10s}  score={payload.score}"
                  f"  ride={str(payload.ride_id)[:8]}")
            rating_count += 1
