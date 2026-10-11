import { Link, Outlet } from 'react-router-dom'
import { useApi } from '../api/client'
import type { Health } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { ROLE_HOME, ROLE_LABEL } from '../auth/roles'

export function Layout() {
  const { user, signOut } = useAuth()
  const health = useApi<Health>('/health')

  return (
    <div className="shell">
      <header className="topbar">
        <Link to={user ? ROLE_HOME[user.role] : '/'} className="brand">
          RideHail
        </Link>
        {user && <span className="role-badge">{ROLE_LABEL[user.role]}</span>}
        <div className="spacer" />
        {health.data && (
          <span
            className={`health-dot ${health.data.status}`}
            title={`Postgres: ${health.data.postgres.detail}\nClickHouse: ${health.data.clickhouse.detail}`}
          >
            {health.data.status === 'ok' ? 'All systems up' : 'Degraded'}
          </span>
        )}
        {user && (
          <>
            <span className="muted">{user.email}</span>
            <button className="btn-ghost" onClick={signOut}>
              Sign out
            </button>
          </>
        )}
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
