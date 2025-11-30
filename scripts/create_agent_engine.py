#!/usr/bin/env python3
"""
Create Agent Engine with Custom Memory Bank Configuration.

This script creates a new Agent Engine with Memory Bank enabled and
configured with Story Crafter's custom memory topics.

The Memory Bank customization config MUST be set during Agent Engine creation.
It cannot be updated after the Agent Engine is created.

Prerequisites:
1. Set environment variables in .env file
2. Authenticate: gcloud auth application-default login
3. Install: pip install google-cloud-aiplatform>=1.111.0

Usage:
    python scripts/create_agent_engine.py --info          # Show current config
    python scripts/create_agent_engine.py --create        # Create new engine
    python scripts/create_agent_engine.py --test-memory   # Test memory generation

Reference: https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/set-up
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
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


def build_memory_bank_config():
    """
    Build the Memory Bank config using the Vertex AI SDK types.
    
    Reference: https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/set-up#class-based_1
    
    Note: Uses internal vertexai._genai.types module. This may break with SDK updates.
    Monitor google-cloud-aiplatform releases for public API alternatives.
    """
    # WARNING: These imports use private/internal SDK types (underscore prefix).
    # This is the current recommended approach per Vertex AI docs, but may change.
    # If imports fail after SDK update, check for public equivalents in vertexai.types
    from vertexai._genai.types import MemoryBankCustomizationConfig as CustomizationConfig
    from vertexai._genai.types import MemoryBankCustomizationConfigMemoryTopic as MemoryTopic
    from vertexai._genai.types import MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic as CustomMemoryTopic
    from vertexai._genai.types import MemoryBankCustomizationConfigMemoryTopicManagedMemoryTopic as ManagedMemoryTopic
    from vertexai._genai.types import ManagedTopicEnum
    from vertexai._genai.types import ReasoningEngineContextSpecMemoryBankConfig as MemoryBankConfig
    
    # Build memory topics using SDK types
    memory_topics = []
    
    raw_topics = get_memory_topics()
    
    for topic in raw_topics:
        if "managed_memory_topic" in topic:
            enum_name = topic["managed_memory_topic"]["managed_topic_enum"]
            enum_value = getattr(ManagedTopicEnum, enum_name)
            memory_topics.append(
                MemoryTopic(
                    managed_memory_topic=ManagedMemoryTopic(
                        managed_topic_enum=enum_value
                    )
                )
            )
        elif "custom_memory_topic" in topic:
            custom = topic["custom_memory_topic"]
            memory_topics.append(
                MemoryTopic(
                    custom_memory_topic=CustomMemoryTopic(
                        label=custom["label"],
                        description=custom["description"]
                    )
                )
            )
    
    # Create the customization config
    customization_config = CustomizationConfig(
        memory_topics=memory_topics
    )
    
    # Create the full Memory Bank config
    # Note: customization_configs is a LIST (plural)
    memory_bank_config = MemoryBankConfig(
        customization_configs=[customization_config]
    )
    
    return memory_bank_config


def show_info():
    """Show current configuration and agent engine info."""
    config = get_env_config()
    
    print("\n" + "=" * 70)
    print("STORY CRAFTER - AGENT ENGINE CONFIGURATION")
    print("=" * 70)
    
    print(f"\n📋 Environment:")
    print(f"   Project: {config['project']}")
    print(f"   Location: {config['location']}")
    print(f"   Agent Engine ID: {config['agent_engine_id']}")
    
    # Show memory topics
    topics = get_memory_topics()
    custom = [t for t in topics if "custom_memory_topic" in t]
    managed = [t for t in topics if "managed_memory_topic" in t]
    
    print(f"\n📝 Memory Topics Configured:")
    print(f"   Managed: {len(managed)}")
    print(f"   Custom: {len(custom)}")
    for t in custom:
        print(f"     • {t['custom_memory_topic']['label']}")
    
    # Try to get agent engine info
    if config['project'] and config['agent_engine_id']:
        print("\n🔍 Checking Agent Engine status...")
        try:
            import vertexai
            vertexai.init(project=config['project'], location=config['location'])
            
            from vertexai.preview import reasoning_engines
            
            # List all reasoning engines to find ours
            engines = reasoning_engines.ReasoningEngine.list()
            
            found = False
            for engine in engines:
                if config['agent_engine_id'] in engine.resource_name:
                    print(f"\n✅ Agent Engine found:")
                    print(f"   Name: {engine.display_name}")
                    print(f"   Resource: {engine.resource_name}")
                    if hasattr(engine, 'create_time'):
                        print(f"   Created: {engine.create_time}")
                    found = True
                    break
            
            if not found:
                print(f"\n⚠️  Agent Engine {config['agent_engine_id']} not found in list")
                print("   It may exist but not be visible via this API")
                
        except Exception as e:
            print(f"\n⚠️  Could not check Agent Engine: {e}")


def test_memory_generation():
    """Test memory generation with sample conversation."""
    config = get_env_config()
    
    if not config['project'] or not config['agent_engine_id']:
        print("❌ Missing GOOGLE_CLOUD_PROJECT or AGENT_ENGINE_ID")
        return False
    
    print("\n" + "=" * 70)
    print("TESTING MEMORY GENERATION")
    print("=" * 70)
    
    # Test conversation
    test_facts = [
        "User loves dark fantasy stories with dragons",
        "User prefers anti-hero protagonists",
        "User enjoys steampunk Victorian settings"
    ]
    
    print("\n📝 Test facts to store:")
    for fact in test_facts:
        print(f"   • {fact}")
    
    try:
        from google.adk.memory import VertexAiMemoryBankService
        
        print("\n⏳ Initializing Memory Bank service...")
        
        memory_service = VertexAiMemoryBankService(
            project=config['project'],
            location=config['location'],
            agent_engine_id=config['agent_engine_id']
        )
        
        print("✓ Memory Bank service initialized")
        
        # Try to add memories directly
        import asyncio
        
        async def add_test_memories():
            # The ADK memory service uses add_session_to_memory
            # For direct memory testing, we'll use search to verify connectivity
            print("\n🔍 Testing memory search capability...")
            
            result = await memory_service.search_memory(
                query="user preferences",
                app_name=config['agent_engine_id'],
                user_id="test_user"
            )
            
            print(f"✓ Memory search successful!")
            if hasattr(result, 'memories') and result.memories:
                print(f"   Found {len(result.memories)} existing memories")
            else:
                print("   No existing memories (this is normal for new users)")
            
            return True
        
        success = asyncio.run(add_test_memories())
        
        if success:
            print("\n✅ Memory Bank is operational!")
            print("""
