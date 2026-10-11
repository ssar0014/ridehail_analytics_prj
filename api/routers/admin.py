from fastapi import APIRouter

from api.db import PgConn
from api.schemas import AdminOverview
from api.security import AdminUser

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverview)
async def overview(_: AdminUser, conn: PgConn) -> AdminOverview:
    # Full-table aggregates straight off the OLTP tables for now; these move to
    # ClickHouse once the batch pipeline populates it.
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT
                (SELECT count(*) FROM drivers)                AS drivers,
                (SELECT count(*) FROM customers)              AS customers,
                (SELECT count(*) FROM vehicles)               AS vehicles,
                (SELECT coalesce(sum(total), 0) FROM fares)   AS gross_revenue
        """)
        totals = await cur.fetchone()
        await cur.execute("SELECT status, count(*) AS n FROM rides GROUP BY status ORDER BY status")
        by_status = {r["status"]: r["n"] for r in await cur.fetchall()}

    return AdminOverview(**totals, rides_by_status=by_status)
