-- ── app_users ─────────────────────────────────────────────────────────────────
-- Login accounts for the web app. Drivers and customers link back to their
-- domain row; admins have no domain link.
CREATE TABLE app_users (
    user_id       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT         NOT NULL,
    role          VARCHAR(20)  NOT NULL CHECK (role IN ('admin', 'customer', 'driver')),
    driver_id     UUID         UNIQUE REFERENCES drivers(driver_id),
    customer_id   UUID         UNIQUE REFERENCES customers(customer_id),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT app_users_role_link CHECK (
        (role = 'admin'    AND driver_id IS NULL     AND customer_id IS NULL) OR
        (role = 'driver'   AND driver_id IS NOT NULL AND customer_id IS NULL) OR
        (role = 'customer' AND driver_id IS NULL     AND customer_id IS NOT NULL)
    )
);
