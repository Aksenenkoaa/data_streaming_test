import os, time, psycopg2, pytest
from decimal import Decimal

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "dbname=streaming user=postgres password=postgres host=localhost port=5432"
)

@pytest.mark.timeout(180)
def test_pipeline_populates_order_agg() -> None:
    time.sleep(30)  # give the pipeline some time to ingest & aggregate

    conn = psycopg2.connect(POSTGRES_DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM order_agg;")
        agg_rows = cur.fetchone()[0]

    assert agg_rows > 0, (
        "order_agg table is still empty – make sure your connector, "
        "Flink job and generator are all running."
    )

def test_orders_table_exists() -> None:
    conn = psycopg2.connect(POSTGRES_DSN)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'orders'
            );
        """)
        exists = cur.fetchone()[0]
    assert exists, "orders table does not exist"


def test_order_agg_table_exists() -> None:
    conn = psycopg2.connect(POSTGRES_DSN)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'order_agg'
            );
        """)
        exists = cur.fetchone()[0]
    assert exists, "order_agg table does not exist"


def test_orders_have_data() -> None:
    conn = psycopg2.connect(POSTGRES_DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM orders;")
        count = cur.fetchone()[0]
    assert count > 0, "orders table is empty"


def test_order_agg_have_data() -> None:
    conn = psycopg2.connect(POSTGRES_DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM order_agg;")
        count = cur.fetchone()[0]
    assert count > 0, "order_agg table is empty"


def test_order_agg_columns() -> None:
    conn = psycopg2.connect(POSTGRES_DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'order_agg';")
        columns = {row[0] for row in cur.fetchall()}
    expected = {'window_start', 'window_end', 'customer_id', 'gross_sales', 'order_count'}
    assert expected.issubset(columns), f"order_agg columns missing: {expected - columns}"


def test_orders_columns() -> None:
    conn = psycopg2.connect(POSTGRES_DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'orders';")
        columns = {row[0] for row in cur.fetchall()}
    expected = {'order_id', 'customer_id', 'quantity', 'price', 'event_ts'}
    assert expected.issubset(columns), f"orders columns missing: {expected - columns}"


def test_order_agg_gross_sales_vs_orders() -> None:
    conn = psycopg2.connect(POSTGRES_DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(quantity * price), 0) FROM orders;")
        total_gross = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(gross_sales), 0) FROM order_agg;")
        agg_gross = cur.fetchone()[0]
    assert agg_gross <= total_gross + Decimal("0.01"), f"Aggregated gross_sales ({agg_gross}) > total orders gross ({total_gross})"
