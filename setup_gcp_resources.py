import os
import argparse
from google.cloud import aiplatform
from google.api_core import exceptions

def setup_agent_engine(project_id, location):
    print(f"🚀 Setting up Agent Engine (Reasoning Engine) for project {project_id} in {location}...")
    
    try:
        # Initialize Vertex AI SDK
        aiplatform.init(project=project_id, location=location)
        
        # Create the Reasoning Engine Service Client (formerly/internally referred to as Agent Engine)
        client = aiplatform.gapic.ReasoningEngineServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )
        
        parent = f"projects/{project_id}/locations/{location}"
        
        print("Creating Reasoning Engine... (this may take a minute)")
        
        # Configure the Reasoning Engine
        # We are creating a default/empty one as a placeholder for the Memory Bank to attach to.
        # In some contexts, the Memory Bank might need to be explicitly created or attached here.
        # However, the ADK's VertexAiMemoryBankService expects an 'agent_engine_id'.
        # We will create a basic Reasoning Engine.
        
        reasoning_engine = {
            "display_name": "Story Crafter Memory Bank",
            "description": "Storage for Story Crafter ADK Memory"
        }

        operation = client.create_reasoning_engine(
            parent=parent,
            reasoning_engine=reasoning_engine
        )
        
        print("Waiting for operation to complete...")
        result = operation.result()
        name = result.name
            
        engine_id = name.split("/")[-1]
        
        print("\n✅ Reasoning Engine Created Successfully!")
        print(f"Resource Name: {name}")
        print(f"\n📢 COPY THIS ID FOR YOUR CONFIGURATION:")
        print(f"VERTEX_AGENT_ENGINE_ID={engine_id}")
        print("\nAdd this to your .env file or deployment variables.")
        
    except exceptions.PermissionDenied:
        print("\n❌ Permission Denied. Please ensure you have 'Vertex AI Administrator' or 'Vertex AI User' role.")
        print(f"Run: gcloud projects add-iam-policy-binding {project_id} --member='user:YOUR_EMAIL' --role='roles/aiplatform.admin'")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Vertex AI Agent Engine")
    parser.add_argument("--project", required=True, help="Google Cloud Project ID")
    parser.add_argument("--location", default="us-central1", help="Google Cloud Region (default: us-central1)")
    
    args = parser.parse_args()
    setup_agent_engine(args.project, args.location)

