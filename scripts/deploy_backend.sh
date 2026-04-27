#!/bin/bash

# --- CONFIGURATION (UPDATE THESE) ---
# --- CONFIGURATION (OVERRIDABLE VIA ENV) ---
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"ambassist-1771888311"} 
REGION=${GOOGLE_CLOUD_REGION:-"southamerica-east1"}
SERVICE_NAME=${SERVICE_NAME:-"securemed-api"}
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
# Require the API key to be set in the environment before deploying
if [ -z "$SECUREMED_API_KEY" ]; then
    echo "❌ Error: SECUREMED_API_KEY environment variable is not set."
    echo "   Set it before running this script: export SECUREMED_API_KEY=<your-secret-key>"
    exit 1
fi

echo "🐳 Building and deploying container to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --min-instances 0 \
    --max-instances 5 \
    --concurrency 50 \
    --allow-unauthenticated \
    --set-env-vars="SECUREMED_API_KEY=$SECUREMED_API_KEY"

echo "✅ Backend Deployment Finished!"
echo "🔗 Your API URL should be visible above."
echo "👉 Next: Update your Reflex Frontend with the new API URL."
