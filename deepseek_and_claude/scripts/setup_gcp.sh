#!/bin/bash

# Configuration
PROJECT_ID="your-project-id"  # Replace with your GCP project ID
REGION="us-central1"          # Replace with your preferred region

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    firestore.googleapis.com

# Create service account
echo "Creating service account..."
gcloud iam service-accounts create github-branch-cleaner \
    --display-name "GitHub Branch Cleaner Service Account"

# Grant necessary permissions
echo "Granting permissions..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member "serviceAccount:github-branch-cleaner@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role "roles/datastore.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member "serviceAccount:github-branch-cleaner@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role "roles/cloudscheduler.jobRunner"

echo "GCP setup complete!" 