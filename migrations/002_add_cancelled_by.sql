ALTER TABLE rides
    ADD COLUMN IF NOT EXISTS cancelled_by VARCHAR(20)
        CHECK (cancelled_by IN ('driver', 'customer', 'admin'));
