"""Postgres queries shared by the driver and customer dashboards."""

from typing import Any, Literal
from uuid import UUID

from psycopg import AsyncConnection, sql

from enums.rated_entity_type import RatedEntityType
from enums.ride_status import RideStatus

Party = Literal["driver", "customer"]


async def ride_stats(conn: AsyncConnection[dict[str, Any]], party: Party, entity_id: UUID) -> dict[str, Any]:
    query = sql.SQL("""
        SELECT
            count(*) FILTER (WHERE r.status = %(completed)s) AS completed_rides,
            count(*) FILTER (WHERE r.status = %(cancelled)s) AS cancelled_rides,
            coalesce(sum(f.total), 0)                        AS fare_total
        FROM rides r
        LEFT JOIN fares f ON f.ride_id = r.ride_id
        WHERE r.{col} = %(id)s
    """).format(col=sql.Identifier(f"{party}_id"))
    async with conn.cursor() as cur:
        await cur.execute(query, {
            "completed": RideStatus.COMPLETED,
            "cancelled": RideStatus.CANCELLED,
            "id": entity_id,
        })
        return await cur.fetchone()


async def avg_rating(conn: AsyncConnection[dict[str, Any]], party: Party, entity_id: UUID) -> Any:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT round(avg(score), 2) AS avg_rating FROM ratings "
            "WHERE rated_entity_id = %s AND rated_entity_type = %s",
            (entity_id, RatedEntityType(party)),
        )
        return (await cur.fetchone())["avg_rating"]


async def recent_rides(
    conn: AsyncConnection[dict[str, Any]], party: Party, entity_id: UUID, limit: int = 10
) -> list[dict[str, Any]]:
    query = sql.SQL("""
        SELECT r.ride_id, r.status, r.pickup_address, r.dropoff_address, r.requested_at,
               r.distance_km, r.duration_minutes, f.total
        FROM rides r
        LEFT JOIN fares f ON f.ride_id = r.ride_id
        WHERE r.{col} = %s
        ORDER BY r.requested_at DESC NULLS LAST
        LIMIT %s
    """).format(col=sql.Identifier(f"{party}_id"))
    async with conn.cursor() as cur:
        await cur.execute(query, (entity_id, limit))
        return await cur.fetchall()
