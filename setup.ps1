# setup.ps1
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

# Check if Minikube is running
$minikubeStatus = minikube status --format='{{.Host}}' 2>$null

# stop if running
if ($minikubeStatus -eq "Running") {
    Write-Host "Stopping existing Minikube cluster gracefully..." -ForegroundColor Yellow
    minikube stop
}

# Check minikube is intialised
Write-Host "Checking Minikube Status..."  -ForegroundColor Green
if ((minikube status) -notmatch "Running") {
    minikube start --driver=docker
}

# Enable ingress add on
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
    Write-Warning ".env file not found. Copying .env.example to .env..."  -ForegroundColor Yellow
    Copy-Item .env.example .env
    kubectl create configmap config --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
}

# Apply manifest files
Write-Host "Deploying Kubernetes Manifests..."  -ForegroundColor Green
kubectl apply -f k8s/

# Wait for deployments to start
Write-Host "Waiting for Deployments to become Ready..."  -ForegroundColor Green
kubectl wait --for=condition=available deployment --all --timeout=120s

# Start minikube tunnel
Write-Host "Launching Minikube Tunnel in a new Administrator window..."  -ForegroundColor Green

# Opens a separate PowerShell window running minikube tunnel as Admin
Start-Process powershell -Verb RunAs -ArgumentList "-NoExit -Command minikube tunnel"
Write-Host "Setup complete! Keep the opened tunnel window running."  -ForegroundColor Green

Start-Process "http://telco-churn.local"