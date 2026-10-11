import { useApi } from '../api/client'
import type { AdminOverview } from '../api/types'
import { Loaded, StatCard } from '../components/ui'
import { fmtInt, fmtMoney } from '../format'

export function AdminHome() {
  const overview = useApi<AdminOverview>('/admin/overview')

  return (
    <>
      <h1>Operations overview</h1>
      <Loaded state={overview}>
        {(o) => {
          const totalRides = Object.values(o.rides_by_status).reduce((a, b) => a + b, 0)
          return (
            <>
              <div className="stat-grid">
                <StatCard label="Drivers" value={fmtInt(o.drivers)} />
                <StatCard label="Riders" value={fmtInt(o.customers)} />
                <StatCard label="Vehicles" value={fmtInt(o.vehicles)} />
                <StatCard label="Rides" value={fmtInt(totalRides)} />
                <StatCard label="Gross revenue" value={fmtMoney(o.gross_revenue)} />
              </div>

              <section className="card">
                <h2>Rides by status</h2>
                <table>
                  <tbody>
                    {Object.entries(o.rides_by_status).map(([status, n]) => (
                      <tr key={status}>
                        <td>
                          <span className={`status status-${status}`}>{status}</span>
                        </td>
                        <td className="num">{fmtInt(n)}</td>
                        <td className="num muted">{((n / totalRides) * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>
            </>
          )
        }}
      </Loaded>
    </>
  )
}
