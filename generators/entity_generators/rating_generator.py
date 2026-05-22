import random
from uuid import UUID

from enums.rated_entity_type import RatedEntityType
from models.rating_model import Rating

# Score distribution skewed high — mirrors real-world rideshare ratings
_SCORES        = [1.0, 2.0, 3.0, 4.0, 5.0]
_SCORE_WEIGHTS = [0.02, 0.03, 0.08, 0.27, 0.60]

_DRIVER_COMMENTS = [
    "Great driver, very smooth ride!",
    "Very friendly and professional.",
    "Arrived quickly, comfortable car.",
    "Safe and efficient route.",
    "Car was clean and driver was polite.",
    None, None, None,  # most riders don't leave a comment
]

_CUSTOMER_COMMENTS = [
    "Pleasant passenger, easy pickup.",
    "Respectful and on time.",
    "No issues at all.",
    None, None, None,
]


class RatingGenerator:
    def generate_pair(
        self,
        ride_id:     UUID,
        driver_id:   UUID,
        customer_id: UUID,
    ) -> tuple[Rating, Rating]:
        """Returns (driver_rating, customer_rating) for a completed ride."""
        driver_rating = Rating(
            ride_id=ride_id,
            rated_entity_id=driver_id,
            rated_entity_type=RatedEntityType.DRIVER,
            rated_by_id=customer_id,
            score=random.choices(_SCORES, weights=_SCORE_WEIGHTS)[0],
            comment=random.choice(_DRIVER_COMMENTS),
        )

        customer_rating = Rating(
            ride_id=ride_id,
            rated_entity_id=customer_id,
            rated_entity_type=RatedEntityType.CUSTOMER,
            rated_by_id=driver_id,
            score=random.choices(_SCORES, weights=_SCORE_WEIGHTS)[0],
            comment=random.choice(_CUSTOMER_COMMENTS),
        )

        return driver_rating, customer_rating

    def generate_many(
        self,
        ride_driver_customer_triples: list[tuple[UUID, UUID, UUID]],
    ) -> list[Rating]:
        ratings = []
        for ride_id, driver_id, customer_id in ride_driver_customer_triples:
            dr, cr = self.generate_pair(ride_id, driver_id, customer_id)
            ratings.extend([dr, cr])
        return ratings
