# k8s_setup.ps1
$ErrorActionPreference = "Stop"

$Domain = "telco-churn.local"
$HostsPath = "$env:windir\System32\drivers\etc\hosts"

# Check if mapping already exists
$HostsContent = Get-Content $HostsPath -ErrorAction SilentlyContinue
if ($HostsContent -notmatch "127\.0\.0\.1\s+$Domain") {
    Write-Host "Adding $Domain to hosts file..."
    
    # Run an elevated PowerShell process to append to hosts file safely
    $Command = "Add-Content -Path '$HostsPath' -Value '`n127.0.0.1 $Domain'"
    Start-Process powershell -Verb RunAs -ArgumentList "-Command $Command" -Wait
    
    # Flush local DNS cache
    ipconfig /flushdns | Out-Null
    Write-Host "Host mapping added and DNS flushed successfully!"
} else {
    Write-Host "Host mapping for $Domain already exists."
}

# Check for minikube
Write-Host "Checking prerequisites..." -ForegroundColor Green
if (-not (Get-Command minikube -ErrorAction SilentlyContinue)) { Stop-Process -Id $PID -ErrorAction Stop; Write-Error "Minikube is required." }

# Start minikube
Write-Host "Starting Minikube..." -ForegroundColor Green
minikube status | Out-Null
if ($LASTEXITCODE -ne 0) { minikube start --driver=docker }

# Enable add ons
Write-Host " Enabling Required Minikube Addons..."  -ForegroundColor Green
minikube addons enable ingress
minikube addons enable metrics-server

Write-Host " Waiting for Minikube Addons to initialize and become ready..."  -ForegroundColor Green

# Wait for ingress-nginx controller to be ready
Write-Host "-> Waiting for Ingress Controller..."  -ForegroundColor Green
kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx --timeout=120s

# Wait for metrics-server deployment to be ready
Write-Host "-> Waiting for Metrics Server..."  -ForegroundColor Green
kubectl rollout status deployment/metrics-server -n kube-system --timeout=120s

# Create configmap from .env
Write-Host "Creating ConfigMap from .env..."  -ForegroundColor Green
if (Test-Path ".env") {
    kubectl create configmap config --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
} else {
    # If .env not found
    Write-Warning ".env file not found. Copying .env.example to .env..."  -ForegroundColor Green
    Copy-Item .env.example .env
    kubectl create configmap config --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
}

# Build docker images
Write-Host "Building docker images..."  -ForegroundColor Green
docker compose --profile tools build

# Pointing image loading directly into Minikube's engine
Write-Host "Loading images into Minikube image store..." -ForegroundColor Green
minikube image load nigelnakajima/telco-database-loader:v1
minikube image load nigelnakajima/telco-database-service:v1
minikube image load nigelnakajima/telco-database:v1
minikube image load nigelnakajima/api_gateway:v1
minikube image load nigelnakajima/dashboard:v1
minikube image load hongheng/ml_engine:v1
minikube image load hongheng/ml_prediction:v1

# Apply k8s manifest files
Write-Host "Deploying Kubernetes Manifests..."  -ForegroundColor Green
kubectl apply -f k8s/

# Wait for deployments to start
Start-Sleep -Seconds 3
Write-Host "Waiting for Deployments to become ready..." -ForegroundColor Yellow
kubectl wait --for=condition=available deployment --all --timeout=180s

# Start minikube tunnel
Write-Host "Launching Minikube Tunnel in a new Administrator window..."  -ForegroundColor Green

# Opens a separate PowerShell window running minikube tunnel as Admin
Start-Process powershell -Verb RunAs -ArgumentList "-NoExit -Command minikube tunnel"
Write-Host "Setup complete! Keep the opened tunnel window running."  -ForegroundColor Green

Start-Sleep -Seconds 2
Start-Process "http://$Domain"