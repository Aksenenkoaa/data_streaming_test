import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import (
    StreamTableEnvironment,
    EnvironmentSettings,
    DataTypes,
)

# Environment variables provide flexibility for docker-compose overrides
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PWD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB  = os.getenv("POSTGRES_DB", "streaming")

def build_pipeline(t_env: StreamTableEnvironment) -> None:
    """
    Define source, sink and transformation logic here.
    Replace all TODOs with working code.
    """
    # -----------------------------------------------------------------
    # 1) Source table over the Debezium topic (JSON without schemas)
    # -----------------------------------------------------------------
    t_env.execute_sql(f"""
        CREATE TABLE orders_cdc (
            `before` ROW<order_id STRING,
                          customer_id INT,
                          quantity INT,
                          price DOUBLE,
                          event_ts TIMESTAMP_LTZ(3)>,
            `after`  ROW<order_id STRING,
                          customer_id INT,
                          quantity INT,
                          price DOUBLE,
                          event_ts TIMESTAMP_LTZ(3)>,
            op STRING,
            ts_ms BIGINT,
            event_ts AS after.event_ts,
            WATERMARK FOR event_ts AS event_ts - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic'     = 'orders_cdc.public.orders',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP}',
            'scan.startup.mode' = 'earliest-offset',
            'format'    = 'json',
            'json.timestamp-format.standard' = 'ISO-8601'
        )
    """)

    # -----------------------------------------------------------------
    # 2) Sink table into Postgres via JDBC upsert
    # -----------------------------------------------------------------
    t_env.execute_sql(f"""
        CREATE TABLE order_agg (
            window_start TIMESTAMP(3),
            window_end   TIMESTAMP(3),
            customer_id  INT,
            gross_sales  DOUBLE,
            order_count  BIGINT,
            PRIMARY KEY (window_start, customer_id) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url'       = 'jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}',
            'table-name' = 'order_agg',
            'username'  = '{POSTGRES_USER}',
            'password'  = '{POSTGRES_PWD}',
            'sink.buffer-flush.max-rows' = '100',
            'sink.buffer-flush.interval' = '1s'
        )
    """)

    # -----------------------------------------------------------------
    # 3) Transform: unwrap Debezium envelope, aggregate
    # -----------------------------------------------------------------
    t_env.execute_sql("""
      INSERT INTO order_agg
      SELECT
        window_start,
        window_end,
        customer_id,
        SUM(quantity * price) AS gross_sales,
        COUNT(*)             AS order_count
      FROM TABLE(
          TUMBLE(
            SELECT
              after.order_id    AS order_id,
              after.customer_id AS customer_id,
              after.quantity    AS quantity,
              after.price       AS price,
              event_ts          AS ts
            FROM orders_cdc
            WHERE (op = 'c' OR op = 'u') 
              AND after IS NOT NULL
              AND after.order_id IS NOT NULL
              AND after.customer_id IS NOT NULL
              AND after.quantity IS NOT NULL
              AND after.price IS NOT NULL
              AND after.event_ts IS NOT NULL
          , DESCRIPTOR(ts), INTERVAL '1' MINUTE))
      GROUP BY window_start, window_end, customer_id
    """)


def main() -> None:
    settings = EnvironmentSettings.in_streaming_mode()
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    build_pipeline(t_env)


if __name__ == "__main__":
    main()
