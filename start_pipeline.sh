#!/bin/bash

# Streaming Pipeline Auto-Start Script
# This script starts all services in the correct order and waits for them to be ready

set -e  # Exit on any error

echo "🚀 Starting Streaming Pipeline..."

# Step 1: Start all services
echo "📦 Starting all Docker services..."
docker compose up -d --build

# Step 2: Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker compose exec -T postgres pg_isready -U postgres -d streaming; do
    echo "PostgreSQL not ready yet, waiting..."
    sleep 5
done
echo "✅ PostgreSQL is ready!"

# Step 3: Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to be ready..."
until docker compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; do
    echo "Kafka not ready yet, waiting..."
    sleep 5
done
echo "✅ Kafka is ready!"

# Step 4: Wait for Kafka Connect to be ready
echo "⏳ Waiting for Kafka Connect to be ready..."
until curl -s http://localhost:8083/connectors > /dev/null; do
    echo "Kafka Connect not ready yet, waiting..."
    sleep 5
done
echo "✅ Kafka Connect is ready!"

# Step 5: Register Debezium connector
echo "🔌 Registering Debezium connector..."
cd debezium && bash ./register_connector.sh && cd ..
echo "✅ Debezium connector registered!"

# Step 6: Wait for Flink JobManager to be ready
echo "⏳ Waiting for Flink JobManager to be ready..."
until curl -s http://localhost:8081/jobs > /dev/null; do
    echo "Flink JobManager not ready yet, waiting..."
    sleep 5
done
echo "✅ Flink JobManager is ready!"

# Step 7: Start Flink job
echo "⚡ Starting Flink streaming job..."
docker exec sp_jobmanager flink run -py /opt/flink_jobs/stream_job.py
echo "✅ Flink job submitted!"

# Step 8: Wait for data to start flowing
echo "⏳ Waiting for data to start flowing..."
sleep 30

# Step 9: Check if everything is working
echo "🔍 Checking pipeline status..."

# Check if orders are being generated
ORDER_COUNT=$(docker exec sp_postgres psql -U postgres -d streaming -t -c "SELECT COUNT(*) FROM orders;" | tr -d ' ')
echo "📊 Orders in database: $ORDER_COUNT"

# Check if Kafka has messages
KAFKA_MESSAGES=$(docker exec sp_kafka /bin/kafka-console-consumer --bootstrap-server localhost:9092 --topic orders_cdc.public.orders --max-messages 3 --timeout-ms 5000 2>/dev/null | wc -l)
if [ "$KAFKA_MESSAGES" -gt 0 ]; then
    echo "✅ Kafka has messages"
else
    echo "⚠️  No messages in Kafka yet"
fi

# Check if aggregations are being created
AGG_COUNT=$(docker exec sp_postgres psql -U postgres -d streaming -t -c "SELECT COUNT(*) FROM order_agg;" | tr -d ' ')
echo "📈 Aggregations in database: $AGG_COUNT"

echo ""
echo "🎉 Pipeline is running!"
echo ""
echo "📋 Useful commands:"
echo "  Check aggregations: docker exec sp_postgres psql -U postgres -d streaming -c \"SELECT * FROM order_agg ORDER BY gross_sales DESC LIMIT 5;\""
echo "  Flink UI:         http://localhost:8081"
echo "  Kafka Connect:    http://localhost:8083"
echo ""
echo "🛑 To stop: docker compose down -v" 