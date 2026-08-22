# docker_rebuild.ps1
param(
    [switch]$SeedDb
)

$ErrorActionPreference = "Stop"

$GREEN = "Green"
$CYAN = "Cyan"

# Rebuild images
Write-Host "Rebuilding Docker images..." -ForegroundColor $CYAN
docker compose build

# Start database
docker compose up -d database --wait

# SeedDb
if ($SeedDb) {
    Write-Host "`nRe-running database loader..." -ForegroundColor $CYAN
    docker compose run --rm db-loader
}

# Start the rest
Write-Host "`nLaunching updated stack..." -ForegroundColor $CYAN
docker compose up -d --wait --force-recreate --build


# Show info
Write-Host "`nStack redeployed successfully!" -ForegroundColor $GREEN
docker compose ps

# Wait a bit
Start-Sleep -Seconds 10