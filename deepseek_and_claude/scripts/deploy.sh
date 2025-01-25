#!/bin/bash

# Configuration
PROJECT_ID="your-project-id"  # Replace with your GCP project ID
REGION="us-central1"          # Replace with your preferred region
SERVICE_ACCOUNT="github-branch-cleaner@${PROJECT_ID}.iam.gserviceaccount.com"

# Build and deploy archive_branches function
echo "Deploying archive_branches service..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/github-branch-cleaner

gcloud run deploy github-branch-cleaner-archive \
    --image gcr.io/${PROJECT_ID}/github-branch-cleaner \
    --platform managed \
    --region ${REGION} \
    --service-account ${SERVICE_ACCOUNT} \
    --set-env-vars "$(cat .env | grep -v '^#' | xargs)" \
    --no-allow-unauthenticated

# Deploy purge_branches function (using same container but different entry point)
echo "Deploying purge_branches service..."
gcloud run deploy github-branch-cleaner-purge \
    --image gcr.io/${PROJECT_ID}/github-branch-cleaner \
    --platform managed \
    --region ${REGION} \
    --service-account ${SERVICE_ACCOUNT} \
    --set-env-vars "$(cat .env | grep -v '^#' | xargs)" \
    --set-env-vars "FUNCTION_TARGET=purge_branches" \
    --no-allow-unauthenticated

# Create Cloud Scheduler jobs
echo "Creating Cloud Scheduler jobs..."

# Weekly archive job (every Monday at 2 AM)
gcloud scheduler jobs create http archive-branches-weekly \
    --schedule "0 2 * * 1" \
    --location ${REGION} \
    --uri "$(gcloud run services describe github-branch-cleaner-archive --region ${REGION} --format 'value(status.url)')" \
    --http-method POST \
    --oidc-service-account-email ${SERVICE_ACCOUNT}

# Monthly purge job (1st of every month at 3 AM)
gcloud scheduler jobs create http purge-branches-monthly \
    --schedule "0 3 1 * *" \
    --location ${REGION} \
    --uri "$(gcloud run services describe github-branch-cleaner-purge --region ${REGION} --format 'value(status.url)')" \
    --http-method POST \
    --oidc-service-account-email ${SERVICE_ACCOUNT}

echo "Deployment complete!" 