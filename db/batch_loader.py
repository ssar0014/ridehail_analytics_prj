"""
Loads a BatchDataset into Postgres using psycopg3's COPY protocol.

Usage:
    uv run python db/batch_loader.py
"""

import time

import psycopg

from db.connection import get_conn
from enums.ride_event_type import RideEventType
from enums.ride_status import RideStatus
from generators.batch.batch_generator import BatchDataset
from models.customer_model import Customer
from models.driver_model import Driver
from models.fare_model import Fare
from models.rating_model import Rating
from models.ride_event_model import RideEvent
from models.ride_model import Ride
from models.vehicle_model import Vehicle


def _copy_drivers(conn: psycopg.Connection, rows: list[Driver]) -> None:
    with conn.cursor() as cur:
        with cur.copy(
            "COPY drivers (driver_id, first_name, last_name, phone_number, email, "
            "license_number, status, current_latitude, current_longitude, "
            "created_at, updated_at) FROM STDIN"
        ) as copy:
            for d in rows:
                copy.write_row((
                    d.driver_id, d.first_name, d.last_name, d.phone_number, d.email,
                    d.license_number, d.status,
                    d.current_latitude, d.current_longitude,
                    d.created_at, d.updated_at,
                ))


def _copy_customers(conn: psycopg.Connection, rows: list[Customer]) -> None:
    with conn.cursor() as cur:
        with cur.copy(
            "COPY customers (customer_id, first_name, last_name, phone_number, email, "
            "payment_token, status, tier, created_at, updated_at) FROM STDIN"
        ) as copy:
            for c in rows:
                copy.write_row((
                    c.customer_id, c.first_name, c.last_name, c.phone_number, c.email,
                    c.payment_token, c.status, c.tier.value,
                    c.created_at, c.updated_at,
                ))


def _copy_vehicles(conn: psycopg.Connection, rows: list[Vehicle]) -> None:
    with conn.cursor() as cur:
        with cur.copy(
            "COPY vehicles (vehicle_id, driver_id, make, model, year, color, plate, "
            "vehicle_type, status, created_at, updated_at) FROM STDIN"
        ) as copy:
            for v in rows:
                copy.write_row((
                    v.vehicle_id, v.driver_id, v.make, v.model, v.year, v.color, v.plate,
                    v.vehicle_type, v.status, v.created_at, v.updated_at,
                ))


def _copy_rides(conn: psycopg.Connection, rows: list[Ride]) -> None:
    with conn.cursor() as cur:
        with cur.copy(
            "COPY rides (ride_id, driver_id, customer_id, vehicle_id, status, "
            "pickup_latitude, pickup_longitude, pickup_address, "
            "dropoff_latitude, dropoff_longitude, dropoff_address, "
            "requested_at, accepted_at, pickup_at, dropoff_at, "
            "distance_km, duration_minutes, cancelled_by, created_at, updated_at) FROM STDIN"
        ) as copy:
            for r in rows:
                copy.write_row((
                    r.ride_id, r.driver_id, r.customer_id, r.vehicle_id, r.status,
                    r.pickup_latitude, r.pickup_longitude, r.pickup_address,
                    r.dropoff_latitude, r.dropoff_longitude, r.dropoff_address,
                    r.requested_at, r.accepted_at, r.pickup_at, r.dropoff_at,
                    r.distance_km, r.duration_minutes, r.cancelled_by,
                    r.created_at, r.updated_at,
                ))


def _copy_fares(conn: psycopg.Connection, rows: list[Fare]) -> None:
    with conn.cursor() as cur:
        with cur.copy(
            "COPY fares (fare_id, ride_id, base_fare, distance_fare, surge_multiplier, "
            "surge_amount, tip, taxes, total, currency, created_at) FROM STDIN"
        ) as copy:
            for f in rows:
                copy.write_row((
                    f.fare_id, f.ride_id, f.base_fare, f.distance_fare, f.surge_multiplier,
                    f.surge_amount, f.tip, f.taxes, f.total, f.currency, f.created_at,
                ))


def _copy_ratings(conn: psycopg.Connection, rows: list[Rating]) -> None:
    with conn.cursor() as cur:
        with cur.copy(
            "COPY ratings (rating_id, ride_id, rated_entity_id, rated_entity_type, "
            "rated_by_id, score, comment, created_at) FROM STDIN"
        ) as copy:
            for r in rows:
                copy.write_row((
                    r.rating_id, r.ride_id, r.rated_entity_id, r.rated_entity_type,
                    r.rated_by_id, r.score, r.comment, r.created_at,
                ))


def _copy_ride_events(conn: psycopg.Connection, rows: list[RideEvent]) -> None:
    with conn.cursor() as cur:
        with cur.copy(
            "COPY ride_events (event_id, ride_id, event_type, latitude, longitude, "
            "occurred_at) FROM STDIN"
        ) as copy:
            for e in rows:
                copy.write_row((
                    e.event_id, e.ride_id, e.event_type,
                    e.latitude, e.longitude, e.occurred_at,
                ))


def load_batch(dataset: BatchDataset) -> None:
    print(f"Loading {dataset.summary()} ...")
    with get_conn() as conn:
        _copy_drivers(conn, dataset.drivers)
        print(f"  drivers       {len(dataset.drivers):>6,}")
        _copy_customers(conn, dataset.customers)
        print(f"  customers     {len(dataset.customers):>6,}")
        _copy_vehicles(conn, dataset.vehicles)
        print(f"  vehicles      {len(dataset.vehicles):>6,}")
        _copy_rides(conn, dataset.rides)
        print(f"  rides         {len(dataset.rides):>6,}")
        _copy_fares(conn, dataset.fares)
        print(f"  fares         {len(dataset.fares):>6,}")
        _copy_ratings(conn, dataset.ratings)
        print(f"  ratings       {len(dataset.ratings):>6,}")
        _copy_ride_events(conn, dataset.ride_events)
        print(f"  ride_events   {len(dataset.ride_events):>6,}")
        conn.commit()
    print("Done.")


