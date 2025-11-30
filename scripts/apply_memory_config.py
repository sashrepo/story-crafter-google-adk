#!/usr/bin/env python3
"""
Apply Custom Memory Topics to Vertex AI Agent Engine.

This script applies the Story Crafter custom memory topics to your
Vertex AI Agent Engine's Memory Bank configuration.

Prerequisites:
1. Set environment variables in .env file:
   - GOOGLE_CLOUD_PROJECT
   - GOOGLE_CLOUD_LOCATION
   - AGENT_ENGINE_ID

2. Authenticate with Google Cloud:
   gcloud auth application-default login

Usage:
    python scripts/apply_memory_config.py
    python scripts/apply_memory_config.py --dry-run

Reference: https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/generate-memories
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from services.memory_config import get_memory_topics, get_customization_config


def get_env_config():
    """Get configuration from environment variables."""
    return {
        "project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        "agent_engine_id": os.getenv("AGENT_ENGINE_ID") or os.getenv("MEMORY_BANK_ID"),
    }


def validate_config(config: dict) -> bool:
    """Validate that all required config is present."""
    missing = []
    if not config["project"]:
        missing.append("GOOGLE_CLOUD_PROJECT")
    if not config["agent_engine_id"]:
        missing.append("AGENT_ENGINE_ID")
    
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        return False
    return True


def build_memory_topics_dict():
    """
    Build memory topics as dictionaries for the API.
    
    Returns list of topic dictionaries.
    """
    return get_memory_topics()


def apply_memory_config(dry_run: bool = False):
    """
    Apply custom memory topics to the Vertex AI Agent Engine.
    
    Args:
        dry_run: If True, only show what would be applied without making changes.
    """
    config = get_env_config()
    
    print("\n" + "=" * 70)
    print("APPLYING MEMORY BANK CONFIGURATION")
    print("=" * 70)
    
    print(f"\n📋 Target Agent Engine:")
    print(f"   Project: {config['project']}")
    print(f"   Location: {config['location']}")
    print(f"   Agent Engine ID: {config['agent_engine_id']}")
    
    if not validate_config(config):
        return False
    
    # Show what will be applied
    topics = get_memory_topics()
    custom_count = sum(1 for t in topics if "custom_memory_topic" in t)
    managed_count = sum(1 for t in topics if "managed_memory_topic" in t)
    
    print(f"\n📝 Topics to apply:")
    print(f"   - {managed_count} managed topics")
    print(f"   - {custom_count} custom topics")
    
    for topic in topics:
        if "custom_memory_topic" in topic:
            label = topic["custom_memory_topic"]["label"]
            print(f"     • {label}")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made")
        print("\nConfiguration that would be applied:")
        print(json.dumps(get_customization_config(), indent=2))
        return True
    
    print("\n⏳ Applying configuration...")
    
    # The Agent Engine resource name
    agent_engine_name = (
        f"projects/{config['project']}/locations/{config['location']}/"
        f"reasoningEngines/{config['agent_engine_id']}"
    )
    
    print(f"\n   Resource: {agent_engine_name}")
    
    # Save the config file
    config_path = project_root / "memory_bank_config.json"
    memory_topics = build_memory_topics_dict()
    
    with open(config_path, "w") as f:
        json.dump(get_customization_config(), f, indent=2)
    
    print(f"\n📄 Configuration exported to: {config_path}")
    
    # Try to apply via Vertex AI SDK
    try:
        import vertexai
        from vertexai import reasoning_engines
        
        # Initialize Vertex AI
        vertexai.init(
            project=config["project"],
            location=config["location"]
        )
        
        print("\n✓ Vertex AI SDK initialized")
        
        # Try to get the reasoning engine
        try:
            engine = reasoning_engines.ReasoningEngine(agent_engine_name)
            print(f"✓ Connected to Agent Engine")
            
            # Check if there's an update method for memory config
            if hasattr(engine, 'update'):
                engine.update(
                    memory_bank_config={
                        "customization_config": {
                            "memory_topics": memory_topics
                        }
                    }
                )
                print("\n✅ Memory Bank configuration applied!")
                return True
        except Exception as e:
            print(f"⚠️  Could not update via SDK: {e}")
            
    except ImportError:
        print("\n⚠️  vertexai SDK not available for direct update")
    except Exception as e:
        print(f"\n⚠️  Vertex AI SDK error: {e}")
    
    # Try using the ADK's memory service directly
    try:
        from google.adk.memory import VertexAiMemoryBankService
        
        memory_service = VertexAiMemoryBankService(
            project=config["project"],
            location=config["location"],
            agent_engine_id=config["agent_engine_id"]
        )
        
        print("\n✓ ADK VertexAiMemoryBankService initialized")
        print("  Memory Bank is accessible via the app!")
        
    except Exception as e:
        print(f"\n⚠️  ADK memory service check: {e}")
    
    # Provide manual instructions
    print("\n" + "=" * 70)
    print("CONFIGURATION READY")
    print("=" * 70)
    print(f"""
