import { useApi } from '../api/client'
import type { DriverDashboard } from '../api/types'
import { Loaded, RideTable, StatCard } from '../components/ui'
import { fmtInt, fmtMoney } from '../format'

export function DriverHome() {
  const dashboard = useApi<DriverDashboard>('/driver/me')

  return (
    <Loaded state={dashboard}>
      {(d) => (
        <>
          <h1>
            Hi, {d.first_name} <span className={`status status-${d.status}`}>{d.status.replace('_', ' ')}</span>
          </h1>

          <div className="stat-grid">
            <StatCard label="Completed rides" value={fmtInt(d.completed_rides)} />
            <StatCard label="Cancelled rides" value={fmtInt(d.cancelled_rides)} />
            <StatCard label="Total earnings" value={fmtMoney(d.total_earnings)} />
            <StatCard label="Rating" value={d.avg_rating ? `${d.avg_rating} ★` : '—'} />
          </div>

          <section className="card">
            <h2>Vehicles</h2>
            {d.vehicles.map((v) => (
              <p key={v.vehicle_id}>
                {v.year} {v.make} {v.model} · {v.color} · <code>{v.plate}</code>{' '}
                <span className="muted">({v.vehicle_type})</span>
              </p>
            ))}
          </section>

          <section className="card">
            <h2>Recent rides</h2>
            <RideTable rides={d.recent_rides} />
          </section>
        </>
      )}
    </Loaded>
  )
}
