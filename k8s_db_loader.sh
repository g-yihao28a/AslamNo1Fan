#!/usr/bin/env bash
set -e

# Color outputs
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${CYAN}Triggering Database Loader Job...${NC}"
kubectl delete job db-loader --ignore-not-found=true
kubectl apply -f ./k8s/database.yaml

echo -e "${YELLOW}Waiting for database load to complete...${NC}"
kubectl wait --for=condition=complete job/db-loader --timeout=120s

echo -e "${GREEN}Logs from job/db-loader:${NC}"
kubectl logs job/db-loader

# Wait a bit
sleep 10