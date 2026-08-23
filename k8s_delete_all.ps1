# k8s_delete_all.ps1
param([switch]$FullDelete)

Write-Host "Cleaning up Kubernetes resources..." -ForegroundColor Red
kubectl delete -f .\k8s\ --ignore-not-found=true

if ($FullDelete) {
    Write-Host "Stopping and deleting Minikube cluster..." -ForegroundColor Red
    minikube delete
}

Start-Sleep -Seconds 10