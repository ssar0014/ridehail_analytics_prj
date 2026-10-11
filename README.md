# ridehail-analytics

An end-to-end data engineering and analytics project simulating a ridehail service (Uber/Lyft-style). The project covers data modelling, simulation, batch and real-time pipelines, and analytics.

---

## Project Goals

1. **Simulate** a ridehail service with realistic entities — drivers, customers, vehicles, rides, fares, ratings, and real-time ride events
2. **Generate** data in two modes — batch (historical records) and real-time (streaming ride events)
3. **Pipeline** the data through two paths:
   - **Batch**: Postgres → Airflow → dbt → ClickHouse → historical analytics
   - **Real-time**: Kafka → Flink → ClickHouse → real-time analytics
4. **Host** the full stack on Docker

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14 |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| OLTP / source of truth | Postgres |
| Analytical warehouse (OLAP) | ClickHouse |
| Batch orchestration | Airflow + dbt |
| Real-time streaming | Kafka + Flink |
| Web app backend | FastAPI (JWT auth, async psycopg pool, clickhouse-connect) |
| Web app frontend | React + TypeScript (Vite) |
| Infrastructure | Docker |

### Architecture overview

```
┌─────────────┐
│   Postgres  │  OLTP — writes, FK integrity, source of truth
└──────┬──────┘
       │
 ┌─────┴──────────────────────┐
 │                            │
 │ Batch path                 │ Real-time path
 │                            │
 Airflow                    Kafka
 (export)                     │
 │                          Flink
 │                  (enrich, join, window)
 └─────────┬──────────────────┘
           │
    ┌──────▼──────┐
    │ ClickHouse  │  OLAP — analytical reads, dashboards
    └──────┬──────┘
           │
          dbt
           │
     FastAPI  ◄──── also reads Postgres (accounts, per-user views)
           │
   React web app  (admin / driver / rider views)
```

**Why two databases?** Postgres is optimised for transactional writes with strong consistency and FK constraints. ClickHouse is a columnar store optimised for analytical reads — aggregations over millions of rows that would be slow in Postgres run in milliseconds. Flink sits between Kafka and ClickHouse to enrich and transform events in-flight before they land; ClickHouse's native Kafka engine can be used for simple ingestion without Flink where no transformation is needed.

---

## Project Structure

```
ridehail_analytics/
├── enums/                          # StrEnum/IntEnum definitions
│   ├── cancelled_by.py             # CancelledBy (driver / customer / admin)
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
│   │   ├── ride_generator.py       # 8% cancellation rate; cancelled_by weighted by actor
│   │   ├── fare_generator.py
│   │   ├── rating_generator.py
│   │   └── ride_event_generator.py
│   ├── batch/
│   │   └── batch_generator.py      # Orchestrates all entity generators; produces BatchDataset
│   └── real_time/
│       └── real_time_generator.py  # Heap-based concurrent ride simulator; yields StreamPayload
├── migrations/                     # Ordered SQL migration files
│   ├── 001_create_schema.sql       # Full OLTP schema (all 7 tables + indexes)
│   ├── 002_add_cancelled_by.sql    # ALTER TABLE rides ADD COLUMN cancelled_by
│   └── 003_create_app_users.sql    # Web-app login accounts (admin / driver / customer)
├── db/
│   ├── connection.py               # get_conn() — psycopg3 connection from env
│   ├── migrate.py                  # Migration runner (--reset to wipe and reapply)
│   └── batch_loader.py             # Bulk-loads BatchDataset via COPY; chunked large-batch loader
├── api/                            # FastAPI backend
│   ├── main.py                     # App, lifespan (DB pools), router wiring
│   ├── config.py                   # Settings from env / .env
│   ├── db.py                       # Postgres pool + lazy ClickHouse client, FastAPI deps
│   ├── security.py                 # Password hashing, JWT, role guards
│   ├── schemas.py                  # Pydantic response models
│   ├── queries.py                  # Shared ride/rating queries
│   ├── users.py                    # CLI: create accounts, seed demo users
│   ├── routers/                    # health, auth, admin, driver, customer
│   └── Dockerfile                  # API image (build context: repo root)
├── frontend/                       # React + TS web app (Vite)
│   ├── src/
│   │   ├── api/                    # fetch client, useApi hook, response types
│   │   ├── auth/                   # AuthContext, RequireRole guard, role routes
│   │   ├── components/             # Layout, StatCard, RideTable
│   │   └── pages/                  # Login, AdminHome, DriverHome, CustomerHome
│   ├── Dockerfile                  # Node build → nginx image
│   └── nginx.conf                  # Static files + /api proxy + SPA fallback
├── ui/
│   └── ride_visualizer.py          # Streamlit live map (legacy — to be ported into frontend/)
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
| `Ride` | `ride_id`, `driver_id`*, `customer_id`*, `vehicle_id`*, `status`, pickup/dropoff lat+lon+address, lifecycle timestamps, `distance_km`, `duration_minutes`, `cancelled_by` | Status follows a defined lifecycle (see below); dropoff fields are nullable for cancelled rides |
| `Fare` | `fare_id`, `ride_id`*, `base_fare`, `distance_fare`, `surge_multiplier`, `surge_amount`, `tip`, `taxes`, `total` | `surge_amount` and `total` are computed in `__post_init__` |
| `Rating` | `rating_id`, `ride_id`*, `rated_entity_id`*, `rated_entity_type`, `rated_by_id`*, `score`, `comment` | One model covers both driver and customer ratings; score validated 1.0–5.0 |
| `RideEvent` | `event_id`, `ride_id`*, `event_type`, `latitude`, `longitude`, `occurred_at` | High-frequency events fed to the real-time pipeline |

\* Required field — must be provided at construction time.

### Ride Status Lifecycle

```
REQUESTED → ACCEPTED → EN_ROUTE_TO_PICKUP → ARRIVED_AT_PICKUP → IN_PROGRESS → COMPLETED
    │            │                                                                  
    └────────────┴──────────────────────────────────────────────────────────────> CANCELLED
                                                                 (cancelled_by: driver | customer | admin)
