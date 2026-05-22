from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from enums.rated_entity_type import RatedEntityType


@dataclass
class Rating:
    ride_id:           UUID
    rated_entity_id:   UUID
    rated_entity_type: RatedEntityType
    rated_by_id:       UUID
    score:             float
    rating_id:         UUID        = field(default_factory=uuid4)
    comment:           str | None  = None
    created_at:        datetime    = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not (1.0 <= self.score <= 5.0):
            raise ValueError(f"score must be between 1.0 and 5.0, got {self.score}")


if __name__ == "__main__":
    driver_id  = uuid4()
    customer_id = uuid4()
    ride_id    = uuid4()

    driver_rating = Rating(
        ride_id=ride_id,
        rated_entity_id=driver_id,
        rated_entity_type=RatedEntityType.DRIVER,
        rated_by_id=customer_id,
        score=4.5,
        comment="Smooth ride, very polite.",
    )

    customer_rating = Rating(
        ride_id=ride_id,
        rated_entity_id=customer_id,
        rated_entity_type=RatedEntityType.CUSTOMER,
        rated_by_id=driver_id,
        score=5.0,
    )

    print(driver_rating)
    print(customer_rating)
