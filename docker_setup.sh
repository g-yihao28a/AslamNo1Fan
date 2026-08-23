#!/usr/bin/env bash
set -e

DOMAIN="telco-churn.local"
HOSTS_PATH="/etc/hosts"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Update Hosts File
echo -e "${CYAN}Checking host mapping...${NC}"
if ! grep -q "127.0.0.1[[:space:]]\+$DOMAIN" "$HOSTS_PATH"; then
    echo -e "${YELLOW}Adding $DOMAIN to $HOSTS_PATH (requires sudo)...${NC}"
    echo "127.0.0.1 $DOMAIN" | sudo tee -a "$HOSTS_PATH" > /dev/null
    echo -e "${GREEN}Host mapping added!${NC}"
else
    echo -e "${GREEN}Host mapping already exists.${NC}"
fi

# Check Environment File
echo -e "\n${CYAN}Checking environment file...${NC}"
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo -e "${YELLOW}Copying .env.example to .env...${NC}"
    cp .env.example .env
fi

# Build and Spin Up Containers
echo -e "\n${CYAN}Building and launching Docker Compose stack...${NC}"
docker compose up -d database --wait
docker compose run --rm db-loader 
docker compose up -d --wait

# Open Application
sleep 3
echo -e "\n${CYAN}Launching application...${NC}"

# Open in browser
if command -v open &> /dev/null; then
    open "http://$DOMAIN"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://$DOMAIN"
else
    echo -e "Navigate to ${CYAN}http://$DOMAIN${NC} in your browser."
fi

echo -e "\n${GREEN}Docker Compose stack running successfully!${NC}"

# Show info
docker compose ps

# Wait a bit
sleep 10