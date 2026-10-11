import { Navigate, Outlet, useLocation } from 'react-router-dom'
import type { Role } from '../api/types'
import { useAuth } from './AuthContext'
import { ROLE_HOME } from './roles'

/** Route guard: signed-out users go to /login; signed-in users of another role go to their own home. */
export function RequireRole({ role }: { role: Role }) {
  const { user, restoring } = useAuth()
  const location = useLocation()

  if (restoring) return null
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (user.role !== role) return <Navigate to={ROLE_HOME[user.role]} replace />
  return <Outlet />
}
