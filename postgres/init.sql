-- Base tables for the streaming pipeline challenge

CREATE TABLE IF NOT EXISTS public.orders (
    order_id       TEXT PRIMARY KEY,
    customer_id    INT          NOT NULL,
    quantity       INT          NOT NULL,
    price          NUMERIC(12,2) NOT NULL,
    event_ts       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.order_agg (
    window_start   TIMESTAMPTZ,
    window_end     TIMESTAMPTZ,
    customer_id    INT,
    gross_sales    NUMERIC(18,2),
    order_count    INT,
    PRIMARY KEY (window_start, customer_id)
);
