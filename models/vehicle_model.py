from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from enums.vehicle_status import VehicleStatus
from enums.vehicle_type import VehicleType

@dataclass
class Vehicle:
    driver_id:    UUID
    vehicle_id:   UUID          = field(default_factory=uuid4)
    make:         str           = ""
    model:        str           = ""
    year:         int           = 0
    color:        str           = ""
    plate:        str           = ""
    vehicle_type: VehicleType   = VehicleType.ECONOMY
    status:       VehicleStatus = VehicleStatus.ACTIVE
    created_at:   datetime      = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:   datetime      = field(default_factory=lambda: datetime.now(timezone.utc))


if __name__ == "__main__":
    vehicle = Vehicle(
        driver_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Silver",
        plate="ABC-1234",
        vehicle_type=VehicleType.ECONOMY,
    )
    print(vehicle)
