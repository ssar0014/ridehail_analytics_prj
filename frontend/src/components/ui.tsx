import type { ReactNode } from 'react'
import type { ApiState } from '../api/client'
import type { RideSummary } from '../api/types'
import { fmtDateTime, fmtMoney } from '../format'

export function StatCard({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  )
}

/** Renders loading / error states, then `children(data)` once loaded. */
export function Loaded<T>({ state, children }: { state: ApiState<T>; children: (data: T) => ReactNode }) {
  if (state.loading) return <p className="muted">Loading…</p>
  if (state.error) return <p className="error">Couldn't load: {state.error}</p>
  return state.data ? children(state.data) : null
}

export function RideTable({ rides }: { rides: RideSummary[] }) {
  if (rides.length === 0) return <p className="muted">No rides yet.</p>
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Requested</th>
            <th>Status</th>
            <th>Pickup</th>
            <th>Dropoff</th>
            <th className="num">Distance</th>
            <th className="num">Fare</th>
          </tr>
        </thead>
        <tbody>
          {rides.map((r) => (
            <tr key={r.ride_id}>
              <td>{fmtDateTime(r.requested_at)}</td>
              <td>
                <span className={`status status-${r.status}`}>{r.status}</span>
              </td>
              <td>{r.pickup_address ?? '—'}</td>
              <td>{r.dropoff_address ?? '—'}</td>
              <td className="num">{r.distance_km ? `${r.distance_km} km` : '—'}</td>
              <td className="num">{fmtMoney(r.total)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
