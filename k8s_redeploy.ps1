# k8s_redeploy.ps1
param (
    [switch]$BuildImages,
    [switch]$SeedDb
)

$ErrorActionPreference = "Stop"

# Optionally Rebuild and Load Local Docker Images
if ($BuildImages) {
    Write-Host "Rebuilding and loading updated container images into Minikube..." -ForegroundColor Cyan
    docker compose --profile tools build
    minikube image load nigelnakajima/telco-database-loader:v1
    minikube image load nigelnakajima/telco-database-service:v1
    minikube image load nigelnakajima/telco-database:v1
    minikube image load nigelnakajima/api_gateway:v1
    minikube image load nigelnakajima/dashboard:v1
    minikube image load hongheng/ml_engine:v1
    minikube image load hongheng/ml_prediction:v1
}

# Trigger Rolling Restarts
Write-Host "`nTriggering rolling restart across all deployments..." -ForegroundColor Cyan
kubectl rollout restart deployment -n default

# Monitor Status Across Deployments
Write-Host "`nMonitoring rollout status for all deployments..." -ForegroundColor Yellow
$Deployments = (kubectl get deployment -n default -o jsonpath='{.items[*].metadata.name}').Split(" ")

foreach ($Dep in $Deployments) {
    if (-not [string]::IsNullOrWhitespace($Dep)) {
        Write-Host "-> Checking status for: $Dep" -ForegroundColor Cyan
        kubectl rollout status deployment/$Dep -n default --timeout=90s
    }
}

# Optionally Run DB Seeding Job
if ($SeedDb) {
    Write-Host "`nRe-running Database Loader Job..." -ForegroundColor Cyan
    kubectl delete job db-loader --ignore-not-found=true
    kubectl apply -f .\k8s\database.yaml
    kubectl wait --for=condition=complete job/db-loader --timeout=120s
}

Write-Host " All services successfully redeployed and healthy!" -ForegroundColor Green

# Print Current Pod Overview
Write-Host "`nCurrent Pod Overview:" -ForegroundColor Yellow
kubectl get pods -n default

Start-Sleep -Seconds 10