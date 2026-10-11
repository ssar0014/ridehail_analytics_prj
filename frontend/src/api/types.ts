// Mirrors api/schemas.py. Decimals arrive as strings to keep precision.

export type Role = 'admin' | 'customer' | 'driver'

export interface Token {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface CurrentUser {
  user_id: string
  email: string
  role: Role
  driver_id: string | null
  customer_id: string | null
  is_active: boolean
}

export interface ServiceHealth {
  ok: boolean
  detail: string
}

export interface Health {
  status: 'ok' | 'degraded'
  postgres: ServiceHealth
  clickhouse: ServiceHealth
}

export interface RideSummary {
  ride_id: string
  status: string
  pickup_address: string | null
  dropoff_address: string | null
  requested_at: string | null
  distance_km: string | null
  duration_minutes: string | null
  total: string | null
}

export interface AdminOverview {
  drivers: number
  customers: number
  vehicles: number
  rides_by_status: Record<string, number>
  gross_revenue: string
}

export interface VehicleInfo {
  vehicle_id: string
  make: string | null
  model: string | null
  year: number | null
  color: string | null
  plate: string | null
  vehicle_type: string
}

export interface DriverDashboard {
  driver_id: string
  first_name: string
  last_name: string
  email: string | null
  status: string
  vehicles: VehicleInfo[]
  completed_rides: number
  cancelled_rides: number
  total_earnings: string
  avg_rating: string | null
  recent_rides: RideSummary[]
}

export interface CustomerDashboard {
  customer_id: string
  first_name: string
  last_name: string
  email: string | null
  tier: number
  completed_rides: number
  cancelled_rides: number
  total_spent: string
  avg_rating: string | null
  recent_rides: RideSummary[]
}
