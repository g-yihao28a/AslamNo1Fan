#!/usr/bin/env bash
set -e

# Default flag value
FULL_DELETE=false

# Parse command line flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --FullDelete) FULL_DELETE=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Color outputs
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}Cleaning up Kubernetes resources...${NC}"
kubectl delete -f ./k8s/ --ignore-not-found=true

if [ "$FULL_DELETE" = true ]; then
    echo -e "${RED}Stopping and deleting Minikube cluster...${NC}"
    minikube delete
fi

# Wait a bit
sleep 10