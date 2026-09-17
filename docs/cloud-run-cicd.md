# GitHub Actions to Cloud Run demo

This demo deliberately deploys only the database-independent `/health` route. The existing Docker Compose setup still starts MySQL and initializes its tables for local development. A production Cloud Run deployment should connect the API to Cloud SQL in a separate follow-up.

## What runs automatically

- `.github/workflows/ci.yml` runs tests and builds the Docker image for pull requests and pushes to `main` or `gcp-deploy`.
- `.github/workflows/deploy.yml` is initially manual. It repeats the tests, builds and pushes an image tagged with the Git commit SHA, deploys that exact image to Cloud Run, and verifies `/health`.
- Authentication uses GitHub OIDC and Google Workload Identity Federation. No service-account JSON key is stored in GitHub.

## 1. Validate locally

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
pytest --quiet
docker build -t user-api-mysql:local .
docker run --rm -p 8080:8080 user-api-mysql:local
curl http://localhost:8080/health
```

The expected response is `{"status":"ok"}`.

## 2. Create the Google Cloud resources

Install and authenticate the Google Cloud CLI, select a billable personal project, then run:

```bash
gcloud auth login
gcloud auth application-default login
./scripts/setup-gcp.sh YOUR_PROJECT_ID australia-southeast1 wxyw7813-alt/fastapi-user-crud
```

The script enables the required APIs and creates:

- an Artifact Registry Docker repository named `cloud-run-demo`;
- a least-purpose deployment service account;
- a separate Cloud Run runtime service account;
- a GitHub-specific Workload Identity Pool and provider;
- the required IAM bindings.

Project-level roles used by the deployer are `Artifact Registry Writer` and `Cloud Run Admin`. It receives `Service Account User` only on the runtime service account.

## 3. Add GitHub repository variables

Copy the seven values printed by `setup-gcp.sh` into **GitHub repository > Settings > Secrets and variables > Actions > Variables**. They are configuration identifiers, not passwords:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCP_ARTIFACT_REPOSITORY`
- `CLOUD_RUN_SERVICE`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_DEPLOY_SERVICE_ACCOUNT`
- `CLOUD_RUN_RUNTIME_SERVICE_ACCOUNT`

If the GitHub CLI is authenticated, each can also be set with:

```bash
gh variable set VARIABLE_NAME --body "VALUE"
```

## 4. Run and verify

1. Commit and push this branch.
2. Open the repository's **Actions** page and confirm the `CI` workflow passes.
3. Select **Deploy to Cloud Run**, choose **Run workflow**, and run it from `gcp-deploy`.
4. Open the deployment job summary or the Cloud Run console to find the service URL.
5. Verify `SERVICE_URL/health` returns `{"status":"ok"}`.

After the manual deployment is stable, automatic deployment can be enabled by adding a `push` trigger for the chosen deployment branch to `deploy.yml`. Keep pull requests CI-only.

## Troubleshooting

- `Permission denied to impersonate Service Account`: wait several minutes for IAM propagation and verify the repository name and full provider resource name.
- `Unauthenticated request`: verify the deploy step completed with `--allow-unauthenticated` and that organization policy permits public Cloud Run services.
- container startup failure: verify the image listens on the Cloud Run-provided `PORT`; this Dockerfile defaults to `8080`.
- database endpoints fail: expected in phase one. `/health` intentionally avoids MySQL. Configure Cloud SQL before treating the CRUD endpoints as deployed functionality.
