# Streaming Pipeline Coding Challenge

This project to build a real-time data streaming pipeline using **PyFlink**, **Kafka**, **Debezium**, and **PostgreSQL**.

## 🚀 Quick Start

You can run it ./start_pipeline.sh or execute individual commands step by step, as described below.

### Step 1: Start the Infrastructure
```bash
# Start all services (first build takes ~5 minutes)
docker compose up -d --build

# Wait for services to initialize (~30 seconds)
sleep 30

# Register the Debezium connector
cd debezium && ./register_connector.sh && cd ..
```

### Step 2: Verify the Pipeline is Working
```bash
# Check that CDC data is flowing from PostgreSQL → Kafka
docker exec sp_kafka /bin/kafka-console-consumer --bootstrap-server localhost:9092 --topic orders_cdc.public.orders --max-messages 5

# Check data generation (should show increasing count)
docker exec sp_postgres psql -U postgres -d streaming -c "SELECT COUNT(*) FROM orders;"
```

## 🎯 Functionality

1. **Parsed Debezium CDC events** from the `orders_cdc.public.orders` Kafka topic
2. **Extracted order data** from the Debezium envelope (`after` field for inserts/updates)
3. **Implemented 1-minute tumbling window aggregations** per `customer_id`:
   - `gross_sales` = SUM(quantity × price)
   - `order_count` = COUNT(*)
4. **Wrote results** to the `order_agg` PostgreSQL table

### Test
```bash
# Submit
docker exec sp_jobmanager flink run -py /opt/flink_jobs/stream_job.py

# Check job status (should show RUNNING)
curl http://localhost:8081/jobs

# Verify results (wait ~2 minutes for data to accumulate)
docker exec sp_postgres psql -U postgres -d streaming -c "SELECT * FROM order_agg ORDER BY gross_sales DESC LIMIT 10;"
```

## 🧪 Run the Test

```bash
pytest tests/test_job.py -v
```

The test validates that streaming job:
- Consumes CDC events from Kafka
- Performs windowed aggregations
- Writes results to PostgreSQL

## 📊 Architecture

```
PostgreSQL → Debezium → Kafka → PyFlink → PostgreSQL
  (orders)              (CDC)  (aggregation)  (order_agg)
```

## 🛠️ Services Overview

- **sp_postgres**: Source database with `orders` table + target `order_agg` table
- **sp_kafka**: Message broker for CDC events
- **sp_connect**: Debezium connector for Change Data Capture
- **sp_jobmanager/sp_taskmanager**: Flink cluster with PyFlink support
- **sp_datagen**: Generates realistic order data continuously

## Info

- Use Flink Web UI at http://localhost:8081 to monitor jobs
- Use Kafka Connect API at http://localhost:8083 to check connector status
- Check container logs: `docker logs sp_jobmanager` or `docker logs sp_connect`
- The data generator creates ~100 orders/minute across 100 customers
