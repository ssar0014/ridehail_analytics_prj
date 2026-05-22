import random
from faker import Faker
from uuid import uuid4

from enums.driver_status import DriverStatus
from models.driver_model import Driver

fake = Faker()

# Weighted statuses — most drivers online and available, few suspended
_STATUS_WEIGHTS = {
    DriverStatus.AVAILABLE: 0.50,
    DriverStatus.ON_TRIP:   0.25,
    DriverStatus.OFF_DUTY:  0.15,
    DriverStatus.OFFLINE:   0.08,
    DriverStatus.SUSPENDED: 0.02,
}

# San Francisco bounding box (default city)
_LAT_MIN, _LAT_MAX = 37.70, 37.82
_LON_MIN, _LON_MAX = -122.52, -122.35


class DriverGenerator:
    def __init__(self, lat_min=_LAT_MIN, lat_max=_LAT_MAX, lon_min=_LON_MIN, lon_max=_LON_MAX):
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max

    def generate(self) -> Driver:
        status = random.choices(
            list(_STATUS_WEIGHTS.keys()),
            weights=list(_STATUS_WEIGHTS.values()),
        )[0]

        return Driver(
            driver_id=uuid4(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=fake.phone_number(),
            email=fake.email(),
            license_number=fake.bothify(text="DL-#######"),
            status=status,
            current_latitude=round(random.uniform(self.lat_min, self.lat_max), 6),
            current_longitude=round(random.uniform(self.lon_min, self.lon_max), 6),
        )

    def generate_many(self, n: int) -> list[Driver]:
        return [self.generate() for _ in range(n)]
