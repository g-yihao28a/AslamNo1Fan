#docker_setup.ps1
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$DOMAIN = "telco-churn.local"
$HOSTS_PATH = "$env:SystemRoot\System32\drivers\etc\hosts"

# Colors for output
$GREEN = "Green"
$YELLOW = "Yellow"
$CYAN = "Cyan"

# Update Hosts File
Write-Host "Checking host mapping..." -ForegroundColor $CYAN
$hostsContent = Get-Content -Path $HOSTS_PATH -ErrorAction SilentlyContinue
if ($hostsContent -notmatch "127\.0\.0\.1\s+$DOMAIN") {
    Write-Host "Adding $DOMAIN to $HOSTS_PATH..." -ForegroundColor $YELLOW
    
    # Check if running as Administrator
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        Write-Host "Administrator privileges required to edit hosts file. Relaunching PowerShell as Admin..." -ForegroundColor $YELLOW
        Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
        exit
    }
    
    Add-Content -Path $HOSTS_PATH -Value "`n127.0.0.1 $DOMAIN"
    Write-Host "Host mapping added!" -ForegroundColor $GREEN
} else {
    Write-Host "Host mapping already exists." -ForegroundColor $GREEN
}

# Check .env File
Write-Host "`nChecking environment file..." -ForegroundColor $CYAN
if ((-not (Test-Path ".env")) -and (Test-Path ".env.example")) {
    Write-Host "Copying .env.example to .env..." -ForegroundColor $YELLOW
    Copy-Item ".env.example" ".env"
}

# Build and Spin Up Containers
Write-Host "`nBuilding and launching Docker Compose stack..." -ForegroundColor $CYAN
docker compose up -d database
docker compose run --rm db-loader
docker compose up -d --wait

# Open Application
Start-Sleep -Seconds 3
Write-Host "`nLaunching application..." -ForegroundColor $CYAN

# Open in browser
try {
    Start-Process "http://$DOMAIN"
} catch {
    Write-Host "Navigate to http://$DOMAIN in your browser." -ForegroundColor $CYAN
}

# Show info
Write-Host "`nDocker Compose stack running successfully!" -ForegroundColor $GREEN
docker compose ps

# Wait a bit
Start-Sleep -Seconds 10