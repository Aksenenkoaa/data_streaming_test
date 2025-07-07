"""Very small integration smoke‑test.

It simply checks that the `order_agg` table receives rows after the
pipeline has been running for a short while.  You are free to add more
assertions, but **do not delete the existing one**.
"""

import os, time, psycopg2, pytest

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "dbname=streaming user=postgres password=postgres host=localhost port=5432"
)

@pytest.mark.timeout(180)
def test_pipeline_populates_order_agg():
    time.sleep(30)  # give the pipeline some time to ingest & aggregate

    conn = psycopg2.connect(POSTGRES_DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM order_agg;")
        agg_rows = cur.fetchone()[0]

    assert agg_rows > 0, (
        "order_agg table is still empty – make sure your connector, "
        "Flink job and generator are all running."
    )
