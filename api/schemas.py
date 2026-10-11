from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from enums.user_role import UserRole


# ── auth ──────────────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class CurrentUser(BaseModel):
    user_id: UUID
    email: str
    role: UserRole
    driver_id: UUID | None = None
    customer_id: UUID | None = None
    is_active: bool = True


# ── health ────────────────────────────────────────────────────────────────────
class ServiceHealth(BaseModel):
    ok: bool
    detail: str


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    postgres: ServiceHealth
    clickhouse: ServiceHealth


# ── shared ────────────────────────────────────────────────────────────────────
class RideSummary(BaseModel):
    ride_id: UUID
    status: str
    pickup_address: str | None
    dropoff_address: str | None
    requested_at: datetime | None
    distance_km: Decimal | None
    duration_minutes: Decimal | None
    total: Decimal | None


# ── admin ─────────────────────────────────────────────────────────────────────
class AdminOverview(BaseModel):
    drivers: int
    customers: int
    vehicles: int
    rides_by_status: dict[str, int]
    gross_revenue: Decimal


# ── driver ────────────────────────────────────────────────────────────────────
class VehicleInfo(BaseModel):
    vehicle_id: UUID
    make: str | None
    model: str | None
    year: int | None
    color: str | None
    plate: str | None
    vehicle_type: str


class DriverDashboard(BaseModel):
    driver_id: UUID
    first_name: str
    last_name: str
    email: str | None
    status: str
    vehicles: list[VehicleInfo]
    completed_rides: int
    cancelled_rides: int
    total_earnings: Decimal
    avg_rating: Decimal | None
    recent_rides: list[RideSummary]


# ── customer ──────────────────────────────────────────────────────────────────
class CustomerDashboard(BaseModel):
    customer_id: UUID
    first_name: str
    last_name: str
    email: str | None
    tier: int
    completed_rides: int
    cancelled_rides: int
    total_spent: Decimal
    avg_rating: Decimal | None
    recent_rides: list[RideSummary]
