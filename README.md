# Case Study 4 for DS553 - Group 16 - Documentation

## GCP Deployment
### Manual Deployment with gcp_start_and_build.sh
1. Open Docker Desktop.
2. Open WSL -> change directory to location of gcp_build_and_start.sh.
3. Run command: bash gcp_build_and_start.sh
4. Should output a full container build & GCP deployment, will give a public URL at the end.
5. To delete service, run: bash gcp_clean.sh

### GitHub Actions Deployment with gcp_deploy.yml (Best Method to Re-Deploy Our GCP Container)
1. First I had to enable the different Google Cloud APIs: Cloud Run, Artifact Registry, and IAM Credentials. These were the commands I used in WSL:
    gcloud services enable \
    iam.googleapis.com \
    iamcredentials.googleapis.com \
    sts.googleapis.com \
    --project=case-study-4-515318

  gcloud services enable artifactregistry.googleapis.com \
    --project=case-study-4-515318

  gcloud services enable run.googleapis.com \
    --project=case-study-4-515318

2. I configured Workload Identity Federation with these commands:
  Workload Identity Pool
  gcloud iam workload-identity-pools create github-actions \
    --project=case-study-4-515318 \
    --location=global \
    --display-name="GitHub Actions"
     
  OIDC GitHub Provider
  gcloud iam workload-identity-pools providers create-oidc github-provider \
    --project=case-study-4-515318 \
    --location=global \
    --workload-identity-pool=github-actions \
    --display-name="GitHub Provider" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner_id=assertion.repository_owner_id" \
    --attribute-condition="assertion.repository_owner_id == '320231736' && assertion.repository == 'kellyheffernan/case_study_4'"

3. I gave GitHub Actions permissions to authenticate as this service account (949473891513-compute@developer.gserviceaccount.com)
  Giving the service account permissions:
  gcloud projects add-iam-policy-binding case-study-4-515318 \
    --member="serviceAccount:949473891513-compute@developer.gserviceaccount.com" \
    --role="roles/run.developer"

  gcloud projects add-iam-policy-binding case-study-4-515318 \
    --member="serviceAccount:949473891513-compute@developer.gserviceaccount.com" \
    --role="roles/run.admin"

  Adding GitHub Actions to the service account:
  gcloud iam service-accounts add-iam-policy-binding \
    949473891513-compute@developer.gserviceaccount.com \
    --project=case-study-4-515318 \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/949473891513/locations/global/workloadIdentityPools/github-actions/attribute.repository/kellyheffernan/case_study_4"

4. After running into many issues with trying to use GitHub Actions to push the image to Docker Hub and then to Google Cloud, I switched to using Google Artifact Registry to store my Docker image in my Google Cloud project instead. Cloud Run can then grab it from there instead when the yml script is triggered.
  To create the repository: (us-central1-docker.pkg.dev/case-study-4-515318/case-study-4/recipe-chatbot)
  gcloud artifacts repositories create case-study-4 \
    --project=case-study-4-515318 \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker images for DS/CS 553 Case Study 4"
   
  To give my service account permissions to upload the Docker image to Google Artifact Repository:
  gcloud artifacts repositories add-iam-policy-binding case-study-4 \
    --project=case-study-4-515318 \
    --location=us-central1 \
    --member="serviceAccount:949473891513-compute@developer.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"

5. Then, I added my necessary GitHub repo variables for the GitHub Actions yml file to use to my Secrets and variables tab in this repo.
   These are the variables I used and their purpose:
    GCP_PROJECT_ID	    ID associated with our Google Cloud project.
    GCP_REGION	        Region we are using for Cloud Run.
    CLOUD_RUN_SERVICE	  Name of the Cloud Run service we are using. 
    WIF_PROVIDER	      Name of the Workload Identity Federation provider for authentication.
    GCP_SERVICE_ACCOUNT	Name of the the service account used by GitHub Actions for our container deployment.

7. Then, I created the GitHub Actions YML file. This is stored in this repo.
   
8. To run the GitHub Action, you have to click on the deploy workflow button. 
   
10. Finally, to delete the service, I run gcp_clean.sh in WSL. 

## Vertex AI Integration
We modified our application to use Google Cloud Vertex AI/Gemini Enterprise AI instead of HuggingFace like we had previously used.

1. First I had to enable Vertex AI API on my case study 4 project, I used this command in WSL:
    gcloud services enable aiplatform.googleapis.com --project=case-study-4-515318

2. I then created a Vertex/Gemini Enterprise AI Service Account specifcally for Vertex AI authentication:
     WSL: cs4-vertex-inference@case-study-4-515318.iam.gserviceaccount.com
     I then gave it the Vertex AI User IAM role in the GCP console so it would be allowed to authroize any incoming inference requests from our app.

3.  I modified my app.py file by:
    - removing the HuggingFace inference token button
    - I replaced my HuggingFace inference functions with Gemini/Vertex AI functions so it would route prompts to Gemini instead
    - I added google-genai and google-auth as package dependencies
    - I added in my relevant Google Cloud/Google Project variables
    - I added in a section to validate JSON credentials if they were provided (for AWS and Azure integration) with os.getenv()
    - Otherwise, the application defaults to the Vertex service account for authenticating on the GCP container.

4. I also updated gcp_build_and_start.sh and gcp_deploy.YML to support using Vertex AI/Gemini Enterprise AI as the inference provider instead.
5. For GitHub Actions specifically, I had to use this gcloud IAM command to get GitHub to work with the Vertex Service Account:
    gcloud iam service-accounts add-iam-policy-binding \
      cs4-vertex-inference@case-study-4-515318.iam.gserviceaccount.com \
      --project=case-study-4-515318 \
      --member="serviceAccount:949473891513-compute@developer.gserviceaccount.com" \
      --role="roles/iam.serviceAccountUser"
