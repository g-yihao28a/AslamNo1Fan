# Copies .env.example
Copy-Item -Path ".env.example" -Destination ".env"
Write-Host ".env file created from .env.example"

# Start internal database
docker compose up -d database

# Run db loader
docker compose run --rm -d db_loader

# Run other services
docker compose up -d

# Train model
$response = Invoke-RestMethod -Uri "http://localhost:8008/ml/train" -Method Post
Write-Host "Title: $($response.title)"

# Wait a bit
sleep 3

# Open api gateway in browser
Start-Process "http://localhost:8008"