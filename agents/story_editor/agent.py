"""
Story Editor Agent for Story Crafter.

This agent edits an existing story based on user feedback/instructions.
"""

from google.adk.agents import Agent
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.llm import create_gemini_model

def create_agent():
    return Agent(
        name="story_editor_agent",
        model=create_gemini_model("gemini-2.0-flash-exp"),
        instruction="""You are a skilled Story Editor.

Your task is to rewrite the Current Story based on the User Request.

Current Story:
{current_story}

User Request:
(See the latest message in the chat history)

Instructions:
1. Read the current story and the user's request carefully.
2. Rewrite the story to incorporate the requested changes.
3. Maintain the original style and tone unless asked to change it.
4. Ensure the story remains coherent and grammatical.
5. Output the COMPLETE updated story. Do not summarize or just show changes.
""",
        output_key="current_story",  # Update the story in context
    )

root_agent = create_agent()
