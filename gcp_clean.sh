#! /bin/bash
set -e

SERVICE_NAME="case-study-4"
REGION="us-central1"

# Delete the container
gcloud run services delete "$SERVICE_NAME" --platform managed --region "$REGION"