```

The batch generator models the end state only (COMPLETED or CANCELLED). The real-time pipeline will emit state-transition events at each stage, starting from REQUESTED.

### Star Schema (Data Warehouse)

The OLTP models above feed a star schema in the warehouse:

- **Fact**: `fact_rides` — one row per completed ride with all fare measures and rating scores
- **Dimensions**: `dim_driver`, `dim_customer`, `dim_vehicle`, `dim_location` (role-played for pickup and dropoff), `dim_date`, `dim_time`

`RideEvent` bypasses the warehouse and feeds the Kafka real-time pipeline directly.

---

## Web App

A FastAPI backend (`api/`) and a React frontend (`frontend/`). Everyone signs in on the same page; each account has a role (`admin`, `driver` or `customer`) and lands on that role's view. Driver and customer accounts link to their row in `drivers` / `customers`.

**Run everything in Docker** (what a deployment runs):

```bash
cp .env.example .env                                   # then set JWT_SECRET
docker compose up -d --build                           # migrations run automatically
docker compose run --rm api python -m api.users demo   # optional demo accounts, password "ridehail"
open http://localhost:8080                             # API docs at /api/docs
```

**Or run the API and frontend on the host** for hot reload while developing:

```bash
docker compose up -d postgres clickhouse
uv run python -m db.migrate                # creates app_users
uv run python -m api.users demo            # demo accounts, password "ridehail"

