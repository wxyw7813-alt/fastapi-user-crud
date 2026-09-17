#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: $0 PROJECT_ID [REGION] [GITHUB_OWNER/REPOSITORY]" >&2
  exit 2
fi

PROJECT_ID="$1"
REGION="${2:-australia-southeast1}"
GITHUB_REPOSITORY="${3:-wxyw7813-alt/fastapi-user-crud}"
ARTIFACT_REPOSITORY="cloud-run-demo"
CLOUD_RUN_SERVICE="fastapi-user-crud-demo"
DEPLOY_SERVICE_ACCOUNT_ID="github-cloud-run-deployer"
RUNTIME_SERVICE_ACCOUNT_ID="cloud-run-demo-runtime"
POOL_ID="github-actions"
PROVIDER_ID="fastapi-user-crud"

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
DEPLOY_SERVICE_ACCOUNT="${DEPLOY_SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
RUNTIME_SERVICE_ACCOUNT="${RUNTIME_SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud services enable \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  run.googleapis.com \
  sts.googleapis.com \
  --project "$PROJECT_ID"

if ! gcloud artifacts repositories list \
  --location "$REGION" \
  --project "$PROJECT_ID" \
  --filter "name:${ARTIFACT_REPOSITORY}" \
  --format 'value(name)' | grep -q .; then
  gcloud artifacts repositories create "$ARTIFACT_REPOSITORY" \
    --repository-format docker \
    --location "$REGION" \
    --description "Images for the Cloud Run CI/CD demo" \
    --project "$PROJECT_ID"
fi

for service_account_id in "$DEPLOY_SERVICE_ACCOUNT_ID" "$RUNTIME_SERVICE_ACCOUNT_ID"; do
  if ! gcloud iam service-accounts describe "${service_account_id}@${PROJECT_ID}.iam.gserviceaccount.com" --project "$PROJECT_ID" >/dev/null 2>&1; then
    gcloud iam service-accounts create "$service_account_id" --project "$PROJECT_ID"
  fi
done

for role in roles/artifactregistry.writer roles/run.admin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member "serviceAccount:${DEPLOY_SERVICE_ACCOUNT}" \
    --role "$role" \
    --condition None \
    --quiet
done

gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SERVICE_ACCOUNT" \
  --project "$PROJECT_ID" \
  --member "serviceAccount:${DEPLOY_SERVICE_ACCOUNT}" \
  --role roles/iam.serviceAccountUser \
  --quiet

if ! gcloud iam workload-identity-pools describe "$POOL_ID" --location global --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "$POOL_ID" \
    --location global \
    --display-name "GitHub Actions" \
    --project "$PROJECT_ID"
fi

if ! gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" --workload-identity-pool "$POOL_ID" --location global --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
    --workload-identity-pool "$POOL_ID" \
    --location global \
    --issuer-uri "https://token.actions.githubusercontent.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --attribute-condition "assertion.repository == '${GITHUB_REPOSITORY}'" \
    --project "$PROJECT_ID"
fi

gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SERVICE_ACCOUNT" \
  --project "$PROJECT_ID" \
  --member "principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${GITHUB_REPOSITORY}" \
  --role roles/iam.workloadIdentityUser \
  --quiet

WORKLOAD_IDENTITY_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"

cat <<EOF

GCP setup complete. Add these GitHub repository variables:

GCP_PROJECT_ID=${PROJECT_ID}
GCP_REGION=${REGION}
GCP_ARTIFACT_REPOSITORY=${ARTIFACT_REPOSITORY}
CLOUD_RUN_SERVICE=${CLOUD_RUN_SERVICE}
GCP_WORKLOAD_IDENTITY_PROVIDER=${WORKLOAD_IDENTITY_PROVIDER}
GCP_DEPLOY_SERVICE_ACCOUNT=${DEPLOY_SERVICE_ACCOUNT}
CLOUD_RUN_RUNTIME_SERVICE_ACCOUNT=${RUNTIME_SERVICE_ACCOUNT}
EOF
