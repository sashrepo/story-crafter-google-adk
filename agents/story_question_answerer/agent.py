"""
Story Question Answerer Agent for Story Crafter.

This agent answers questions about the story without modifying it.
"""

from google.adk.agents import Agent
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import create_gemini_model

root_agent = Agent(
    name="story_question_answerer",
    model=create_gemini_model("gemini-2.0-flash-exp"),
    instruction="""You are a Story Expert.

Your task is to answer the User's question about the Current Story.

Current Story:
{current_story}

User Question:
(See the latest message in the chat history)

Instructions:
1. Answer the question accurately based ONLY on the story provided.
2. If the answer is not in the story, say so politely.
3. Be helpful and concise.
""",
    # No output_key needed, it just responds to the user
)
