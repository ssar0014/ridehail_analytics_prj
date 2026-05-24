from enum import StrEnum


class CancelledBy(StrEnum):
    DRIVER   = "driver"
    CUSTOMER = "customer"
    ADMIN    = "admin"
