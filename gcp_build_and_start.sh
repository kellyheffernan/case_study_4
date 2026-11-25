#!/bin/bash
set -e

IMAGE="docker.io/kellywpi/case-study-4:vertex-ai"
SERVICE_NAME="case-study-4"
REGION="us-central1"
PORT="7860"
MEMORY="4Gi"
CPU="1"

PROJECT_ID="case-study-4-515318"
SERVICE_ACCOUNT="cs4-vertex-inference@${PROJECT_ID}.iam.gserviceaccount.com"
LOCATION="global"
MODEL="gemini-3.5-flash-lite"

GCP_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/case-study-4/case-study-4:vertex-ai"
# Build a Linux AMD64 image for Cloud Run.
docker build --platform linux/amd64 -t "$IMAGE" .

# Push the container to Docker Hub.
docker push "$IMAGE"

# Pushing to Google Artifact Registry because I kept running into issues with Cloud Run taking forever to cache my Docker image
docker tag "$IMAGE" "$GCP_IMAGE"
docker push "$GCP_IMAGE"

# Deploy to Google Cloud Run with 4 GiB of memory per instance.
gcloud run deploy "$SERVICE_NAME" \
  --image "$GCP_IMAGE" \
  --project "$PROJECT_ID" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port "$PORT" \
  --cpu "$CPU" \
  --memory "$MEMORY" \
  --service-account "$SERVICE_ACCOUNT" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${LOCATION},GEMINI_MODEL=${MODEL}" \
  --min-instances 0 \
  --max-instances 1

# Get the deployed service URL.
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --project "$PROJECT_ID" \
  --platform managed \
  --region "$REGION" \
  --format="value(status.url)")

echo "Deployment complete!"
echo "Docker Image:    $IMAGE"
echo "GCP Image:       $GCP_IMAGE"
echo "Service name:    $SERVICE_NAME"
echo "Region:          $REGION"
echo "Memory:          $MEMORY per instance"
echo "Inference model: $MODEL"
echo "Service account: $SERVICE_ACCOUNT"
echo "Service URL:     $SERVICE_URL"




