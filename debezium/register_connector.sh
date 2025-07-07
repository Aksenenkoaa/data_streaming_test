#!/usr/bin/env bash
#
# Register (or update) the Debezium PostgreSQL connector.
# Usage:
#   ./debezium/register_connector.sh
#
# Set CONNECT_URL if Kafka Connect runs elsewhere.
set -euo pipefail

CONNECT_URL=${CONNECT_URL:-http://localhost:8083}
CONFIG_FILE="$(dirname "$0")/connector-config.json"

curl -s -o /dev/null -w "\nStatus: %{http_code}\n" -X PUT \
     -H "Accept:application/json" \
     -H "Content-Type:application/json" \
     --data @"$CONFIG_FILE" \
     "$CONNECT_URL/connectors/orders-connector/config"
