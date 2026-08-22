# Stop execution on unhandled errors


Write-Host "`n[0/4] Checking Minikube status..." -ForegroundColor Cyan

# Check if Minikube is running
$minikubeStatus = minikube status --format='{{.Host}}' 2>$null

# stop if running
if ($minikubeStatus -eq "Running") {
    Write-Host "Stopping existing Minikube cluster gracefully..." -ForegroundColor Yellow
    minikube stop
}

# start minikube
Write-Host "Starting Minikube cluster..." -ForegroundColor Yellow
minikube start

# Apply Manifest Files
Write-Host "`n[1/4] Applying Kubernetes Manifests from k8s\..." -ForegroundColor Green
if (Test-Path ".\k8s") {
    kubectl apply -f .\k8s\
} else {
    Write-Host "ERROR: Could not find 'k8s' directory!" -ForegroundColor Red
    Start-Sleep -Seconds 5
    exit 1
}

# 2Trigger Rolling Restart Across All Deployments
Write-Host "`n[2/4] Triggering rolling updates..." -ForegroundColor Green
kubectl rollout restart deployment -n default

# Monitor Rolling Update Progress
Write-Host "`n[3/4] Monitoring rollout status..." -ForegroundColor Green
$deployments = kubectl get deployments -n default -o jsonpath='{.items[*].metadata.name}'

if ($deployments) {
    foreach ($dep in $deployments.Split(' ')) {
        if ($dep) {
            Write-Host " -> Rolling out update for: $dep..." -ForegroundColor Gray
            kubectl rollout status deployment/$dep -n default --timeout=180s
        }
    }
} else {
    Write-Host "No active deployments found to update." -ForegroundColor DarkGray
}

Write-Host "`nRolling Update Completed!" -ForegroundColor Green

# Show Current Pods & Launch Tunnel/Browser
Write-Host "`n[4/4] Final Setup" -ForegroundColor Cyan
Write-Host "CURRENT POD STATUS:" -ForegroundColor Green
kubectl get pods

Write-Host "`nLaunching Minikube Tunnel in a new Administrator window..." -ForegroundColor Green
Start-Process powershell -Verb RunAs -ArgumentList "-NoExit -Command minikube tunnel"

Write-Host "Opening web browser..." -ForegroundColor Green
Start-Process "http://telco-churn.local"

Write-Host "`nSetup complete! Keep the opened tunnel window running." -ForegroundColor Green