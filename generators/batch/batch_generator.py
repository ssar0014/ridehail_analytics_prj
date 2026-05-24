from dataclasses import dataclass
from datetime import datetime

from enums.ride_status import RideStatus
from models.customer_model import Customer
from models.driver_model import Driver
from models.fare_model import Fare
from models.rating_model import Rating
from models.ride_event_model import RideEvent
from models.ride_model import Ride
from models.vehicle_model import Vehicle

from generators.entity_generators.customer_generator import CustomerGenerator
from generators.entity_generators.driver_generator import DriverGenerator
from generators.entity_generators.fare_generator import FareGenerator
from generators.entity_generators.rating_generator import RatingGenerator
from generators.entity_generators.ride_event_generator import RideEventGenerator
from generators.entity_generators.ride_generator import RideGenerator
from generators.entity_generators.vehicle_generator import VehicleGenerator


@dataclass
class BatchDataset:
    drivers:     list[Driver]
    customers:   list[Customer]
    vehicles:    list[Vehicle]
    rides:       list[Ride]
    fares:       list[Fare]
    ratings:     list[Rating]
    ride_events: list[RideEvent]

    def summary(self) -> str:
        return (
            f"BatchDataset("
            f"drivers={len(self.drivers)}, "
            f"customers={len(self.customers)}, "
            f"vehicles={len(self.vehicles)}, "
            f"rides={len(self.rides)}, "
            f"fares={len(self.fares)}, "
            f"ratings={len(self.ratings)}, "
            f"ride_events={len(self.ride_events)})"
        )


class BatchGenerator:
    def __init__(
        self,
        n_drivers:   int = 50,
        n_customers: int = 200,
        n_rides:     int = 1000,
        start_date:  datetime | None = None,
        end_date:    datetime | None = None,
    ):
        self.n_drivers   = n_drivers
        self.n_customers = n_customers
        self.n_rides     = n_rides

        self._driver_gen     = DriverGenerator()
        self._customer_gen   = CustomerGenerator()
        self._vehicle_gen    = VehicleGenerator()
        self._ride_gen       = RideGenerator(start_date=start_date, end_date=end_date)
        self._fare_gen       = FareGenerator()
        self._rating_gen     = RatingGenerator()
        self._ride_event_gen = RideEventGenerator()

    def generate(self) -> BatchDataset:
        # Entity pools
        drivers   = self._driver_gen.generate_many(self.n_drivers)
        customers = self._customer_gen.generate_many(self.n_customers)
        vehicles  = self._vehicle_gen.generate_many([d.driver_id for d in drivers])

        driver_ids   = [d.driver_id   for d in drivers]
        customer_ids = [c.customer_id for c in customers]
        vehicle_ids  = [v.vehicle_id  for v in vehicles]

        # All rides (completed + cancelled)
        rides = self._ride_gen.generate_many(driver_ids, customer_ids, vehicle_ids, self.n_rides)
        completed = [r for r in rides if r.status == RideStatus.COMPLETED]

        # Fares and ratings only for completed rides
        fares = self._fare_gen.generate_many(
            [(r.ride_id, r.distance_km) for r in completed]
        )
        ratings = self._rating_gen.generate_many(
            [(r.ride_id, r.driver_id, r.customer_id) for r in completed]
        )

        # Ride events — full location stream per ride
        ride_events: list[RideEvent] = []
        for ride in rides:
            ride_events.extend(self._ride_event_gen.generate_for_ride(
                ride_id=ride.ride_id,
                pickup_lat=ride.pickup_latitude,
                pickup_lon=ride.pickup_longitude,
                dropoff_lat=ride.dropoff_latitude,
                dropoff_lon=ride.dropoff_longitude,
                pickup_at=ride.pickup_at,
                dropoff_at=ride.dropoff_at,
            ))

        return BatchDataset(
            drivers=drivers,
            customers=customers,
            vehicles=vehicles,
            rides=rides,
            fares=fares,
            ratings=ratings,
            ride_events=ride_events,
        )


if __name__ == "__main__":
    gen = BatchGenerator(n_drivers=10, n_customers=50, n_rides=100)
    dataset = gen.generate()
    print(dataset.summary())
    print("\nSample ride:")
    print(dataset.rides[0])
    print("\nSample fare:")
    print(dataset.fares[0])
    print("\nSample ratings:")
    print(dataset.ratings[0])
    print(dataset.ratings[1])
