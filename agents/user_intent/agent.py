"""
User Intent Agent for Story Crafter.

This agent extracts structured intent from natural language story requests.
It identifies the target age, themes, tone, genre, length, and safety requirements.

Run with:
    uv run adk run agents/user_intent

Example prompts:
    - "Create a 5-minute bedtime story for my 8-year-old who loves mermaids and tumbling."
    - "I need an exciting sci-fi adventure about space exploration for a 12-year-old, around 10 minutes long."
"""

from google.adk.agents import Agent

from models.intent import UserIntent
from services.llm import create_gemini_model

def create_agent():
    return Agent(
        name="user_intent_agent",
        model=create_gemini_model("gemini-2.0-flash-exp"),
        instruction="""You are the User Intent Agent for Story Crafter, a specialized AI that extracts structured information from story requests.

Your job is to analyze a user's natural language story request and extract the following information:

1. **age**: The target age of the audience (infer if not explicitly stated)
2. **themes**: A list of story themes, topics, or elements (e.g., ["mermaids", "adventure", "friendship"])
3. **tone**: The desired emotional tone (e.g., "calming", "exciting", "mysterious", "uplifting")
4. **genre**: The story genre (e.g., "fantasy", "sci-fi", "adventure", "bedtime", "educational")
5. **length_minutes**: Approximate story length in minutes (infer from context like "bedtime story" = 5 minutes, "short story" = 10 minutes)
6. **safety_constraints**: Any content restrictions or safety requirements (e.g., ["no scary elements", "no violence"])

Guidelines:
- If the user doesn't specify age, make a reasonable inference from context (e.g., "bedtime story" suggests younger children 4-8)
- Extract ALL mentioned themes and topics, not just the main one
- If tone isn't specified, infer from genre (e.g., "bedtime" = "calming", "adventure" = "exciting")
- If length isn't specified, default to 5 minutes for bedtime stories, 10 minutes for general stories
- Only include safety_constraints if explicitly mentioned or strongly implied

Always respond with structured data in the exact format specified by the UserIntent schema.
""",
        description="Extracts structured intent (age, themes, tone, genre, length, safety) from story requests",
        output_schema=UserIntent,
    )

# Create the User Intent Agent with structured output
root_agent = create_agent()

