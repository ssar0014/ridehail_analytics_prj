from enum import IntEnum, StrEnum

class CustomerStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class CustomerTier(IntEnum):
    REGULAR = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4