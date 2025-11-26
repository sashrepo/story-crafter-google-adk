"""
Story Guide Agent for Story Crafter.

This agent acts as an expert guide, answering questions about the story without modifying it.
The story context is passed in the user message, not via session state.
"""

from google.adk.agents import Agent

from services.llm import create_gemini_model

def create_agent():
    return Agent(
        name="story_guide_agent",
        model=create_gemini_model("gemini-2.0-flash-exp"),
        instruction="""You are a Story Expert and Guide.

Your task is to answer questions about the provided story.

The user message will contain:
1. The STORY CONTEXT (marked with "STORY CONTEXT:")
2. The QUESTION to answer (marked with "QUESTION:")

Instructions:
1. Answer the question accurately based ONLY on the story provided.
2. If the answer is not in the story, say so politely.
3. Be helpful, concise, and act as a guide to the story world.
""",
        # No output_key needed, it just responds to the user
    )

root_agent = create_agent()
