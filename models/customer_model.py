from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4
from enums.customer_status import CustomerStatus, CustomerTier

@dataclass
class Customer:
    customer_id:  UUID     = field(default_factory=uuid4)
    first_name:   str      = ""
    last_name:    str      = ""
    phone_number: str      = ""
    email:        str      = ""
    payment_token: str | None = None
    status: CustomerStatus = CustomerStatus.ACTIVE
    tier: CustomerTier = CustomerTier.REGULAR
    created_at:   datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:   datetime = field(default_factory=lambda: datetime.now(timezone.utc))


if __name__ == "__main__":
    customer = Customer(
        first_name="Jane",
        last_name="Smith",
        phone_number="987-654-3210",
        email="jane.smith@gmail.com",
        payment_token="tok_visa_abc123",
        status=CustomerStatus.ACTIVE,
        tier=CustomerTier.GOLD
    )
    print(customer)
