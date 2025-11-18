"""
Example script demonstrating Story Crafter ADK usage.

This script shows how to use the ADK Runner with proper session management
to generate a complete story with all agents.
"""

import asyncio
import os
from pathlib import Path
import uuid

# Set up path for imports
import sys
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from orchestrator.story_orchestrator.agent import story_orchestrator


async def generate_story_example():
    """Generate a sample story using the full orchestrator."""
    
    # Example story request
    user_request = """
    Create a 5-minute bedtime story for my 8-year-old daughter.
    She loves mermaids, gymnastics, and stories about being brave.
    Keep it calming and appropriate for bedtime.
    """
    
    print("🚀 Starting Story Generation...")
    print(f"📝 Request: {user_request.strip()}\n")
    
    try:
        # Set up runner with proper session management
        session_service = InMemorySessionService()
        runner = Runner(
            agent=story_orchestrator,
            session_service=session_service
        )
        
        # Create session IDs
        user_id = "user_001"
        session_id = str(uuid.uuid4())
        
        # Run the orchestrator
        events = runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message={"text": user_request}
        )
        
        print("✅ Story Generation Complete!\n")
        print("=" * 70)
        
        # Process events
        for event in events:
            if hasattr(event, 'content') and event.content:
                print(f"\n📘 Response:\n{event.content}")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"❌ Error generating story: {e}")
        import traceback
        traceback.print_exc()


async def generate_with_individual_agent():
    """Example of using a single agent directly."""
    
    from agents.user_intent.agent import root_agent as user_intent_agent
    
    print("\n🔍 Testing Individual Agent (User Intent)...\n")
    
    user_message = "I want a spooky mystery story for a 12-year-old, about 10 minutes long"
    
    # Set up runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=user_intent_agent,
        session_service=session_service
    )
    
    # Create session IDs
    user_id = "user_001"
    session_id = str(uuid.uuid4())
    
    # Run the agent
    events = runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message={"text": user_message}
    )
    
    print("✅ Intent Extraction Complete!")
    for event in events:
        if hasattr(event, 'content') and event.content:
            print(f"Output: {event.content}\n")


async def main():
    """Main entry point."""
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  WARNING: GOOGLE_API_KEY not found in environment!")
        print("Please set your API key:")
        print("  export GOOGLE_API_KEY='your-key-here'")
        print("\nOr create a .env file with:")
        print("  GOOGLE_API_KEY=your-key-here\n")
        return
    
    print("\n" + "=" * 70)
    print(" " * 20 + "STORY CRAFTER ADK")
    print(" " * 15 + "Multi-Agent Story Generation")
    print("=" * 70 + "\n")
    
    # Run full orchestrator example
    await generate_story_example()
    
    # Optionally, test individual agent
    # Uncomment to test:
    # await generate_with_individual_agent()


if __name__ == "__main__":
    asyncio.run(main())