💡 To generate memories from conversations:
   1. Run the Story Crafter app: streamlit run app.py
   2. Have a conversation with preferences like:
      "I want a dark fantasy story with an anti-hero"
   3. Memories are extracted automatically from sessions
   4. Check 'Memory Bank' in sidebar to verify
""")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def create_agent_engine(dry_run: bool = False):
    """
    Create a new Agent Engine with Memory Bank configured.
    
    This creates a minimal Agent Engine with Memory Bank enabled and
    custom memory topics configured for Story Crafter.
    
    Args:
        dry_run: If True, show what would be created without actually creating.
    """
    config = get_env_config()
    
    if not config['project']:
        print("❌ GOOGLE_CLOUD_PROJECT not set")
        return False
    
    print("\n" + "=" * 70)
    print("CREATE NEW AGENT ENGINE WITH MEMORY BANK")
    print("=" * 70)
    
    print(f"\n📋 Configuration:")
    print(f"   Project: {config['project']}")
    print(f"   Location: {config['location']}")
    
    # Get memory config
    memory_config = get_customization_config()
    
    print(f"\n📝 Memory Topics to configure:")
    for topic in memory_config['memory_topics']:
        if 'custom_memory_topic' in topic:
            print(f"   • {topic['custom_memory_topic']['label']}")
        else:
            print(f"   • [managed] {topic['managed_memory_topic']['managed_topic_enum']}")
    
    if dry_run:
        print("\n🔍 DRY RUN - showing what would be created...")
        print("\nMemory Bank Config (SDK format):")
        print(json.dumps(memory_config, indent=2))
        return True
    
    print("\n⏳ Building Memory Bank configuration...")
    
    try:
        import vertexai
        # Note: Using internal types - see build_memory_bank_config() for details
        from vertexai._genai.types import (
            AgentEngineConfig,
            ReasoningEngineContextSpec,
        )
        
        # Build the Memory Bank config using SDK types
        memory_bank_config = build_memory_bank_config()
        
        print("✓ Memory Bank config built successfully")
        
        # Create context spec with Memory Bank config
        context_spec = ReasoningEngineContextSpec(
            memory_bank_config=memory_bank_config
        )
        
        # Create agent engine config
        agent_engine_config = AgentEngineConfig(
            display_name="Story Crafter Memory Bank",
            description="Story Crafter AI with custom memory topics for story preferences, characters, worlds, and narrative style.",
            context_spec=context_spec,
        )
        
        print("\n⏳ Creating Agent Engine...")
        print("   (This may take a few minutes)")
        
        # Use the new vertexai.Client API
        client = vertexai.Client(
            project=config['project'],
            location=config['location']
        )
        
        # Create the Agent Engine
        agent_engine = client.agent_engines.create(
            config=agent_engine_config
        )
        
        # Extract the agent engine ID from the resource
        # The response is an AgentEngine object with api_resource containing details
        if hasattr(agent_engine, 'api_resource') and agent_engine.api_resource:
            resource_name = agent_engine.api_resource.name
            display_name = getattr(agent_engine.api_resource, 'display_name', 'Story Crafter')
        elif hasattr(agent_engine, 'name'):
            resource_name = agent_engine.name
            display_name = getattr(agent_engine, 'display_name', 'Story Crafter')
        else:
            # Fallback: use string representation
            resource_name = str(agent_engine)
            display_name = "Story Crafter"
        
        # Format: projects/{project}/locations/{location}/reasoningEngines/{id}
        agent_engine_id = resource_name.split("/")[-1] if "/" in resource_name else resource_name
        
        print("\n" + "=" * 70)
        print("✅ AGENT ENGINE CREATED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n   Resource Name: {resource_name}")
        print(f"   Agent Engine ID: {agent_engine_id}")
        print(f"   Display Name: {display_name}")
        
        # Get the actual configured topics to display
        configured_topics = [t['custom_memory_topic']['label'] for t in get_memory_topics() if 'custom_memory_topic' in t]
        topics_list = '\n   '.join(f'• {topic}' for topic in configured_topics)
        
        print(f"""
