#!/bin/bash

# --- CONFIGURATION (UPDATE THESE) ---
PROJECT_ID="securemed-chat"          # Your GCP Project ID
REGION="southamerica-east1"          # Desired Region
SERVICE_NAME="securemed-api"         # Service name for Cloud Run
# ------------------------------------

echo "🚀 Starting Zero-Cost Backend Deployment for SecureMed..."

# Check if logged in
if ! gcloud auth list --format="value(account)" | grep -q "@"; then
    echo "❌ Error: Not logged into gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the active project
gcloud config set project $PROJECT_ID

# Deploy the API to Cloud Run
# --source . : Builds and pushes the container automatically
# --min-instances 0 : Essential for zero cost
# --no-cpu-throttling : Optional but recommended for better latency
echo "🐳 Building and deploying container to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --min-instances 0 \
    --allow-unauthenticated \
    --set-env-vars="SECUREMED_API_KEY=dev_key_123"

echo "✅ Backend Deployment Finished!"
echo "🔗 Your API URL should be visible above."
echo "👉 Next: Update your Reflex Frontend with the new API URL."
