# setup.ps1
Write-Host "Checking Minikube Status..."
if ((minikube status) -notmatch "Running") {
    minikube start --driver=docker
}

Write-Host " Enabling Required Minikube Addons..."
minikube addons enable ingress
minikube addons enable ingress-dns

Write-Host "Creating ConfigMap from .env..." 
if (Test-Path ".env") {
    kubectl create configmap app-config --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
} else {
    Write-Warning ".env file not found. Copying .env.example to .env..."
    Copy-Item .env.example .env
    kubectl create configmap app-config --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
}

Write-Host "Deploying Kubernetes Manifests..."
kubectl apply -f k8s/

Write-Host "Waiting for Deployments to become Ready..."
kubectl wait --for=condition=available deployment --all --timeout=120s

Write-Host "Setup Complete! Remember to run 'minikube tunnel' in a separate terminal to route ingress traffic."