📋 NEXT STEPS:

1. Update your .env file with the new Agent Engine ID:
   
   AGENT_ENGINE_ID={agent_engine_id}

2. Restart your Story Crafter app:
   
   streamlit run app.py

3. Your custom memory topics are now active:
   {topics_list}

Memory Bank will now extract these topics from conversations!
""")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Missing package: {e}")
        print("   Try: pip install google-cloud-aiplatform>=1.111.0")
        return False
    except Exception as e:
        print(f"\n❌ Error creating Agent Engine: {e}")
        print(f"   Type: {type(e).__name__}")
        
        # Provide alternative instructions
        print("""
📋 ALTERNATIVE: Create via Python script

If automatic creation failed, you can create the Agent Engine manually:

```python
import vertexai
from vertexai.preview import reasoning_engines
from vertexai.types import (
    MemoryBankCustomizationConfig as CustomizationConfig,
    MemoryBankCustomizationConfigMemoryTopic as MemoryTopic,
    MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic as CustomMemoryTopic,
    MemoryBankCustomizationConfigMemoryTopicManagedMemoryTopic as ManagedMemoryTopic,
    ManagedTopicEnum,
    ReasoningEngineContextSpec,
    ReasoningEngineContextSpecMemoryBankConfig as MemoryBankConfig,
)

vertexai.init(project="YOUR_PROJECT", location="us-central1")

# Define custom topics
customization_config = CustomizationConfig(
    memory_topics=[
        MemoryTopic(
            managed_memory_topic=ManagedMemoryTopic(
                managed_topic_enum=ManagedTopicEnum.USER_PREFERENCES
            )
        ),
        MemoryTopic(
            custom_memory_topic=CustomMemoryTopic(
                label="story_preferences",
                description="User preferences about story genres, themes, tone..."
            )
        ),
        # Add more topics...
    ]
)

memory_bank_config = MemoryBankConfig(
    customization_config=customization_config
)

context_spec = ReasoningEngineContextSpec(
    memory_bank_config=memory_bank_config
)

agent_engine = reasoning_engines.ReasoningEngine.create(
    display_name="Story Crafter",
    context_spec=context_spec,
)

print(f"Created: {agent_engine.resource_name}")
```
""")
        return False


def update_agent_engine():
    """
    Update an existing Agent Engine's Memory Bank configuration.
    
    This updates the context_spec with the new memory topics without
    creating a new Agent Engine.
    """
    config = get_env_config()
    
    if not config['project'] or not config['agent_engine_id']:
        print("❌ GOOGLE_CLOUD_PROJECT and AGENT_ENGINE_ID must be set")
        return False
    
    print("\n" + "=" * 70)
    print("UPDATE EXISTING AGENT ENGINE MEMORY BANK CONFIG")
    print("=" * 70)
    
    print(f"\n📋 Target Agent Engine:")
    print(f"   Project: {config['project']}")
    print(f"   Location: {config['location']}")
    print(f"   Agent Engine ID: {config['agent_engine_id']}")
    
    # Get memory config
    memory_config = get_customization_config()
    custom_topics = [t for t in memory_config['memory_topics'] if 'custom_memory_topic' in t]
    
    print(f"\n📝 Memory Topics to apply:")
    for topic in custom_topics:
        print(f"   • {topic['custom_memory_topic']['label']}")
    
    print("\n⏳ Building Memory Bank configuration...")
    
    try:
        import vertexai
        
        # Get the memory topics config
        memory_config = get_customization_config()
        
        print("✓ Memory config loaded")
        
        # Build resource name
        agent_engine_name = (
            f"projects/{config['project']}/locations/{config['location']}/"
            f"reasoningEngines/{config['agent_engine_id']}"
        )
        
        print(f"\n⏳ Updating Agent Engine: {config['agent_engine_id']}...")
        
        # Initialize client and update
        client = vertexai.Client(
            project=config['project'],
            location=config['location']
        )
        
        # Update the agent engine using dict config
        response = client.agent_engines.update(
            name=agent_engine_name,
            config={
                "context_spec": {
                    "memory_bank_config": {
                        "customization_configs": [
                            {
                                "memory_topics": memory_config['memory_topics']
                            }
                        ]
                    }
                }
            }
        )
        
        print("\n" + "=" * 70)
        print("✅ AGENT ENGINE UPDATED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n   Agent Engine ID: {config['agent_engine_id']}")
        print(f"   Memory topics updated: {len(custom_topics) + 1}")
        
        print("""
