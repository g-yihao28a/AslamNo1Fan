# Stop on error
$ErrorActionPreference = "Stop"

Write-Host "[1/3] Building Docker Images..." -ForegroundColor Green
docker compose build --no-cache

Write-Host "`n[2/3] Pushing Images to Registry..." -ForegroundColor Green
docker compose push

Write-Host "`n[3/3] Triggering Kubernetes Rollout..." -ForegroundColor Green
.\deploy.ps1

# Wait a bit
Start-Sleep -Seconds 5