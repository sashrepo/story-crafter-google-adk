#!/usr/bin/env python3
"""
Memory Bank Setup Script for Story Crafter.

This script helps you configure Memory Bank with custom memory topics
for the Story Crafter application.

Prerequisites:
1. Set environment variables in .env file or shell:
   - GOOGLE_CLOUD_PROJECT: Your GCP project ID
   - GOOGLE_CLOUD_LOCATION: Region (e.g., us-central1)
   - AGENT_ENGINE_ID: Your Vertex AI Agent Engine ID

2. Authenticate with Google Cloud:
   gcloud auth application-default login

Usage:
    python scripts/setup_memory_bank.py --show-topics
    python scripts/setup_memory_bank.py --setup
    python scripts/setup_memory_bank.py --verify

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

from services.memory_config import (
    get_memory_topics,
    get_customization_config,
    STORY_CONTENT_TOPIC,
)


def get_env_config():
    """Get configuration from environment variables."""
    return {
        "project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        "agent_engine_id": os.getenv("AGENT_ENGINE_ID") or os.getenv("MEMORY_BANK_ID"),
    }


def show_topics():
    """Display all configured memory topics."""
    print("\n" + "=" * 70)
    print("STORY CRAFTER - CUSTOM MEMORY TOPICS")
    print("=" * 70)
    
    topics = get_memory_topics()
    
    print(f"\nTotal topics configured: {len(topics)}")
    print("-" * 70)
    
    for i, topic in enumerate(topics, 1):
        if "managed_memory_topic" in topic:
            enum = topic["managed_memory_topic"]["managed_topic_enum"]
            print(f"\n{i}. [MANAGED] {enum}")
            print("   Pre-defined by Google Cloud Memory Bank")
        elif "custom_memory_topic" in topic:
            custom = topic["custom_memory_topic"]
            print(f"\n{i}. [CUSTOM] {custom['label']}")
            print(f"   Description: {custom['description'][:200]}...")
    
    print("\n" + "-" * 70)
    print("\nFull JSON configuration:")
    print("-" * 70)
    print(json.dumps(get_customization_config(), indent=2))


def show_setup_instructions():
    """Display setup instructions for Memory Bank."""
    config = get_env_config()
    
    print("\n" + "=" * 70)
    print("MEMORY BANK SETUP INSTRUCTIONS")
    print("=" * 70)
    
    print("\n📋 STEP 1: Verify Environment Configuration")
    print("-" * 70)
    print(f"   GOOGLE_CLOUD_PROJECT: {config['project'] or '❌ NOT SET'}")
    print(f"   GOOGLE_CLOUD_LOCATION: {config['location']}")
    print(f"   AGENT_ENGINE_ID: {config['agent_engine_id'] or '❌ NOT SET'}")
    
    if not config['project'] or not config['agent_engine_id']:
        print("\n   ⚠️  Missing required environment variables!")
        print("   Set them in your .env file or export them:")
        print("   export GOOGLE_CLOUD_PROJECT=your-project-id")
        print("   export AGENT_ENGINE_ID=your-agent-engine-id")
    
    print("\n📋 STEP 2: Set Up Memory Bank via Vertex AI SDK")
    print("-" * 70)
    print("""
   Memory Bank customization is configured at the Agent Engine level.
   Use the following Python code to set up your Memory Bank:

   ```python
   from google import genai
   from vertexai.types import (
       MemoryBankCustomizationConfig,
       MemoryBankCustomizationConfigMemoryTopic as MemoryTopic,
       MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic as CustomMemoryTopic,
   )

   # Initialize the client
   client = genai.Client(
       vertexai=True,
       project="{project}",
       location="{location}"
   )

   # Define custom topics (see services/memory_config.py for full definitions)
   custom_topics = [
       MemoryTopic(
           custom_memory_topic=CustomMemoryTopic(
               label="story_preferences",
               description="User preferences about story creation..."
           )
       ),
       # ... add other topics
   ]

   # Apply to your Agent Engine
   # (Consult latest Vertex AI SDK docs for exact API)
   ```
