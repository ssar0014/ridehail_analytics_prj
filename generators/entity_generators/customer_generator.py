import random
from faker import Faker
from uuid import uuid4

from enums.customer_status import CustomerStatus, CustomerTier
from models.customer_model import Customer

fake = Faker()

_EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "hotmail.com",
    "outlook.com", "protonmail.com", "icloud.com",
]


def _random_email(first: str, last: str) -> str:
    suffix = uuid4().hex[:8]
    domain = random.choice(_EMAIL_DOMAINS)
    return f"{first.lower()}.{last.lower()}.{suffix}@{domain}"

# Weighted tiers — most customers are regular, fewer reach platinum
_TIER_WEIGHTS = {
    CustomerTier.REGULAR:  0.60,
    CustomerTier.SILVER:   0.25,
    CustomerTier.GOLD:     0.12,
    CustomerTier.PLATINUM: 0.03,
}

# Most customers are active; inactive represents churned users
_STATUS_WEIGHTS = {
    CustomerStatus.ACTIVE:   0.85,
    CustomerStatus.INACTIVE: 0.15,
}


class CustomerGenerator:
    def generate(self) -> Customer:
        tier = random.choices(
            list(_TIER_WEIGHTS.keys()),
            weights=list(_TIER_WEIGHTS.values()),
        )[0]

        status = random.choices(
            list(_STATUS_WEIGHTS.keys()),
            weights=list(_STATUS_WEIGHTS.values()),
        )[0]

        first_name = fake.first_name()
        last_name  = fake.last_name()
        return Customer(
            customer_id=uuid4(),
            first_name=first_name,
            last_name=last_name,
            phone_number=fake.phone_number(),
            email=_random_email(first_name, last_name),
            payment_token=f"tok_{fake.bothify(text='????####????####')}",
            status=status,
            tier=tier,
        )

    def generate_many(self, n: int) -> list[Customer]:
        return [self.generate() for _ in range(n)]
