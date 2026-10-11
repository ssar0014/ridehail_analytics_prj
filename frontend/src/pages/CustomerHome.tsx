import { useApi } from '../api/client'
import type { CustomerDashboard } from '../api/types'
import { Loaded, RideTable, StatCard } from '../components/ui'
import { fmtInt, fmtMoney } from '../format'

const TIER_LABEL: Record<number, string> = { 1: 'Regular', 2: 'Silver', 3: 'Gold', 4: 'Platinum' }

export function CustomerHome() {
  const dashboard = useApi<CustomerDashboard>('/customer/me')

  return (
    <Loaded state={dashboard}>
      {(c) => (
        <>
          <h1>
            Hi, {c.first_name} <span className="role-badge">{TIER_LABEL[c.tier] ?? `Tier ${c.tier}`}</span>
          </h1>

          <div className="stat-grid">
            <StatCard label="Rides taken" value={fmtInt(c.completed_rides)} />
            <StatCard label="Cancelled" value={fmtInt(c.cancelled_rides)} />
            <StatCard label="Total spent" value={fmtMoney(c.total_spent)} />
            <StatCard label="Your rating" value={c.avg_rating ? `${c.avg_rating} ★` : '—'} />
          </div>

          <section className="card">
            <h2>Recent rides</h2>
            <RideTable rides={c.recent_rides} />
          </section>
        </>
      )}
    </Loaded>
  )
}