""".format(**config))

    print("\n📋 STEP 3: Verify Memory Extraction")
    print("-" * 70)
    print("""
   After setting up, test memory extraction:

   1. Start the Story Crafter app:
      streamlit run app.py

   2. Create a story with explicit preferences:
      "I want a dark fantasy story with dragons and an anti-hero protagonist"

   3. Check if memories were created (may take 5-10 minutes):
      - Click "🔍 Check Memories" in the sidebar
      - Or use the Vertex AI Console to inspect memories

   4. In subsequent sessions, memories should be retrieved and applied.
""")

    print("\n📋 STEP 4: Monitor Memory Generation")
    print("-" * 70)
    print("""
   Memory Bank provides APIs to inspect generated memories:

   ```python
   # List memories for a user
   memories = client.agent_engines.memories.list(
       name="projects/{project}/locations/{location}/reasoningEngines/{agent_engine_id}",
       scope={{"user_id": "your-user-id"}}
   )

   # Inspect memory revisions (extraction + consolidation steps)
   revisions = client.agent_engines.memories.revisions.list(
       name="projects/.../memories/.../revisions/..."
   )
   ```
""".format(**config))


def verify_setup():
    """Verify Memory Bank configuration."""
    config = get_env_config()
    
    print("\n" + "=" * 70)
    print("VERIFYING MEMORY BANK SETUP")
    print("=" * 70)
    
    errors = []
    warnings = []
    
    # Check environment
    if not config['project']:
        errors.append("GOOGLE_CLOUD_PROJECT not set")
    if not config['agent_engine_id']:
        errors.append("AGENT_ENGINE_ID not set")
    
    # Check topic configuration
    topics = get_memory_topics()
    custom_topics = [t for t in topics if "custom_memory_topic" in t]
    managed_topics = [t for t in topics if "managed_memory_topic" in t]
    
    print(f"\n✓ Found {len(custom_topics)} custom topics")
    print(f"✓ Found {len(managed_topics)} managed topics")
    
    # Validate topic structure
    for topic in custom_topics:
        custom = topic.get("custom_memory_topic", {})
        if not custom.get("label"):
            errors.append(f"Custom topic missing 'label'")
        if not custom.get("description"):
            warnings.append(f"Custom topic '{custom.get('label', 'unknown')}' has no description")
        elif len(custom.get("description", "")) < 50:
            warnings.append(f"Custom topic '{custom.get('label')}' has a short description (< 50 chars)")
    
    # Print results
    if errors:
        print("\n❌ ERRORS:")
        for err in errors:
            print(f"   - {err}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warn in warnings:
            print(f"   - {warn}")
    
    if not errors and not warnings:
        print("\n✅ All checks passed!")
    elif not errors:
        print("\n✅ Configuration valid (with warnings)")
    else:
        print("\n❌ Please fix errors before proceeding")
        return False
    
    return True


def generate_api_payload():
    """Generate the API payload for Memory Bank setup."""
    config = get_customization_config()
    
    print("\n" + "=" * 70)
    print("API PAYLOAD FOR MEMORY BANK CONFIGURATION")
    print("=" * 70)
    print("\nUse this JSON payload when configuring Memory Bank via API:\n")
    print(json.dumps(config, indent=2))
    
    # Also save to file
    output_path = project_root / "memory_bank_config.json"
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\n✓ Saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Memory Bank Setup Script for Story Crafter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_memory_bank.py --show-topics
  python scripts/setup_memory_bank.py --setup
  python scripts/setup_memory_bank.py --verify
  python scripts/setup_memory_bank.py --export
        """
    )
    
    parser.add_argument(
        "--show-topics", "-t",
        action="store_true",
        help="Display all configured memory topics"
    )
    parser.add_argument(
        "--setup", "-s",
        action="store_true",
        help="Show detailed setup instructions"
    )
    parser.add_argument(
        "--verify", "-v",
        action="store_true",
        help="Verify Memory Bank configuration"
    )
    parser.add_argument(
        "--export", "-e",
        action="store_true",
        help="Export configuration as JSON file"
    )
    
    args = parser.parse_args()
    
    if not any([args.show_topics, args.setup, args.verify, args.export]):
        # Default: show everything
        show_topics()
        show_setup_instructions()
        verify_setup()
    else:
        if args.show_topics:
            show_topics()
        if args.setup:
            show_setup_instructions()
        if args.verify:
            verify_setup()
        if args.export:
            generate_api_payload()


if __name__ == "__main__":
    main()

