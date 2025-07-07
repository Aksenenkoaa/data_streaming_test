import os, random, time, uuid, psycopg2

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "dbname=streaming user=postgres password=postgres host=sp_postgres port=5432"
)

def wait_for_postgres() -> bool:
    """Wait for PostgreSQL to be ready"""
    max_retries = 30
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(POSTGRES_DSN)
            conn.close()
            print("PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError as e:
            print(f"Attempt {attempt + 1}/{max_retries}: PostgreSQL not ready yet: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print("Failed to connect to PostgreSQL after all retries")
                return False
    return False

def main() -> None:
    # Wait for PostgreSQL to be ready
    if not wait_for_postgres():
        return

    conn = psycopg2.connect(POSTGRES_DSN)
    conn.autocommit = True
    cur = conn.cursor()
    print("Starting data generation...")

    while True:
        order_id = uuid.uuid4().hex[:24]
        customer_id = random.randint(1, 100)
        quantity = random.randint(1, 5)
        price = round(random.uniform(10, 500), 2)

        cur.execute(
            """INSERT INTO orders (order_id, customer_id, quantity, price, event_ts)
                   VALUES (%s, %s, %s, %s, NOW())""",
            (order_id, customer_id, quantity, price)
        )
        time.sleep(0.001)  # ~1000 rows / sec

if __name__ == "__main__":
    main()
