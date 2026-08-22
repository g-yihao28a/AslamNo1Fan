#!/usr/bin/env bash
set -e

DOMAIN="telco-churn.local"
HOSTS_PATH="/etc/hosts"

# Color outputs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Update Hosts File
echo -e "${CYAN}[1/8] Checking host mapping...${NC}"
if ! grep -q "127.0.0.1[[:space:]]\+$DOMAIN" "$HOSTS_PATH"; then
    echo -e "${YELLOW}Adding $DOMAIN to $HOSTS_PATH (requires sudo privileges)...${NC}"
    echo "127.0.0.1 $DOMAIN" | sudo tee -a "$HOSTS_PATH" > /dev/null
    echo -e "${GREEN}Host mapping added successfully!${NC}"
else
    echo -e "${GREEN}Host mapping for $DOMAIN already exists.${NC}"
fi

# Check Prerequisites
echo -e "\n${CYAN}[2/8] Checking prerequisites...${NC}"
if ! command -v minikube &> /dev/null; then
    echo "Error: Minikube is not installed or not in PATH." >&2
    exit 1
fi

# Start Minikube
echo -e "\n${CYAN}[3/8] Starting Minikube...${NC}"
if ! minikube status &> /dev/null; then
    minikube start --driver=docker
fi

# Enable Addons & Wait for Readiness
echo -e "\n${CYAN}[4/8] Enabling Minikube Addons...${NC}"
minikube addons enable ingress
minikube addons enable metrics-server

echo -e "${YELLOW}-> Waiting for Ingress Controller...${NC}"
kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx --timeout=120s

echo -e "${YELLOW}-> Waiting for Metrics Server...${NC}"
kubectl rollout status deployment/metrics-server -n kube-system --timeout=120s

# Handle ConfigMap (.env)
echo -e "\n${CYAN}[5/8] Configuring Environment ConfigMap...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}.env file not found. Copying .env.example to .env...${NC}"
        cp .env.example .env
    else
        echo -e "${YELLOW}Warning: Neither .env nor .env.example found. Proceeding without env-file.${NC}"
    fi
fi

if [ -f ".env" ]; then
    kubectl create configmap config --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
fi

# Build & Load Docker Images into Minikube
echo -e "\n${CYAN}[6/8] Building Docker images...${NC}"
docker compose --profile tools build

echo -e "${GREEN}Loading images into Minikube image store...${NC}"
minikube image load nigelnakajima/telco-database-loader:v1
minikube image load nigelnakajima/telco-database-service:v1
minikube image load nigelnakajima/telco-database:v1
minikube image load nigelnakajima/api_gateway:v1
minikube image load nigelnakajima/dashboard:v1
minikube image load hongheng/ml_engine:v1
minikube image load hongheng/ml_prediction:v1

# Apply Kubernetes Manifests
echo -e "\n${CYAN}[7/8] Deploying Kubernetes Manifests...${NC}"
kubectl apply -f k8s/

sleep 3
echo -e "${YELLOW}Waiting for Deployments to become ready...${NC}"
kubectl wait --for=condition=available deployment --all --timeout=180s

# Start Minikube Tunnel & Launch Browser
echo -e "\n${CYAN}[8/8] Launching Minikube Tunnel...${NC}"
echo -e "${YELLOW}Minikube tunnel requires elevated privileges. Please enter password if prompted:${NC}"

# Launch tunnel in background
sudo -E minikube tunnel > /dev/null 2>&1 &
TUNNEL_PID=$!

echo -e "${GREEN}Setup complete! Minikube tunnel running in background (PID: $TUNNEL_PID).${NC}"

# Open browser cross-platform (macOS/Linux)
sleep 2
if command -v open &> /dev/null; then
    open "http://$DOMAIN"          # macOS
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://$DOMAIN"      # Linux (Ubuntu, Debian, Fedora, etc.)
else
    echo -e "Navigate to ${CYAN}http://$DOMAIN${NC} in your browser."
fi

echo -e "\n${GREEN}Press [ENTER] to stop minikube tunnel and exit.${NC}"
read -r

# Clean up background tunnel process on exit
if [ -n "$TUNNEL_PID" ]; then
    sudo kill "$TUNNEL_PID" 2>/dev/null || true
fi