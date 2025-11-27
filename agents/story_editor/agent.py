"""
Story Editor Agent for Story Crafter.

This agent edits an existing story based on user feedback/instructions.
The current story is passed in the user message, not via session state.
"""

from google.adk.agents import Agent

from services.llm import create_gemini_model

def create_agent():
    return Agent(
        name="story_editor_agent",
        model=create_gemini_model("gemini-2.5-flash"),
        instruction="""You are a skilled Story Editor.

Your task is to edit the provided story based on the user's request.

The user message will contain:
1. The CURRENT STORY to edit (marked with "CURRENT STORY:")
2. The EDIT REQUEST describing what changes to make (marked with "EDIT REQUEST:")

Instructions:
1. Read the current story and the edit request carefully.
2. Rewrite the story to incorporate the requested changes.
3. Maintain the original style and tone unless asked to change it.
4. Ensure the story remains coherent and grammatical.
5. Output the COMPLETE updated story. Do not summarize or just show changes.
""",
        output_key="current_story",  # Update the story in context
    )

root_agent = create_agent()