def load_large_batch(
    n_drivers:   int = 500,
    n_customers: int = 5_000,
    n_rides:     int = 2_500_000,
    chunk_size:  int = 10_000,
) -> None:
    """
    Generates and inserts data in chunks to keep memory bounded.
    Entity pools (drivers/customers/vehicles) are inserted once; rides and
    their dependents are generated and flushed chunk_size at a time.
    """
    from generators.entity_generators.customer_generator import CustomerGenerator
    from generators.entity_generators.driver_generator import DriverGenerator
    from generators.entity_generators.fare_generator import FareGenerator
    from generators.entity_generators.rating_generator import RatingGenerator
    from generators.entity_generators.ride_event_generator import RideEventGenerator
    from generators.entity_generators.ride_generator import RideGenerator
    from generators.entity_generators.vehicle_generator import VehicleGenerator

    print(
        f"Loading {n_drivers:,} drivers, {n_customers:,} customers, "
        f"{n_rides:,} rides (chunks of {chunk_size:,}) ..."
    )
    t0 = time.perf_counter()

    drivers   = DriverGenerator().generate_many(n_drivers)
    customers = CustomerGenerator().generate_many(n_customers)
    vehicles  = VehicleGenerator().generate_many([d.driver_id for d in drivers])

    driver_ids   = [d.driver_id   for d in drivers]
    customer_ids = [c.customer_id for c in customers]
    vehicle_ids  = [v.vehicle_id  for v in vehicles]

    ride_gen   = RideGenerator()
    fare_gen   = FareGenerator()
    rating_gen = RatingGenerator()
    event_gen  = RideEventGenerator()

    with get_conn() as conn:
        _copy_drivers(conn, drivers)
        _copy_customers(conn, customers)
        _copy_vehicles(conn, vehicles)
        conn.commit()
        print(
            f"  entities      drivers={len(drivers):,}  "
            f"customers={len(customers):,}  vehicles={len(vehicles):,}  "
            f"({time.perf_counter() - t0:.1f}s)"
        )
        del drivers, customers, vehicles

        rides_done   = 0
        total_events = 0
        while rides_done < n_rides:
            n = min(chunk_size, n_rides - rides_done)
            tc = time.perf_counter()

            rides = ride_gen.generate_many(driver_ids, customer_ids, vehicle_ids, n)
            completed = [r for r in rides if r.status == RideStatus.COMPLETED]

            fares = fare_gen.generate_many(
                [(r.ride_id, r.distance_km) for r in completed]
            )
            ratings = rating_gen.generate_many(
                [(r.ride_id, r.driver_id, r.customer_id) for r in completed]
            )
            ride_events: list[RideEvent] = []
            for r in completed:
                for e in event_gen.generate_for_ride(
                    ride_id=r.ride_id,
                    pickup_lat=r.pickup_latitude,
                    pickup_lon=r.pickup_longitude,
                    dropoff_lat=r.dropoff_latitude,
                    dropoff_lon=r.dropoff_longitude,
                    pickup_at=r.pickup_at,
                    dropoff_at=r.dropoff_at,
                ):
                    if e.event_type == RideEventType.STATUS_CHANGED:
                        ride_events.append(e)

            _copy_rides(conn, rides)
            _copy_fares(conn, fares)
            _copy_ratings(conn, ratings)
            _copy_ride_events(conn, ride_events)
            conn.commit()

            rides_done   += n
            total_events += len(ride_events)
            pct = rides_done / n_rides * 100
            print(
                f"  rides {rides_done:>10,}/{n_rides:,} ({pct:5.1f}%)  "
                f"events_this_chunk={len(ride_events):,}  "
                f"chunk={time.perf_counter() - tc:.1f}s  "
                f"elapsed={time.perf_counter() - t0:.0f}s"
            )

    print(f"Done. total_ride_events={total_events:,}  elapsed={time.perf_counter() - t0:.0f}s")


def load_cancelled_batch(n_rides: int = 250) -> None:
    """
    Generates exactly n_rides cancelled rides using existing drivers/customers/vehicles
    already in the database.  No new entities are inserted.
    """
    import random

    from generators.entity_generators.ride_generator import RideGenerator

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT driver_id FROM drivers;")
            driver_ids = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT customer_id FROM customers;")
            customer_ids = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT vehicle_id FROM vehicles;")
            vehicle_ids = [row[0] for row in cur.fetchall()]

    ride_gen  = RideGenerator()
    cancelled = []
    while len(cancelled) < n_rides:
        ride = ride_gen.generate(
            driver_id=random.choice(driver_ids),
            customer_id=random.choice(customer_ids),
            vehicle_id=random.choice(vehicle_ids),
        )
        if ride.status == RideStatus.CANCELLED:
            cancelled.append(ride)

    print(f"Loading {n_rides} cancelled rides using existing entities ...")
    with get_conn() as conn:
        _copy_rides(conn, cancelled)
        conn.commit()
    print(f"Done. {n_rides} cancelled rides inserted.")


if __name__ == "__main__":
    load_large_batch(
        n_drivers=500,
        n_customers=5_000,
        n_rides=2_500_000,
        chunk_size=10_000,
    )