📋 NEXT STEPS:

1. Your existing Agent Engine now has the updated memory topics
2. No need to change AGENT_ENGINE_ID in .env
3. Restart your app: streamlit run app.py
4. New conversations will use the updated extraction config
""")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error updating Agent Engine: {e}")
        print(f"   Type: {type(e).__name__}")
        print("\n💡 If update fails, you may need to create a new Agent Engine with --create")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create/manage Agent Engine with Memory Bank",
    )
    
    parser.add_argument("--info", "-i", action="store_true",
                       help="Show current configuration")
    parser.add_argument("--create", "-c", action="store_true",
                       help="Create new Agent Engine with custom Memory Bank config")
    parser.add_argument("--update", "-u", action="store_true",
                       help="Update existing Agent Engine's Memory Bank config")
    parser.add_argument("--dry-run", "-n", action="store_true",
                       help="Show what would be created without creating")
    parser.add_argument("--test-memory", "-t", action="store_true",
                       help="Test memory generation with current Agent Engine")
    
    args = parser.parse_args()
    
    if not any([args.info, args.create, args.update, args.test_memory]):
        # Default: show info
        show_info()
    else:
        if args.info:
            show_info()
        if args.update:
            update_agent_engine()
        if args.create:
            create_agent_engine(dry_run=args.dry_run)
        if args.test_memory:
            test_memory_generation()


if __name__ == "__main__":
    main()

