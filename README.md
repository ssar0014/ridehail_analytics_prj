# ridehail-analytics

An end-to-end data engineering and analytics project simulating a ridehail service (Uber/Lyft-style). The project covers data modelling, simulation, batch and real-time pipelines, and analytics.

---

## Project Goals

1. **Simulate** a ridehail service with realistic entities — drivers, customers, vehicles, rides, fares, ratings, and real-time ride events
2. **Generate** data in two modes — batch (historical records) and real-time (streaming ride events)
3. **Pipeline** the data through two paths:
   - **Batch**: Postgres → Airflow → dbt → historical analytics
   - **Real-time**: Kafka → Flink → real-time analytics
4. **Host** the full stack on Docker

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14 |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Batch warehouse | Postgres / Snowflake |
| Batch orchestration | Airflow + dbt |
| Real-time streaming | Kafka + Flink |
| Infrastructure | Docker |

---

## Project Structure

```
ridehail_analytics/
├── enums/                  # StrEnum/IntEnum definitions
│   ├── customer_status.py  # CustomerStatus, CustomerTier
│   ├── driver_status.py    # DriverStatus
│   ├── rated_entity_type.py# RatedEntityType
│   ├── ride_event_type.py  # RideEventType
│   ├── ride_status.py      # RideStatus
│   ├── vehicle_status.py   # VehicleStatus
│   └── vehicle_type.py     # VehicleType
├── models/                 # OLTP data models (Python dataclasses)
│   ├── driver_model.py     # Driver
│   ├── customer_model.py   # Customer
│   ├── vehicle_model.py    # Vehicle
│   ├── ride_model.py       # Ride
│   ├── fare_model.py       # Fare
│   ├── rating_model.py     # Rating
│   └── ride_event_model.py # RideEvent
└── main.py
```

---

## Data Models

All models are Python `@dataclass` classes representing the OLTP layer. They map directly to Postgres tables and serve as the schema for Kafka event payloads.

### Entity Relationships

```
Driver  ──< Vehicle
Driver  ──< Ride >── Customer
               │
               ├──── Fare        (1:1)
               ├──── Rating      (1:many, one per direction: driver + customer)
               └──── RideEvent   (1:many, real-time location/status stream)
```

### Models

| Model | Key Fields | Notes |
|---|---|---|
| `Driver` | `driver_id`, `first_name`, `last_name`, `phone_number`, `email`, `license_number`, `status`, `current_latitude`, `current_longitude` | Status via `DriverStatus` enum |
| `Customer` | `customer_id`, `first_name`, `last_name`, `phone_number`, `email`, `payment_token`, `is_active`, `is_premium_member` | `payment_token` is an opaque ref — raw card data is never stored |
| `Vehicle` | `vehicle_id`, `driver_id`*, `make`, `model`, `year`, `color`, `plate`, `vehicle_type`, `status` | `driver_id` is required — a vehicle cannot exist without a driver |
| `Ride` | `ride_id`, `driver_id`*, `customer_id`*, `vehicle_id`*, `status`, pickup/dropoff lat+lon+address, lifecycle timestamps, `distance_km`, `duration_minutes` | Status follows a defined lifecycle (see below) |
| `Fare` | `fare_id`, `ride_id`*, `base_fare`, `distance_fare`, `surge_multiplier`, `surge_amount`, `tip`, `taxes`, `total` | `surge_amount` and `total` are computed in `__post_init__` |
| `Rating` | `rating_id`, `ride_id`*, `rated_entity_id`*, `rated_entity_type`, `rated_by_id`*, `score`, `comment` | One model covers both driver and customer ratings; score validated 1.0–5.0 |
| `RideEvent` | `event_id`, `ride_id`*, `event_type`, `latitude`, `longitude`, `occurred_at` | High-frequency events fed to the real-time pipeline |

\* Required field — must be provided at construction time.

### Ride Status Lifecycle

```
REQUESTED → ACCEPTED → EN_ROUTE_TO_PICKUP → ARRIVED_AT_PICKUP → IN_PROGRESS → COMPLETED
                                                                             → CANCELLED
```

### Star Schema (Data Warehouse)

The OLTP models above feed a star schema in the warehouse:

- **Fact**: `fact_rides` — one row per completed ride with all fare measures and rating scores
- **Dimensions**: `dim_driver`, `dim_customer`, `dim_vehicle`, `dim_location` (role-played for pickup and dropoff), `dim_date`, `dim_time`

`RideEvent` bypasses the warehouse and feeds the Kafka real-time pipeline directly.

---

## Commands

```bash
# Install dependencies and sync virtualenv
uv sync

# Run the project
uv run python main.py

# Add a dependency
uv add <package>

# Run a script or tool
uv run <command>
```

---

## Roadmap

- [x] OLTP data models
- [ ] Batch data generator
- [ ] Real-time data generator
- [ ] Postgres schema + migrations
- [ ] Kafka producer
- [ ] Airflow DAGs
- [ ] dbt models
- [ ] Flink jobs
- [ ] Docker Compose setup
- [ ] Hosting
