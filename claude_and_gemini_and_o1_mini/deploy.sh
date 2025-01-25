#!/bin/bash
set -e

# Check if required environment variables are set
if [ -z "$PROJECT_ID" ]; then
    echo "Please set PROJECT_ID environment variable"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Please set GITHUB_TOKEN environment variable"
    exit 1
fi

if [ -z "$SLACK_TOKEN" ]; then
    echo "Please set SLACK_TOKEN environment variable"
    exit 1
fi

# Enable required APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com

# Create secrets
echo -n "$GITHUB_TOKEN" | gcloud secrets create github-token --data-file=-
echo -n "$SLACK_TOKEN" | gcloud secrets create slack-token --data-file=-

# Build and push the container
gcloud builds submit --tag gcr.io/$PROJECT_ID/github-branch-manager

# Create the Cloud Run job
gcloud run jobs create github-branch-manager \
    --image gcr.io/$PROJECT_ID/github-branch-manager \
    --set-secrets=GITHUB_TOKEN=github-token:latest \
    --set-secrets=SLACK_TOKEN=slack-token:latest \
    --set-env-vars="GITHUB_ORG=your-org-name"

# Create a Cloud Scheduler job to run weekly
gcloud scheduler jobs create http github-branch-manager-weekly \
    --schedule="0 0 * * 0" \
    --uri="$(gcloud run jobs describe github-branch-manager --format='value(status.address.url)')" \
    --http-method=POST \
    --attempt-deadline=1800s \
    --time-zone="UTC"

echo "Deployment complete!" 