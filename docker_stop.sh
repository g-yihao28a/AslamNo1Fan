#!/usr/bin/env bash
set -e

# Parse flags
WIPE=false

for arg in "$@"; do
  case "$arg" in
    -Wipe)
      WIPE=true
      break
      ;;
  esac
done

# Colors for output
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

if [ "$WIPE" = true ]; then
    echo -e "${YELLOW}Stopping stack and deleting all persistent volumes...${NC}"
    docker compose down -v --remove-orphans
    echo -e "${GREEN}Stack and volumes purged!${NC}"
else
    echo -e "${YELLOW}Stopping stack...${NC}"
    docker compose down --remove-orphans
    echo -e "${GREEN}Stack stopped safely!${NC}"
fi

# Wait a bit
sleep 10