# docker_db_loader.ps1
$ErrorActionPreference = "Stop"

$CYAN = "Cyan"
$GREEN = "Green"

# Ensure the database service is running and healthy
Write-Host "Checking database state..." -ForegroundColor $CYAN
docker compose up -d database

# Run the db-loader job and remove its container when finished
Write-Host "`nRunning database loader..." -ForegroundColor $CYAN
docker compose run --rm db-loader

Write-Host "`nDatabase seeding completed successfully!" -ForegroundColor $GREEN

# Wait a bit
Start-Sleep -Seconds 10