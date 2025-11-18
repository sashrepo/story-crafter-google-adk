"""
ADK-based Story Orchestrator for Story Crafter.

This module uses Google ADK's Sequential and Parallel workflow agents to
coordinate story generation with optimal performance.

Workflow:
1. User Intent Agent (sequential)
2. Parallel execution:
   - Worldbuilder Agent
   - Character Forge Agent  
   - Plot Architect Agent
3. Story Writer Agent (sequential)
4. Art Director Agent (sequential)

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
from agents.worldbuilder.agent import root_agent as worldbuilder_agent
from agents.character_forge.agent import root_agent as character_forge_agent
from agents.plot_architect.agent import root_agent as plot_architect_agent
from agents.story_writer.agent import root_agent as story_writer_agent
from agents.art_director.agent import root_agent as art_director_agent

# Optional model imports for type hints
from models.intent import UserIntent
from models.world import WorldModel
from models.character import CharacterModel
from models.plot import PlotModel
from models.story import StoryModel
from models.artwork import ArtworkModel


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
# 2️⃣ Sequential pipeline (non-runnable workflow)
# --------------------------------------------------------------------
story_orchestrator_pipeline = SequentialAgent(
    name="story_orchestrator_pipeline",
    description="Pipeline combining intent, world, characters, plot, writing, and art",
    sub_agents=[
        user_intent_agent,
        parallel_content_generation,
        story_writer_agent,
        art_director_agent,
    ],
)


# --------------------------------------------------------------------
# 3️⃣ Top-level LLM Agent (runnable via ADK Runtime)
# --------------------------------------------------------------------
story_orchestrator = LlmAgent(
    name="story_orchestrator",
    model="gemini-2.5-flash",
    description="Top-level orchestrator agent for full story generation",
    sub_agents=[story_orchestrator_pipeline],
)


# --------------------------------------------------------------------
# CLI Compatibility — ADK expects `root_agent`
# --------------------------------------------------------------------
root_agent = story_orchestrator

