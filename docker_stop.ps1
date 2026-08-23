# docker_stop.ps1
param(
    [switch]$Wipe
)

$ErrorActionPreference = "Stop"

$YELLOW = "Yellow"
$GREEN = "Green"

if ($Wipe) {
    Write-Host "Stopping stack and deleting all persistent volumes..." -ForegroundColor $YELLOW
    docker compose down -v --remove-orphans
    Write-Host "Stack and volumes purged!" -ForegroundColor $GREEN
} else {
    Write-Host "Stopping stack..." -ForegroundColor $YELLOW
    docker compose down --remove-orphans
    Write-Host "Stack stopped safely!" -ForegroundColor $GREEN
}

# Wait a bit
Start-Sleep -Seconds 10