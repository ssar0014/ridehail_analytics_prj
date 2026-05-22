from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Fare:
    ride_id:          UUID
    base_fare:        float
    distance_fare:    float
    fare_id:          UUID     = field(default_factory=uuid4)
    surge_multiplier: float    = 1.0
    tip:              float    = 0.0
    taxes:            float    = 0.0
    currency:         str      = "USD"
    surge_amount:     float    = field(init=False)
    total:            float    = field(init=False)
    created_at:       datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if self.surge_multiplier > 1.0:
            self.surge_amount = round((self.base_fare + self.distance_fare) * (self.surge_multiplier - 1), 2)
            self.total = round((self.base_fare + self.distance_fare) * self.surge_multiplier + self.tip + self.taxes, 2)
        else:
            self.surge_amount = 0.0
            self.total = round(self.base_fare + self.distance_fare + self.tip + self.taxes, 2)

if __name__ == "__main__":
    fare = Fare(
        ride_id=uuid4(),
        base_fare=3.50,
        distance_fare=11.20,
        surge_multiplier=1.5,
        tip=2.00,
        taxes=1.10,
    )
    print(fare)
    print(f"Surge amount: ${fare.surge_amount}")
    print(f"Total:        ${fare.total}")
