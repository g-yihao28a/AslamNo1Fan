#!/usr/bin/env bash
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

# Ensure the database is running and healthy
echo -e "${CYAN}Checking database state...${NC}"
docker compose up -d database

# Run the db-loader job and remove its container when finished
echo -e "\n${CYAN}Running database loader...${NC}"
docker compose run --rm db-loader

echo -e "\n${GREEN}Database seeding completed successfully!${NC}"

# Wait a bit
sleep 10