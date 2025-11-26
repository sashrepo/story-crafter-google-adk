"""
Safety Agent for Story Crafter.

This agent validates user input using the Perspective API to ensure
content safety before processing it further. It is a deterministic
agent that does NOT use an LLM, for lower latency and cost.
"""

from typing import AsyncGenerator, Optional

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types

from services.perspective import check_toxicity, SafetyViolationError

class SafetyAgent(BaseAgent):
    """
    A deterministic agent that checks content safety using Perspective API.
    It does NOT use an LLM.
    """
    
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Core logic to run this agent.
        It intercepts the user input, checks it, and either yields an event (if safe)
        or raises an exception (if unsafe).
        """
        
        # 1. Get the user input from the context
        # The context stores the session which contains the events.
        # We iterate through session events backwards to find the last 'user' message.
        
        user_text = ""
        # Use the helper method on ctx to get events
        # Note: _get_events is an internal helper but available on the instance
        events = ctx.session.events
        
        for event in reversed(events):
            if event.author == "user":
                # Extract text from Content object
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            user_text += part.text
                elif isinstance(event.content, str):
                    user_text = event.content
                break
                
        if not user_text:
            # Fallback: if no user message found in history (unlikely), just pass through
            # or check if it's in the 'input' of the context if ADK supports that.
            # For now, assuming history is populated.
             yield Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                branch=ctx.branch,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="SAFE")]
                ),
            )
             return

        # 2. Check Toxicity
        # This is where we fail hard if the content is toxic
        result = check_toxicity(user_text)
        
        if not result["safe"]:
             error_msg = f"Content Rejected: {result['reason']}"
             raise SafetyViolationError(error_msg)

        # 3. If Safe, we just yield an event confirming it was processed.
        # We construct the content as a proper types.Content object
        
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Safety Check Passed (Score: {result['score']:.2f})")]
            ), 
        )

# Create the Safety Agent instance
def create_agent():
    return SafetyAgent(
        name="safety_agent",
        description="Validates user input for safety using Perspective API (Deterministic).",
    )

root_agent = create_agent()
