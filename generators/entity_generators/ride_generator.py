import random
import math
from datetime import datetime, timedelta, timezone
from faker import Faker
from uuid import UUID, uuid4

from enums.ride_status import RideStatus
from models.ride_model import Ride

fake = Faker()

# San Francisco bounding box (default)
_LAT_MIN, _LAT_MAX = 37.70, 37.82
_LON_MIN, _LON_MAX = -122.52, -122.35

# Average city speed (km/h) used to derive duration from distance
_AVG_SPEED_KMH = 28.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance between two coordinates in kilometres."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class RideGenerator:
    def __init__(
        self,
        lat_min=_LAT_MIN, lat_max=_LAT_MAX,
        lon_min=_LON_MIN, lon_max=_LON_MAX,
        start_date: datetime | None = None,
        end_date:   datetime | None = None,
    ):
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.start_date = start_date or datetime.now(timezone.utc) - timedelta(days=365)
        self.end_date   = end_date   or datetime.now(timezone.utc)

    def _random_coord(self) -> tuple[float, float]:
        return (
            round(random.uniform(self.lat_min, self.lat_max), 6),
            round(random.uniform(self.lon_min, self.lon_max), 6),
        )

    def _random_timestamp_in_range(self) -> datetime:
        delta = self.end_date - self.start_date
        return self.start_date + timedelta(seconds=random.uniform(0, delta.total_seconds()))

    def generate(self, driver_id: UUID, customer_id: UUID, vehicle_id: UUID) -> Ride:
        pickup_lat,  pickup_lon  = self._random_coord()
        dropoff_lat, dropoff_lon = self._random_coord()

        distance_km = round(_haversine_km(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon), 2)
        # Add a routing factor — roads are longer than straight-line
        distance_km = round(distance_km * random.uniform(1.2, 1.5), 2)
        distance_km = max(distance_km, 0.5)

        duration_minutes = round((distance_km / _AVG_SPEED_KMH) * 60, 1)

        requested_at = self._random_timestamp_in_range()
        accepted_at  = requested_at + timedelta(minutes=random.uniform(1, 5))
        pickup_at    = accepted_at  + timedelta(minutes=random.uniform(3, 15))
        dropoff_at   = pickup_at    + timedelta(minutes=duration_minutes)

        return Ride(
            ride_id=uuid4(),
            driver_id=driver_id,
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            status=RideStatus.COMPLETED,
            pickup_latitude=pickup_lat,
            pickup_longitude=pickup_lon,
            pickup_address=fake.address().replace("\n", ", "),
            dropoff_latitude=dropoff_lat,
            dropoff_longitude=dropoff_lon,
            dropoff_address=fake.address().replace("\n", ", "),
            requested_at=requested_at,
            accepted_at=accepted_at,
            pickup_at=pickup_at,
            dropoff_at=dropoff_at,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
        )

    def generate_many(
        self,
        driver_ids:   list[UUID],
        customer_ids: list[UUID],
        vehicle_ids:  list[UUID],
        n: int,
    ) -> list[Ride]:
        return [
            self.generate(
                driver_id=random.choice(driver_ids),
                customer_id=random.choice(customer_ids),
                vehicle_id=random.choice(vehicle_ids),
            )
            for _ in range(n)
        ]
