#!/bin/bash
set -e

# Run schema migrations for Superset's own metadata DB
superset db upgrade

# Create the admin user if it doesn't already exist (idempotent-ish: Superset
# will just warn "already exists" on subsequent runs, which is fine)
superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
    --firstname Admin \
    --lastname Admin \
    --email "${SUPERSET_ADMIN_EMAIL:-admin@example.com}" \
    --password "${SUPERSET_ADMIN_PASSWORD:-admin}" \
    || true

superset init

exec gunicorn \
    --bind "0.0.0.0:${SUPERSET_PORT:-8088}" \
    --workers 4 \
    --timeout 120 \
    "superset.app:create_app()"
