# Vertex AI Memory Bank Integration Guide

This document explains how to set up and use Vertex AI Memory Bank and Session Service for persistent, long-term storage in Story Crafter.

## Overview

Story Crafter supports two storage modes:

1. **In-Memory (Default)**: Fast, but sessions are lost on app restart. Good for development and testing.
2. **Vertex AI Memory Bank**: Persistent storage backed by Google Cloud. Sessions survive restarts, supports multiple users, and provides long-term memory.

## Architecture

The integration uses two key services:

- **VertexAiSessionService**: Manages conversation history and agent interactions
- **VertexAiMemoryBankService**: Stores long-term memory about story elements, characters, and worlds

The system automatically detects configuration and falls back to in-memory storage if Vertex AI is not configured.

## Prerequisites

Before enabling Vertex AI integration, you need:

1. **Google Cloud Platform Account** with billing enabled
2. **GCP Project** with the following APIs enabled:
   - Vertex AI API (`aiplatform.googleapis.com`)
   - Vertex AI Agent Builder API
3. **Vertex AI Agent Engine** created in your project
4. **Authentication** set up (Application Default Credentials or Service Account)

## Setup Instructions

### Step 1: Enable Required APIs

```bash
# Set your project ID
export GCP_PROJECT="your-project-id"
gcloud config set project $GCP_PROJECT

# Enable Vertex AI APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

### Step 2: Set Up Authentication

Choose one of the following methods:

#### Option A: Application Default Credentials (Development)
```bash
gcloud auth application-default login
```

#### Option B: Service Account (Production)
```bash
# Create a service account
gcloud iam service-accounts create story-crafter-sa \
  --display-name="Story Crafter Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:story-crafter-sa@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create ~/story-crafter-key.json \
  --iam-account=story-crafter-sa@$GCP_PROJECT.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/story-crafter-key.json
```

### Step 3: Create Vertex AI Agent Engine

You can create an Agent Engine through the GCP Console or using the helper script:

#### Using GCP Console:
1. Go to [Vertex AI Agent Builder](https://console.cloud.google.com/gen-app-builder/engines)
2. Click "Create App" or "Create Engine"
3. Choose "Agent" type
4. Note the Engine ID (format: `projects/{project}/locations/{location}/engines/{engine-id}`)

#### Using the Helper Script:
```bash
# Run the setup script (if available in your project)
python setup_gcp_resources.py
```

### Step 4: Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your configuration:
```bash
# Required for basic functionality
GOOGLE_API_KEY=your-google-api-key-here

# Required for Vertex AI Memory Bank
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_AGENT_ENGINE_ID=your-agent-engine-id
```

### Step 5: Verify Configuration

Run the application and check the startup logs:

```bash
streamlit run app.py
```

You should see:
```
Initializing Vertex AI Session Service (Project: your-project, Engine: your-engine-id)
Initializing Vertex AI Memory Bank (Project: your-project, Engine: your-engine-id)
```

If Vertex AI is not configured, you'll see:
```
VERTEX_AGENT_ENGINE_ID not set. Falling back to InMemorySessionService.
VERTEX_AGENT_ENGINE_ID not set. Falling back to InMemoryMemoryService.
```

## How It Works

### Session Management

The `VertexAiSessionService` automatically:
- Creates and retrieves sessions based on `user_id` and `session_id`
- Persists conversation history across app restarts
- Isolates sessions per user for multi-tenant support

### Memory Bank

The `VertexAiMemoryBankService` provides:
- Long-term storage of story elements, characters, and world details
- Contextual retrieval of relevant information during story generation
- Automatic indexing and search capabilities

### Code Integration

The integration is transparent to the rest of the application:

```python
# services/memory.py
@st.cache_resource
def get_session_service():
    """Automatically selects Vertex AI or InMemory based on config."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    agent_engine_id = os.environ.get("VERTEX_AGENT_ENGINE_ID")
    
    if project_id and agent_engine_id:
        return VertexAiSessionService(
            project=project_id,
            location=location,
            agent_engine_id=agent_engine_id
        )
    
    return InMemorySessionService()
```

## Benefits of Vertex AI Integration

✅ **Persistence**: Sessions survive app restarts and server crashes  
✅ **Scalability**: Automatic scaling handled by Google Cloud  
✅ **Multi-User**: Built-in user isolation and session management  
✅ **Long-Term Memory**: Story elements persist across conversations  
✅ **Search & Retrieval**: Efficient querying of historical context  
✅ **Reliability**: Enterprise-grade infrastructure and backups  

## Cost Considerations

Vertex AI Memory Bank usage incurs charges based on:
- Storage: Per GB per month
- API calls: Per request
- Agent Engine: Compute time

For development/testing, in-memory mode is recommended. For production with multiple users, Vertex AI provides better value and reliability.

See [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing) for details.

## Troubleshooting

### "Permission Denied" Errors
- Verify your service account has `roles/aiplatform.user` role
- Check that Application Default Credentials are set correctly
- Ensure the project ID matches your configuration

### "Agent Engine Not Found"
- Verify the `VERTEX_AGENT_ENGINE_ID` is correct
- Ensure the engine exists in the specified project and location
- Check the engine ID format: should be just the ID, not the full resource name

### Sessions Not Persisting
- Verify all three environment variables are set: `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `VERTEX_AGENT_ENGINE_ID`
- Check the startup logs to confirm Vertex AI services are initialized
- Test authentication with: `gcloud auth application-default print-access-token`

### Slow Response Times
- Vertex AI adds network latency compared to in-memory storage
- Consider using in-memory mode for development
- Check your GCP region - use the closest location to your users

## Migration from In-Memory

If you're switching from in-memory to Vertex AI:

1. Existing sessions will be lost (they were in RAM)
2. Set up the environment variables as described above
3. Restart the application
4. New sessions will be created in Vertex AI

No code changes are needed - the switch is purely configuration-based.

## Security Best Practices

1. **Never commit** `.env` files or service account keys to version control
2. Use **Secret Manager** for production deployments
3. **Rotate** service account keys regularly
4. Apply **principle of least privilege** to IAM roles
5. Use **VPC Service Controls** for additional security in enterprise environments

## Further Reading

- [Vertex AI Agent Builder Documentation](https://cloud.google.com/vertex-ai/docs/agents/overview)
- [Google ADK Documentation](https://ai.google.dev/gemini-api/docs/adk)
- [Vertex AI Memory Bank Guide](https://cloud.google.com/vertex-ai/docs/generative-ai/memory-bank)
- [GCP Authentication Best Practices](https://cloud.google.com/docs/authentication/best-practices-applications)

## Support

For issues specific to:
- **Story Crafter**: Open an issue in the project repository
- **Vertex AI**: See [GCP Support](https://cloud.google.com/support)
- **Google ADK**: Check [ADK Documentation](https://ai.google.dev/gemini-api/docs/adk)

