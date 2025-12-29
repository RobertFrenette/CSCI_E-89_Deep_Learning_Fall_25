#!/bin/bash
# Refresh PostgreSQL database from CSV files

docker run --rm \
  --network insure-network \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/database-init:/app/database-init" \
  -w /app/database-init \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=insurance_db \
  -e POSTGRES_USER=insure_admin \
  -e POSTGRES_PASSWORD=insure_secure_pass_2025 \
  python:3.11-slim \
  sh -c "pip install -q --no-cache-dir psycopg2-binary python-dotenv && python load_data.py"

