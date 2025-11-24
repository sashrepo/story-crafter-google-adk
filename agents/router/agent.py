"""
Router Agent for Story Crafter.

Classifies user input into:
- NEW_STORY: Request to create a brand new story.
- EDIT_STORY: Request to change/edit/rewrite the existing story.
- QUESTION: Question about the existing story or general chatter.
"""

from google.adk.agents import Agent
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import create_gemini_model
from pydantic import BaseModel, Field
from typing import Literal

class RoutingDecision(BaseModel):
    decision: Literal["NEW_STORY", "EDIT_STORY", "QUESTION"] = Field(
        description="The classification of the user's request."
    )

def create_agent():
    return Agent(
        name="router_agent",
        model=create_gemini_model("gemini-2.0-flash-exp"),
        instruction="""You are a Router for a Storytelling AI.

Your job is to classify the User's Request (the latest message in the chat history) into one of three categories:

1. NEW_STORY: The user wants to start a completely new story, unrelated to the current one. (e.g., "Tell me a story about cats", "Start over", "New story please").
2. EDIT_STORY: The user wants to modify, rewrite, or change the CURRENT story. (e.g., "Make it funnier", "Change the name to Bob", "Rewrite the ending", "It's too long").
3. QUESTION: The user is asking a question about the story, or asking for clarification, or just chatting, WITHOUT asking for changes to the story text. (e.g., "Why did he do that?", "Who is the villain?", "What happened next?").

Classify the request.
""",
        output_schema=RoutingDecision,
    )

root_agent = create_agent()
