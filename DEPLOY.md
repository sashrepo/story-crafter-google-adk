# Deploying Story Crafter ADK to Google Cloud

This guide outlines how to deploy the Story Crafter application to Google Cloud Run. This setup ensures your agentic application runs in a scalable, serverless environment.

## Prerequisites

1.  **Google Cloud Project**: Create or select a project in the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Billing Enabled**: Ensure billing is enabled for your project.
3.  **gcloud CLI**: Install and configure the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install).
4.  **APIs Enabled**: Enable the following APIs:
    *   Cloud Run API: `run.googleapis.com`
    *   Artifact Registry API: `artifactregistry.googleapis.com`
    *   Vertex AI API: `aiplatform.googleapis.com` (for the agents)

    ```bash
    gcloud services enable run.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com
    ```

## Deployment Steps

### 1. Set up Environment Variables

You will need your Google API Key for the agents to function.

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_API_KEY="your-gemini-api-key"
```

### 2. Build and Submit the Container

We will use Google Cloud Build to build the Docker image and store it in the Container Registry (or Artifact Registry).

```bash
# Submit the build
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/story-crafter-adk
```

*Note: If you prefer Artifact Registry, create a repository first and adjust the tag accordingly (e.g., `us-central1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/repo-name/story-crafter-adk`).*

### 3. Deploy to Cloud Run

Deploy the container to Cloud Run. We need to pass the `GOOGLE_API_KEY` as an environment variable.

```bash
gcloud run deploy story-crafter-adk \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/story-crafter-adk \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY \
  --memory 2Gi
```

*   `--allow-unauthenticated`: Makes the web app publicly accessible. Remove this flag if you want to restrict access.
*   `--memory 2Gi`: Increases memory as agentic workflows can be memory-intensive.
*   `--region`: Choose a region close to you (e.g., `us-central1`).

### 4. Access the Application

Once the deployment finishes, `gcloud` will output a Service URL. Open that URL in your browser to start crafting stories!

## Continuous Deployment (Optional)

You can set up continuous deployment from GitHub:

1.  Go to the [Cloud Run Console](https://console.cloud.google.com/run).
2.  Click "Create Service".
3.  Select "Continuously deploy new revisions from a source repository".
4.  Connect your GitHub repository.
5.  Select "Dockerfile" as the build type.

## Troubleshooting

*   **503 Service Unavailable**: Check the logs in the Cloud Run console. It might be a startup timeout or error.
*   **API Key Error**: Ensure the `GOOGLE_API_KEY` environment variable is correctly set in the Cloud Run service revision.