uv run uvicorn api.main:app --reload       # API on :8000 (docs at /api/docs)
cd frontend && npm install && npm run dev  # web app on :5173 (proxies /api → :8000)
```

| Demo account | Role | Lands on |
|---|---|---|
| `admin@ridehail.dev` | admin | `/admin` — platform totals, rides by status |
| `driver@ridehail.dev` | driver | `/driver` — earnings, rating, vehicle, recent rides |
| `customer@ridehail.dev` | customer | `/customer` — spend, rating, recent rides |

Create real accounts with `uv run python -m api.users create --email … --role driver --driver-id <uuid>` (prompts for a password).

**API**

| Endpoint | Access | |
|---|---|---|
| `GET /api/health` | public | Postgres + ClickHouse connectivity |
| `POST /api/auth/login` | public | OAuth2 password form → JWT bearer token |
| `GET /api/auth/me` | any role | Current account |
| `GET /api/admin/overview` | admin | Platform totals |
| `GET /api/driver/me` | driver | Driver dashboard |
| `GET /api/customer/me` | customer | Customer dashboard |

Auth is a stateless JWT (HS256), checked against `app_users` on every request so deactivating an account takes effect immediately. Set `JWT_SECRET` (see `.env.example`) for anything beyond local dev. The API starts even if ClickHouse is down; `/api/health` reports it as degraded.

## Live Map (legacy Streamlit preview)

`ui/ride_visualizer.py` is a Streamlit + PyDeck app that visualises the real-time generator on a dark map of San Francisco. It shows active vehicle positions (green dots) and their route trails (blue paths), refreshing every 2 seconds.

```bash
uv run streamlit run ui/ride_visualizer.py
```

> **Note:** superseded by the web app above; the live map will be ported into the admin view and this script removed.

---

## Infrastructure

`docker compose up -d` starts the whole stack. All settings come from `.env` (copy `.env.example`); Compose refuses to start until `JWT_SECRET` is set.

| Service | Image | Host port | Notes |
|---|---|---|---|
| `postgres` | `postgres:16` | `127.0.0.1:5432` | OLTP database |
| `clickhouse` | `clickhouse/clickhouse-server:25.8` | `127.0.0.1:8123` (HTTP), `127.0.0.1:9000` (native) | OLAP warehouse |
| `migrate` | `ridehail-api` (`api/Dockerfile`) | — | One-shot: applies pending migrations, then exits; `api` waits for it |
| `api` | `ridehail-api` (`api/Dockerfile`) | — (internal `:8000`) | FastAPI; only reachable through `web` |
| `web` | `ridehail-web` (`frontend/Dockerfile`) | `${WEB_PORT:-8080}` | nginx: serves the built React app and proxies `/api` → `api` |
| `pgadmin` | `dpage/pgadmin4` | `127.0.0.1:5050` | **`dev` profile only** — not started by a plain `up` |

```bash
docker compose up -d --build              # build images and start the stack
docker compose --profile dev up -d        # …plus pgAdmin (admin@ridehail.dev / admin)
docker compose logs -f api                # tail API logs
docker compose run --rm api python -m db.migrate   # re-run migrations by hand
```

Database ports are bound to `127.0.0.1`, so host tools (batch loader, dev API, DB clients) can use them while they stay closed to the network on a server; only the web app's port is public. Database credentials default to `ridehail` / `ridehail` and can be overridden in `.env` (they only take effect when a data volume is first created). Inside Compose the API reaches the databases by service name; on the host, scripts use `DATABASE_URL` (default `postgresql://ridehail:ridehail@localhost:5432/ridehail_db`).

---

## Database

### Migrations

```bash
# Apply any pending migrations
uv run python -m db.migrate

# Wipe schema and reapply all migrations from scratch (dev only)
uv run python -m db.migrate --reset
```

Migrations are plain `.sql` files in `migrations/`, applied in filename order and tracked in a `schema_migrations` table.

### Loading historical data

```bash
# Load 2.5M rides (500 drivers, 5 000 customers) — chunked to keep memory bounded
uv run python -m db.batch_loader

# Append cancelled rides using entities already in the database
uv run python -c "from db.batch_loader import load_cancelled_batch; load_cancelled_batch()"
```

`load_large_batch()` uses psycopg3's `COPY … FROM STDIN` protocol for high-throughput inserts, processing 10 000 rides per chunk. Only `STATUS_CHANGED` ride events (ride start and end) are stored in Postgres; full location streams belong in the Kafka real-time pipeline.

**Batch data characteristics:**
- ~8% of rides are cancelled (weighted: 55% customer, 35% driver, 10% admin)
- Fares and ratings are generated only for completed rides
- Each completed ride produces two ride events (STATUS_CHANGED at pickup and dropoff)

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

# Run the API (http://localhost:8000/api/docs)
uv run uvicorn api.main:app --reload

# Run the web app (http://localhost:5173)
cd frontend && npm run dev

# Frontend type-check + build / lint
cd frontend && npm run build
cd frontend && npm run lint

# Launch the legacy Streamlit live map
uv run streamlit run ui/ride_visualizer.py

# Add a dependency
uv add <package>
```

---

## Roadmap

- [x] OLTP data models
- [x] Batch data generator (completed + cancelled rides, fares, ratings, ride events)
- [x] Real-time data generator
- [x] Live map visualiser (dev preview)
- [x] Postgres schema + migrations
- [x] Docker Compose setup (Postgres + pgAdmin)
- [x] Dockerised API + web app — full stack via `docker compose up -d`
- [x] Bulk historical data load — via psycopg3 COPY
- [ ] Kafka producer
- [ ] Flink jobs
- [x] ClickHouse Docker service
- [x] Web app scaffold — FastAPI backend, React frontend, role-based logins (admin / driver / customer)
- [ ] Port live map into the web app; retire Streamlit
- [ ] ClickHouse schema
- [ ] Airflow DAGs (Postgres → ClickHouse export)
- [ ] dbt models (targeting ClickHouse)
- [ ] Surge zones table + admin controls
- [ ] Build out role views (admin live parameter controls, driver telemetry, rider trip tracking)
- [ ] Hosting
