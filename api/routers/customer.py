from fastapi import APIRouter, HTTPException, status

from api import queries
from api.db import PgConn
from api.schemas import CustomerDashboard
from api.security import CustomerUser

router = APIRouter(prefix="/customer", tags=["customer"])


@router.get("/me", response_model=CustomerDashboard)
async def dashboard(user: CustomerUser, conn: PgConn) -> CustomerDashboard:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT customer_id, first_name, last_name, email, tier FROM customers WHERE customer_id = %s",
            (user.customer_id,),
        )
        customer = await cur.fetchone()
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Customer record not found")

    stats = await queries.ride_stats(conn, "customer", user.customer_id)
    return CustomerDashboard(
        **customer,
        completed_rides=stats["completed_rides"],
        cancelled_rides=stats["cancelled_rides"],
        total_spent=stats["fare_total"],
        avg_rating=await queries.avg_rating(conn, "customer", user.customer_id),
        recent_rides=await queries.recent_rides(conn, "customer", user.customer_id),
    )
