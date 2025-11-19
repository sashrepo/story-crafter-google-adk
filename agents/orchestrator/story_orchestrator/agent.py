"""
ADK-based Story Orchestrator for Story Crafter.

This module uses Google ADK's Sequential, Parallel, and Loop workflow agents to
coordinate story generation with optimal performance.

Workflow:
1. User Intent Agent (sequential)
2. Parallel execution:
   - Worldbuilder Agent
   - Character Forge Agent  
   - Plot Architect Agent
3. Story Writer Agent (sequential) - creates initial draft
4. Story Quality Loop (max 3 iterations):
   - Critic Agent: reviews and approves or provides feedback
   - Refiner Agent: revises story or exits loop when approved

USAGE (CLI):
    adk run orchestrator/story_orchestrator
    
    Then interact with the agent in the interactive CLI.

USAGE (Python - see example.py for full implementation):
    The ADK CLI is the recommended way to run agents interactively.
    For programmatic usage, see example.py which uses proper ADK Runner setup.
"""

import os
from pathlib import Path
import sys

# Ensure project root is discoverable for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent

# --------------------------------------------------------------------
# Import sub-agents
# --------------------------------------------------------------------
from agents.user_intent.agent import root_agent as user_intent_agent
from agents.safety.agent import root_agent as safety_check_agent
from agents.worldbuilder.agent import root_agent as worldbuilder_agent
from agents.character_forge.agent import root_agent as character_forge_agent
from agents.plot_architect.agent import root_agent as plot_architect_agent
from agents.story_writer.agent import root_agent as story_writer_agent
from agents.story_quality_loop.agent import story_quality_loop
from agents.story_editor.agent import root_agent as story_editor_agent
from agents.story_question_answerer.agent import root_agent as story_qa_agent

# Optional model imports for type hints
from models.intent import UserIntent
from models.world import WorldModel
from models.character import CharacterModel
from models.plot import PlotModel
from models.story import StoryModel


# --------------------------------------------------------------------
# 1️⃣ PARALLEL content generation stage
# --------------------------------------------------------------------
parallel_content_generation = ParallelAgent(
    name="parallel_content_generation",
    description="Generates world, characters, and plot simultaneously for efficiency",
    sub_agents=[
        worldbuilder_agent,
        character_forge_agent,
        plot_architect_agent,
    ],
)


# --------------------------------------------------------------------
# 2️⃣ Top-level Sequential Agent (default with refinement)
# --------------------------------------------------------------------
story_orchestrator = SequentialAgent(
    name="story_orchestrator",
    description="Top-level orchestrator: safety → intent → content → writer → quality loop with iterative refinement",
    sub_agents=[
        safety_check_agent,
        user_intent_agent,
        parallel_content_generation,
        story_writer_agent,
        story_quality_loop,  # LoopAgent with critic + refiner (max 3 iterations)
    ],
)


# --------------------------------------------------------------------
# Helper function to get orchestrator based on refinement preference
# --------------------------------------------------------------------
def get_orchestrator(enable_refinement: bool = True, mode: str = "create"):
    """
    Get the appropriate orchestrator based on mode and refinement preference.
    
    Args:
        enable_refinement: If True, returns the default orchestrator with quality loop (only for 'create' mode).
        mode: One of "create", "edit", "question".
              - create: Full story generation pipeline
              - edit: Modifies existing story
              - question: Answers questions about existing story
    
    Returns:
        The appropriate Agent orchestrator
    """
    
    if mode == "edit":
        # Need fresh safety agent and editor agent to avoid parent conflicts
        import importlib
        import agents.safety.agent
        import agents.story_editor.agent
        
        importlib.reload(agents.safety.agent)
        importlib.reload(agents.story_editor.agent)
        
        from agents.safety.agent import root_agent as fresh_safety_agent
        from agents.story_editor.agent import root_agent as fresh_editor_agent

        # Safety -> Editor
        return SequentialAgent(
            name="story_editor_orchestrator",
            description="Editor pipeline: safety → editor",
            sub_agents=[
                fresh_safety_agent,
                fresh_editor_agent,
            ],
        )
        
    if mode == "question":
        # Need fresh safety agent and QA agent
        import importlib
        import agents.safety.agent
        import agents.story_question_answerer.agent
        
        importlib.reload(agents.safety.agent)
        importlib.reload(agents.story_question_answerer.agent)
        
        from agents.safety.agent import root_agent as fresh_safety_agent
        from agents.story_question_answerer.agent import root_agent as fresh_qa_agent

        # Safety -> QA
        return SequentialAgent(
            name="story_qa_orchestrator",
            description="QA pipeline: safety → question answerer",
            sub_agents=[
                fresh_safety_agent,
                fresh_qa_agent,
            ],
        )

    # Default: Create Mode
    if enable_refinement:
        return story_orchestrator
    else:
        # Build fast orchestrator on-demand to avoid parent conflicts
        # Need to reload modules to get truly fresh agent instances
        import importlib
        import agents.safety.agent
        import agents.user_intent.agent
        import agents.worldbuilder.agent
        import agents.character_forge.agent
        import agents.plot_architect.agent
        import agents.story_writer.agent
        
        # Reload to get fresh instances (not cached)
        importlib.reload(agents.safety.agent)
        importlib.reload(agents.user_intent.agent)
        importlib.reload(agents.worldbuilder.agent)
        importlib.reload(agents.character_forge.agent)
        importlib.reload(agents.plot_architect.agent)
        importlib.reload(agents.story_writer.agent)
        
        # Now import fresh instances
        from agents.safety.agent import root_agent as fresh_safety_check_agent
        from agents.user_intent.agent import root_agent as fresh_user_intent_agent
        from agents.worldbuilder.agent import root_agent as fresh_worldbuilder_agent
        from agents.character_forge.agent import root_agent as fresh_character_forge_agent
        from agents.plot_architect.agent import root_agent as fresh_plot_architect_agent
        from agents.story_writer.agent import root_agent as fresh_story_writer_agent
        
        fresh_parallel_content_generation = ParallelAgent(
            name="parallel_content_generation_fast",
            description="Generates world, characters, and plot simultaneously for efficiency",
            sub_agents=[
                fresh_worldbuilder_agent,
                fresh_character_forge_agent,
                fresh_plot_architect_agent,
            ],
        )
        
        return SequentialAgent(
            name="story_orchestrator_fast",
            description="Fast orchestrator: intent → content → writer (no refinement)",
            sub_agents=[
                fresh_safety_check_agent,
                fresh_user_intent_agent,
                fresh_parallel_content_generation,
                fresh_story_writer_agent,  # Skip quality loop for faster generation
            ],
        )


# --------------------------------------------------------------------
# CLI Compatibility — ADK expects `root_agent`
# --------------------------------------------------------------------
root_agent = story_orchestrator

