#!/bin/bash

# deploy_multitenant.sh
# Usage: ./deploy_multitenant.sh <BRAND_ID>

set -e

BRAND_ID=$1

if [ -z "$BRAND_ID" ]; then
  echo "❌ Error: BRAND_ID is required."
  echo "Usage: ./deploy_multitenant.sh <BRAND_ID>"
  echo "Example: ./deploy_multitenant.sh banco_chile"
  exit 1
fi

echo "🚀 Deploying Agent for Brand: $BRAND_ID"

# 0. Generate Dockerfile
echo "📄 Generating Dockerfile..."
cat <<EOF > Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir google-cloud-firestore google-cloud-bigquery google-cloud-aiplatform requests pyyaml markdown matplotlib pandas
CMD ["python", "main.py"]
EOF

# 1. Build Docker Image (Cloud Build)
IMAGE_NAME="us-central1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/cuba-news/brand-agent:latest"
echo "📦 Building Docker Image with Cloud Build..."
gcloud builds submit --tag $IMAGE_NAME .

# 2. Update/Create Cloud Run Job for this specific Brand
# Replace underscores with dashes for Cloud Run Job Name compliance
SANITIZED_BRAND_ID=${BRAND_ID//_/-}
JOB_NAME="brand-agent-$SANITIZED_BRAND_ID"
REGION="us-central1"

echo "☁️ Updating/Creating Cloud Run Job: $JOB_NAME"

# Define fixed variables (or fetch from Secret Manager if preferred)
GMAIL_USER="renier.perez@gmail.com"
BCC_EMAILS="renier.perez@gmail.com;renierperez@google.com;pedrogarciacl@google.com;mmarocchi@google.com;odure@google.com"

if gcloud run jobs describe $JOB_NAME --region $REGION > /dev/null 2>&1; then
    gcloud run jobs update $JOB_NAME \
      --image $IMAGE_NAME \
      --region $REGION \
      --set-env-vars="BRAND_ID=$BRAND_ID,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GMAIL_USER=$GMAIL_USER,BCC_EMAILS=$BCC_EMAILS" \
      --set-secrets="GMAIL_PASSWORD=GMAIL_PASSWORD:latest,SERPAPI_KEY=SERPAPI_KEY:latest" \
      --max-retries 0 \
      --task-timeout 300s \
      --memory 2Gi \
      --cpu 1
else
    gcloud run jobs create $JOB_NAME \
      --image $IMAGE_NAME \
      --region $REGION \
      --set-env-vars="BRAND_ID=$BRAND_ID,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GMAIL_USER=$GMAIL_USER,BCC_EMAILS=$BCC_EMAILS" \
      --set-secrets="GMAIL_PASSWORD=GMAIL_PASSWORD:latest,SERPAPI_KEY=SERPAPI_KEY:latest" \
      --max-retries 0 \
      --task-timeout 300s \
      --memory 2Gi \
      --cpu 1
fi

# 3. Update Scheduler (Optional - assuming weekly for all)
SCHEDULER_NAME="$JOB_NAME-weekly"
echo "⏰ Updating Scheduler: $SCHEDULER_NAME"

# Note: We use 'gcloud run jobs execute' via http target or just create a scheduler that targets the job
# Simpler approach: Create a scheduler that invokes the job via the run.googleapis.com API
# But for now, let's just ensure the job exists. The user can schedule it manually or we can add it.
# We will skip scheduler creation to keep it simple, or we can add it if requested.
# Let's add it for completeness.

SERVICE_ACCOUNT_EMAIL=$(gcloud config get-value account) # Or specific SA

if gcloud scheduler jobs describe $SCHEDULER_NAME --location $REGION > /dev/null 2>&1; then
    echo "🔄 Updating Scheduler: $SCHEDULER_NAME"
    gcloud scheduler jobs update http $SCHEDULER_NAME \
      --schedule="0 8 * * 1" \
      --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$GOOGLE_CLOUD_PROJECT/jobs/$JOB_NAME:run" \
      --http-method POST \
      --oauth-service-account-email "30162433848-compute@developer.gserviceaccount.com" \
      --location $REGION \
      --time-zone "America/Santiago"
else
    echo "➕ Creating Scheduler: $SCHEDULER_NAME"
    gcloud scheduler jobs create http $SCHEDULER_NAME \
      --schedule="0 8 * * 1" \
      --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$GOOGLE_CLOUD_PROJECT/jobs/$JOB_NAME:run" \
      --http-method POST \
      --oauth-service-account-email "30162433848-compute@developer.gserviceaccount.com" \
      --location $REGION \
      --time-zone "America/Santiago"
fi

echo "✅ Deployment Complete for $BRAND_ID!"
