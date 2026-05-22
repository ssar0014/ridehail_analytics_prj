from uuid import UUID, uuid4
from enums.driver_status import DriverStatus
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class Driver:
    driver_id: UUID = field(default_factory=uuid4)
    first_name: str = ""
    last_name: str = ""
    phone_number: str = ""
    email: str = ""
    license_number: str = ""
    status: DriverStatus = DriverStatus.AVAILABLE
    current_latitude: float = 0.0
    current_longitude: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


if __name__ == "__main__":
    fname = "John"
    lname = "Doe"
    phone_number = "123-456-7890"
    email = "john.doe@gmail.com"
    license_number = "D1234567"
    status = DriverStatus.AVAILABLE
    current_latitude = 37.7749
    current_longitude = -122.4194
    driver = Driver(first_name=fname, last_name=lname, phone_number=phone_number, email=email, license_number=license_number, status=status, current_latitude=current_latitude, current_longitude=current_longitude)
    print(driver)