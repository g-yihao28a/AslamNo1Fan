# k8s_db_loader.ps1
Write-Host "Triggering Database Loader Job..." -ForegroundColor Cyan
kubectl delete job db-loader --ignore-not-found=true
kubectl apply -f .\k8s\database.yaml

Write-Host "Waiting for database load to complete..." -ForegroundColor Yellow
kubectl wait --for=condition=complete job/db-loader --timeout=120s
kubectl logs job/db-loader

Start-Sleep -Seconds 10