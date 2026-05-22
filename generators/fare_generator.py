import random
from uuid import UUID

from models.fare_model import Fare

_BASE_FARE        = 2.50   # fixed pickup fee
_RATE_PER_KM      = 1.50   # per kilometre charge
_TAX_RATE         = 0.10   # 10% of pre-tip subtotal

# Surge multipliers and their probability of occurring
_SURGE_MULTIPLIERS = [1.0,  1.2,  1.5,  1.8,  2.0,  2.5]
_SURGE_WEIGHTS     = [0.70, 0.12, 0.09, 0.05, 0.03, 0.01]


class FareGenerator:
    def generate(self, ride_id: UUID, distance_km: float) -> Fare:
        base_fare     = round(_BASE_FARE, 2)
        distance_fare = round(distance_km * _RATE_PER_KM, 2)

        surge_multiplier = random.choices(_SURGE_MULTIPLIERS, weights=_SURGE_WEIGHTS)[0]

        subtotal = (base_fare + distance_fare) * surge_multiplier
        taxes    = round(subtotal * _TAX_RATE, 2)
        tip      = round(random.choice([0.0, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0]), 2)

        return Fare(
            ride_id=ride_id,
            base_fare=base_fare,
            distance_fare=distance_fare,
            surge_multiplier=surge_multiplier,
            tip=tip,
            taxes=taxes,
        )

    def generate_many(self, ride_id_distance_pairs: list[tuple[UUID, float]]) -> list[Fare]:
        return [self.generate(ride_id, distance_km) for ride_id, distance_km in ride_id_distance_pairs]
