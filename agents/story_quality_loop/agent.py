"""
Story Quality Loop Agent using ADK's LoopAgent.

This implements an iterative refinement process:
1. Story Writer creates initial draft (runs once)
2. Quality Loop (max 3 iterations):
   - Critic Agent: Reviews story, outputs APPROVED or feedback
   - Refiner Agent: Exits loop if approved, else revises story

Run with:
    uv run adk run agents/story_quality_loop
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk.agents import Agent, LoopAgent
from google.adk.tools import FunctionTool, exit_loop
from config import create_gemini_model
from models.story_feedback import StoryFeedback


def create_agent():
    # --------------------------------------------------------------------
    # Critic Agent - Reviews story and provides feedback
    # --------------------------------------------------------------------
    critic_agent = Agent(
        name="quality_critic",
        model=create_gemini_model("gemini-2.0-flash-thinking-exp"),
        instruction="""You are a VERY STRICT, picky story critic. Your job is to push for perfection.

Story: {current_story}

Evaluate these aspects:
- Age appropriateness for target audience
- Tone consistency throughout
- Plot coherence and pacing
- Character development
- Prose quality and grammar

IMPORTANT TEST MODE INSTRUCTIONS:
- Unless the story is absolute literary perfection (Score > 9.8/10), DO NOT APPROVE.
- Always find at least one thing to improve (e.g., "Add more sensory details", "Dialogue tags are repetitive", "Pacing in the middle is slow").
- Be constructive but demanding.

- If (and only if) it is perfect: Respond with ONE WORD: APPROVED
- Otherwise: Provide 2-3 specific, actionable suggestions for improvement.

DO NOT add any other text if approving. Just the word: APPROVED""",
        output_key="critique",
    )


    # --------------------------------------------------------------------
    # Refiner Agent - Revises story based on feedback or exits loop
    # --------------------------------------------------------------------
    refiner_agent = Agent(
        name="story_refiner",
        model=create_gemini_model("gemini-2.0-flash-exp"),
        instruction="""You are a story refiner with ONE critical responsibility: check if the story is approved.

Critique: {critique}

STEP 1 - CHECK FOR APPROVAL:
Look at the critique above. Does it contain the word "APPROVED"?

If YES: You MUST call the exit_loop function RIGHT NOW. Do not write anything else. Just call the function.

If NO: Continue to step 2.

STEP 2 - REVISE THE STORY:
Current Story: {current_story}

The story needs improvement. Rewrite it completely, incorporating this feedback:
{critique}

When rewriting:
- Keep the same title, format, and structure
- Fix all issues mentioned in the critique
- Preserve the core story elements (characters, setting, plot)
- Output the complete revised story with title and all content

REMEMBER: If the critique says "APPROVED", do NOT rewrite. Just call exit_loop!""",
        output_key="current_story",  # Overwrites the story with refined version
        tools=[FunctionTool(exit_loop)],
    )


    # --------------------------------------------------------------------
    # Loop Agent - Runs Critic → Refiner repeatedly until approved
    # --------------------------------------------------------------------
    story_quality_loop = LoopAgent(
        name="story_quality_loop",
        sub_agents=[critic_agent, refiner_agent],
        max_iterations=1,  # Prevents infinite loops
    )

    return story_quality_loop


# --------------------------------------------------------------------
# CLI Compatibility
# --------------------------------------------------------------------
root_agent = create_agent()
