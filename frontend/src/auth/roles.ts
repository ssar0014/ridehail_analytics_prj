import type { Role } from '../api/types'

export const ROLE_HOME: Record<Role, string> = {
  admin: '/admin',
  driver: '/driver',
  customer: '/customer',
}

export const ROLE_LABEL: Record<Role, string> = {
  admin: 'Admin',
  driver: 'Driver',
  customer: 'Rider',
}
