#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
REPO_NAME="cuba-news" # Reusing existing repo for simplicity, or create new one
IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/brand-agent"
JOB_NAME="brand-monitoring-job"

echo "Creating BigQuery Dataset and Table..."
bq mk --dataset --location=US ${PROJECT_ID}:brand_monitoring || echo "Dataset already exists"
bq mk --table ${PROJECT_ID}:brand_monitoring.mentions \
    id:STRING,source:STRING,text:STRING,sentiment:STRING,urgency:STRING,timestamp:TIMESTAMP || echo "Table already exists"

echo "Creating temporary cloudbuild.yaml..."
cat <<EOF > cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '$IMAGE_NAME', '-f', 'Dockerfile', '.']
images: ['$IMAGE_NAME']
EOF

# Create a simple Dockerfile for this agent
cat <<EOF > Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir google-cloud-firestore google-cloud-bigquery google-cloud-aiplatform requests pyyaml markdown matplotlib pandas
CMD ["python", "main.py"]
EOF

echo "Building and pushing Docker image..."
gcloud builds submit --config cloudbuild.yaml .
rm cloudbuild.yaml Dockerfile

echo "Creating/Updating Cloud Run Job..."
if gcloud run jobs describe $JOB_NAME --region $REGION > /dev/null 2>&1; then
    gcloud run jobs update $JOB_NAME \
        --image $IMAGE_NAME \
        --region $REGION \
        --set-env-vars="NON_INTERACTIVE=true,GMAIL_USER=renier.perez@gmail.com,GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
        --set-secrets="GMAIL_PASSWORD=GMAIL_PASSWORD:latest,SERPAPI_KEY=SERPAPI_KEY:latest"
else
    gcloud run jobs create $JOB_NAME \
        --image $IMAGE_NAME \
        --region $REGION \
        --set-env-vars="NON_INTERACTIVE=true,GMAIL_USER=renier.perez@gmail.com,GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
        --set-secrets="GMAIL_PASSWORD=GMAIL_PASSWORD:latest,SERPAPI_KEY=SERPAPI_KEY:latest"
fi

echo "Creating/Updating Cloud Scheduler Job..."
SCHEDULER_JOB_NAME="brand-monitoring-weekly"
SCHEDULE="0 8 * * 1" # Every Monday at 8:00 AM
SERVICE_ACCOUNT_EMAIL="30162433848-compute@developer.gserviceaccount.com"

if gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location $REGION > /dev/null 2>&1; then
    gcloud scheduler jobs update http $SCHEDULER_JOB_NAME \
        --location $REGION \
        --schedule "$SCHEDULE" \
        --time-zone "America/Santiago" \
        --uri "https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
        --http-method POST \
        --oauth-service-account-email $SERVICE_ACCOUNT_EMAIL
else
    gcloud scheduler jobs create http $SCHEDULER_JOB_NAME \
        --location $REGION \
        --schedule "$SCHEDULE" \
        --time-zone "America/Santiago" \
        --uri "https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
        --http-method POST \
        --oauth-service-account-email $SERVICE_ACCOUNT_EMAIL
fi

echo "Cloud Run Job $JOB_NAME and Scheduler $SCHEDULER_JOB_NAME created/updated."
