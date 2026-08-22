#!/usr/bin/env bash
set -e

# Default flag values
BUILD_IMAGES=false
SEED_DB=false

# Parse command line flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --BuildImages) BUILD_IMAGES=true ;;
        --SeedDb) SEED_DB=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Color outputs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Optionally Rebuild and Load Local Docker Images
if [ "$BUILD_IMAGES" = true ]; then
    echo -e "${CYAN}Rebuilding and loading updated container images into Minikube...${NC}"
    docker compose --profile tools build

    echo -e "${GREEN}Loading images into Minikube image store...${NC}"
    minikube image load nigelnakajima/telco-database-loader:v1
    minikube image load nigelnakajima/telco-database-service:v1
    minikube image load nigelnakajima/telco-database:v1
    minikube image load nigelnakajima/api_gateway:v1
    minikube image load nigelnakajima/dashboard:v1
    minikube image load hongheng/ml_engine:v1
    minikube image load hongheng/ml_prediction:v1
fi

# Trigger Rolling Restarts
echo -e "\n${CYAN}Triggering rolling restart across all deployments...${NC}"
kubectl rollout restart deployment -n default

# Monitor Status Across Deployments
echo -e "\n${YELLOW}Monitoring rollout status for all deployments...${NC}"
DEPLOYMENTS=$(kubectl get deployment -n default -o jsonpath='{.items[*].metadata.name}')

for DEP in $DEPLOYMENTS; do
    if [ -n "$DEP" ]; then
        echo -e "${CYAN}-> Checking status for: $DEP${NC}"
        kubectl rollout status "deployment/$DEP" -n default --timeout=90s
    fi
done

# Optionally Run DB Seeding Job
if [ "$SEED_DB" = true ]; then
    echo -e "\n${CYAN}Re-running Database Loader Job...${NC}"
    kubectl delete job db-loader --ignore-not-found=true
    kubectl apply -f ./k8s/database.yaml
    kubectl wait --for=condition=complete job/db-loader --timeout=120s
fi

echo -e "\n${GREEN}All services successfully redeployed and healthy!${NC}"

# Print Current Pod Overview
echo -e "\n${YELLOW}Current Pod Overview:${NC}"
kubectl get pods -n default

# Wait a bit
sleep 10