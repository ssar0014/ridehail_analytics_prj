import random
from faker import Faker
from uuid import UUID, uuid4

from enums.vehicle_status import VehicleStatus
from enums.vehicle_type import VehicleType
from models.vehicle_model import Vehicle

fake = Faker()

# Curated make/model pools per vehicle type
_VEHICLES_BY_TYPE: dict[VehicleType, list[tuple[str, str]]] = {
    VehicleType.ECONOMY: [
        ("Toyota", "Camry"), ("Toyota", "Corolla"), ("Honda", "Civic"),
        ("Honda", "Accord"), ("Hyundai", "Elantra"), ("Nissan", "Altima"),
        ("Chevrolet", "Malibu"), ("Ford", "Fusion"),
    ],
    VehicleType.PREMIUM: [
        ("BMW", "3 Series"), ("Audi", "A4"), ("Mercedes-Benz", "C-Class"),
        ("Lexus", "ES"), ("Cadillac", "CT5"),
    ],
    VehicleType.XL: [
        ("Ford", "Explorer"), ("Chevrolet", "Suburban"), ("Toyota", "Highlander"),
        ("GMC", "Yukon"), ("Ford", "F-150"),
    ],
    VehicleType.GREEN: [
        ("Toyota", "Prius"), ("Tesla", "Model 3"), ("Nissan", "Leaf"),
        ("Chevrolet", "Bolt"), ("Hyundai", "Ioniq"),
    ],
    VehicleType.BLACK: [
        ("Mercedes-Benz", "S-Class"), ("BMW", "7 Series"), ("Cadillac", "CT6"),
        ("Lincoln", "Town Car"), ("Genesis", "G90"),
    ],
    VehicleType.MINI: [
        ("Mini", "Cooper"), ("Ford", "Fiesta"), ("Volkswagen", "Polo"),
        ("Toyota", "Yaris"), ("Honda", "Fit"),
    ],
    VehicleType.BIKE: [
        ("Trek", "FX3"), ("Giant", "Escape"), ("Specialized", "Sirrus"),
    ],
}

_COLORS = ["White", "Black", "Silver", "Gray", "Blue", "Red", "Pearl White", "Charcoal"]

# Weighted statuses — most vehicles are active
_STATUS_WEIGHTS = {
    VehicleStatus.ACTIVE:      0.88,
    VehicleStatus.MAINTENANCE: 0.09,
    VehicleStatus.RETIRED:     0.03,
}

# Weighted vehicle types — economy dominates, bikes rare
_TYPE_WEIGHTS = {
    VehicleType.ECONOMY: 0.45,
    VehicleType.GREEN:   0.20,
    VehicleType.PREMIUM: 0.12,
    VehicleType.XL:      0.10,
    VehicleType.BLACK:   0.07,
    VehicleType.MINI:    0.05,
    VehicleType.BIKE:    0.01,
}


class VehicleGenerator:
    def generate(self, driver_id: UUID) -> Vehicle:
        vehicle_type = random.choices(
            list(_TYPE_WEIGHTS.keys()),
            weights=list(_TYPE_WEIGHTS.values()),
        )[0]

        status = random.choices(
            list(_STATUS_WEIGHTS.keys()),
            weights=list(_STATUS_WEIGHTS.values()),
        )[0]

        make, model = random.choice(_VEHICLES_BY_TYPE[vehicle_type])

        return Vehicle(
            driver_id=driver_id,
            vehicle_id=uuid4(),
            make=make,
            model=model,
            year=random.randint(2015, 2024),
            color=random.choice(_COLORS),
            plate=fake.bothify(text="???-####").upper(),
            vehicle_type=vehicle_type,
            status=status,
        )

    def generate_many(self, driver_ids: list[UUID]) -> list[Vehicle]:
        return [self.generate(driver_id) for driver_id in driver_ids]
