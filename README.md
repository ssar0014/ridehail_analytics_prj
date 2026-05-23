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
├── enums/                          # StrEnum/IntEnum definitions
│   ├── customer_status.py          # CustomerStatus, CustomerTier
│   ├── driver_status.py            # DriverStatus
│   ├── rated_entity_type.py        # RatedEntityType
│   ├── ride_event_type.py          # RideEventType
│   ├── ride_status.py              # RideStatus
│   ├── vehicle_status.py           # VehicleStatus
│   └── vehicle_type.py             # VehicleType
├── models/                         # OLTP data models (Python dataclasses)
│   ├── driver_model.py             # Driver
│   ├── customer_model.py           # Customer
│   ├── vehicle_model.py            # Vehicle
│   ├── ride_model.py               # Ride
│   ├── fare_model.py               # Fare
│   ├── rating_model.py             # Rating
│   └── ride_event_model.py         # RideEvent
├── generators/
│   ├── entity_generators/          # Per-entity generators (Faker-based)
│   │   ├── driver_generator.py
│   │   ├── customer_generator.py
│   │   ├── vehicle_generator.py
│   │   ├── ride_generator.py
│   │   ├── fare_generator.py
│   │   ├── rating_generator.py
│   │   └── ride_event_generator.py
│   ├── batch/
│   │   └── batch_generator.py      # Orchestrates all entity generators; produces BatchDataset
│   └── real_time/
│       └── real_time_generator.py  # Heap-based concurrent ride simulator; yields StreamPayload
├── ui/
│   └── ride_visualizer.py          # Streamlit + PyDeck live map (dev preview)
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

## Live Map (dev preview)

`ui/ride_visualizer.py` is a Streamlit + PyDeck app that visualises the real-time generator on a dark map of San Francisco. It shows active vehicle positions (green dots) and their route trails (blue paths), refreshing every 2 seconds.

```bash
uv run streamlit run ui/ride_visualizer.py
```

> **Note:** this is a development preview only. It will be replaced by a full admin console (with driver/customer telemetry panels and live parameter controls) once the Kafka + Flink pipeline is in place.

---

## Commands

```bash
# Install dependencies and sync virtualenv
uv sync

# Run the project entry point
uv run python main.py

# Run the batch generator smoke test
uv run python generators/batch/batch_generator.py

# Run the real-time generator smoke test (Ctrl+C to stop)
uv run python generators/real_time/real_time_generator.py

# Launch the live map visualiser
uv run streamlit run ui/ride_visualizer.py

# Add a dependency
uv add <package>
```

---

## Roadmap

- [x] OLTP data models
- [x] Batch data generator
- [x] Real-time data generator
- [x] Live map visualiser (dev preview)
- [ ] Postgres schema + migrations
- [ ] Docker Compose setup
- [ ] Kafka producer
- [ ] Flink jobs
- [ ] Airflow DAGs
- [ ] dbt models
- [ ] Admin console (driver/customer panels, live parameter controls)
- [ ] Hosting