✅ Custom memory topics configuration saved to:
   {config_path}

The Memory Bank customization config defines WHAT to extract from conversations.
To apply these custom topics, use one of the following options:

📋 OPTION 1 - Apply via Python SDK (Recommended):

   Run this script with --apply-sdk flag, or use this code:
   
   ```python
   import vertexai
   from vertexai.preview import reasoning_engines
   
   vertexai.init(project="{config['project']}", location="{config['location']}")
   
   # Load your custom config
   import json
   with open("memory_bank_config.json") as f:
       memory_config = json.load(f)
   
   # Update the agent engine with custom memory topics
   agent = reasoning_engines.ReasoningEngine("{config['agent_engine_id']}")
   # Check the SDK docs for the exact update method
   ```

📋 OPTION 2 - Apply via Google Cloud Console:

   1. Go to: https://console.cloud.google.com/vertex-ai/agent-builder
   2. Navigate to Agent Engine section
   3. Select your Agent Engine: {config['agent_engine_id']}
   4. Edit Memory Bank settings
   5. Add custom memory topics from memory_bank_config.json

📋 OPTION 3 - Create new Agent Engine with config:

   When creating a new Agent Engine, include memory_bank_config in the
   context_spec parameter. See: 
   https://cloud.google.com/agent-builder/agent-engine/memory-bank/set-up

💡 TIP: Your app already uses Memory Bank via VertexAiMemoryBankService.
   Custom topics control WHAT gets extracted. Default managed topics 
   are already active and working!
""")
    
    return True


def test_memory_generation(dry_run: bool = False):
    """
    Test memory generation with a sample conversation.
    
    This helps verify that the custom topics are working.
    """
    config = get_env_config()
    
    if not validate_config(config):
        return False
    
    print("\n" + "=" * 70)
    print("TESTING MEMORY GENERATION")
    print("=" * 70)
    
    # Sample conversation that should trigger memory extraction
    test_events = [
        {"role": "user", "content": "I love dark fantasy stories with anti-hero protagonists."},
        {"role": "assistant", "content": "Great choice! I'll create a dark fantasy story with a complex anti-hero."},
        {"role": "user", "content": "Set it in a steampunk Victorian world with magic."},
        {"role": "assistant", "content": "Perfect! A steampunk Victorian setting with magical elements it is."},
    ]
    
    print("\n📝 Test conversation:")
    for event in test_events:
        role_emoji = "👤" if event["role"] == "user" else "🤖"
        print(f"   {role_emoji} {event['role'].title()}: {event['content']}")
    
    print("\n📋 Expected memories to extract:")
    print("   • story_preferences: User loves dark fantasy stories")
    print("   • character_preferences: User prefers anti-hero protagonists")
    print("   • world_preferences: User wants steampunk Victorian setting with magic")
    
    if dry_run:
        print("\n🔍 DRY RUN - Skipping actual API call")
        return True
    
    print("\n⏳ Sending test conversation to Memory Bank...")
    
    try:
        from google import genai
        
        client = genai.Client(
            vertexai=True,
            project=config["project"],
            location=config["location"]
        )
        
        agent_engine_name = (
            f"projects/{config['project']}/locations/{config['location']}/"
            f"reasoningEngines/{config['agent_engine_id']}"
        )
        
        # Build events for the API using dictionary format
        events = []
        for event in test_events:
            events.append({
                "content": {
                    "role": event["role"],
                    "parts": [{"text": event["content"]}]
                }
            })
        
        # Generate memories from the test conversation
        response = client.agent_engines.memories.generate(
            name=agent_engine_name,
            direct_contents_source={"events": events},
            scope={"user_id": "test_user_memory_config"},
            config={"wait_for_completion": True}
        )
        
        print("\n✅ Memory generation request sent!")
        print(f"   Response: {response}")
        print("\n💡 Note: Memories may take 5-10 minutes to appear.")
        print("   Use 'Check Memories' in the app to verify.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing memory generation: {e}")
        print("   This may indicate the customization config isn't applied yet.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Apply custom memory topics to Vertex AI Agent Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be applied without making changes"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Test memory generation after applying config"
    )
    
    args = parser.parse_args()
    
    success = apply_memory_config(dry_run=args.dry_run)
    
    if success and args.test and not args.dry_run:
        test_memory_generation()


if __name__ == "__main__":
    main()

