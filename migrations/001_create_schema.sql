-- ── drivers ───────────────────────────────────────────────────────────────────
CREATE TABLE drivers (
    driver_id         UUID          PRIMARY KEY,
    first_name        VARCHAR(100)  NOT NULL,
    last_name         VARCHAR(100)  NOT NULL,
    phone_number      VARCHAR(30),
    email             VARCHAR(255)  UNIQUE,
    license_number    VARCHAR(50)   UNIQUE,
    status            VARCHAR(20)   NOT NULL,
    current_latitude  DOUBLE PRECISION,
    current_longitude DOUBLE PRECISION,
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ── customers ─────────────────────────────────────────────────────────────────
CREATE TABLE customers (
    customer_id    UUID         PRIMARY KEY,
    first_name     VARCHAR(100) NOT NULL,
    last_name      VARCHAR(100) NOT NULL,
    phone_number   VARCHAR(30),
    email          VARCHAR(255) UNIQUE,
    payment_token  VARCHAR(255),
    status         VARCHAR(20)  NOT NULL DEFAULT 'active',
    tier           SMALLINT     NOT NULL DEFAULT 1,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── vehicles ──────────────────────────────────────────────────────────────────
CREATE TABLE vehicles (
    vehicle_id   UUID         PRIMARY KEY,
    driver_id    UUID         NOT NULL REFERENCES drivers(driver_id),
    make         VARCHAR(100),
    model        VARCHAR(100),
    year         SMALLINT,
    color        VARCHAR(50),
    plate        VARCHAR(20)  UNIQUE,
    vehicle_type VARCHAR(20)  NOT NULL,
    status       VARCHAR(20)  NOT NULL DEFAULT 'active',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── rides ─────────────────────────────────────────────────────────────────────
CREATE TABLE rides (
    ride_id           UUID          PRIMARY KEY,
    driver_id         UUID          NOT NULL REFERENCES drivers(driver_id),
    customer_id       UUID          NOT NULL REFERENCES customers(customer_id),
    vehicle_id        UUID          NOT NULL REFERENCES vehicles(vehicle_id),
    status            VARCHAR(30)   NOT NULL,
    pickup_latitude   DOUBLE PRECISION,
    pickup_longitude  DOUBLE PRECISION,
    pickup_address    TEXT,
    dropoff_latitude  DOUBLE PRECISION,
    dropoff_longitude DOUBLE PRECISION,
    dropoff_address   TEXT,
    requested_at      TIMESTAMPTZ,
    accepted_at       TIMESTAMPTZ,
    pickup_at         TIMESTAMPTZ,
    dropoff_at        TIMESTAMPTZ,
    distance_km       NUMERIC(8, 2),
    duration_minutes  NUMERIC(8, 1),
    cancelled_by      VARCHAR(20)   CHECK (cancelled_by IN ('driver', 'customer', 'admin')),
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rides_driver_id   ON rides(driver_id);
CREATE INDEX idx_rides_customer_id ON rides(customer_id);
CREATE INDEX idx_rides_status      ON rides(status);
CREATE INDEX idx_rides_requested_at ON rides(requested_at);

-- ── fares ─────────────────────────────────────────────────────────────────────
CREATE TABLE fares (
    fare_id          UUID         PRIMARY KEY,
    ride_id          UUID         NOT NULL UNIQUE REFERENCES rides(ride_id),
    base_fare        NUMERIC(8,2) NOT NULL,
    distance_fare    NUMERIC(8,2) NOT NULL,
    surge_multiplier NUMERIC(4,2) NOT NULL DEFAULT 1.0,
    surge_amount     NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    tip              NUMERIC(8,2) NOT NULL DEFAULT 0.0,
    taxes            NUMERIC(8,2) NOT NULL,
    total            NUMERIC(8,2) NOT NULL,
    currency         VARCHAR(10)  NOT NULL DEFAULT 'USD',
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── ratings ───────────────────────────────────────────────────────────────────
CREATE TABLE ratings (
    rating_id        UUID         PRIMARY KEY,
    ride_id          UUID         NOT NULL REFERENCES rides(ride_id),
    rated_entity_id  UUID         NOT NULL,
    rated_entity_type VARCHAR(10) NOT NULL CHECK (rated_entity_type IN ('driver', 'customer')),
    rated_by_id      UUID         NOT NULL,
    score            NUMERIC(2,1) NOT NULL CHECK (score BETWEEN 1.0 AND 5.0),
    comment          TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ratings_ride_id        ON ratings(ride_id);
CREATE INDEX idx_ratings_rated_entity_id ON ratings(rated_entity_id);

-- ── ride_events ───────────────────────────────────────────────────────────────
CREATE TABLE ride_events (
    event_id    UUID         PRIMARY KEY,
    ride_id     UUID         NOT NULL REFERENCES rides(ride_id),
    event_type  VARCHAR(30)  NOT NULL,
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL,
    occurred_at TIMESTAMPTZ  NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ride_events_ride_id     ON ride_events(ride_id);
CREATE INDEX idx_ride_events_occurred_at ON ride_events(occurred_at);
