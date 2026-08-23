#!/usr/bin/env bash
set -e

# Parse flags 
SEED_DB=false

for arg in "$@"; do
  case $arg in
    -SeedDb)
      SEED_DB=true
      break
      ;;
  esac
done

# Colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Rebuild images
echo -e "${CYAN}Rebuilding Docker images...${NC}"
docker compose build
# Start database
docker compose up -d database --wait

# SeedDb
if [ "$SEED_DB" = true ]; then
    echo -e "\n${CYAN}Re-running database loader...${NC}"
    docker compose run --rm db-loader
fi

# Start the rest
echo -e "\n${CYAN}Launching updated stack...${NC}"
docker compose up -d --wait --force-recreate --build

# Show info
echo -e "\n${GREEN}Stack redeployed successfully!${NC}"
docker compose ps

# Wait a bit
sleep 10