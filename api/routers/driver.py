from fastapi import APIRouter, HTTPException, status

from api import queries
from api.db import PgConn
from api.schemas import DriverDashboard
from api.security import DriverUser

router = APIRouter(prefix="/driver", tags=["driver"])


@router.get("/me", response_model=DriverDashboard)
async def dashboard(user: DriverUser, conn: PgConn) -> DriverDashboard:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT driver_id, first_name, last_name, email, status FROM drivers WHERE driver_id = %s",
            (user.driver_id,),
        )
        driver = await cur.fetchone()
        if driver is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Driver record not found")
        await cur.execute(
            "SELECT vehicle_id, make, model, year, color, plate, vehicle_type "
            "FROM vehicles WHERE driver_id = %s ORDER BY created_at",
            (user.driver_id,),
        )
        vehicles = await cur.fetchall()

    stats = await queries.ride_stats(conn, "driver", user.driver_id)
    return DriverDashboard(
        **driver,
        vehicles=vehicles,
        completed_rides=stats["completed_rides"],
        cancelled_rides=stats["cancelled_rides"],
        total_earnings=stats["fare_total"],
        avg_rating=await queries.avg_rating(conn, "driver", user.driver_id),
        recent_rides=await queries.recent_rides(conn, "driver", user.driver_id),
    )
