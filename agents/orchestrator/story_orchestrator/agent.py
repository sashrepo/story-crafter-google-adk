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
    adk run agents/orchestrator/story_orchestrator
    
    Then interact with the agent in the interactive CLI.

USAGE (Python - see example.py for full implementation):
    The ADK CLI is the recommended way to run agents interactively.
    For programmatic usage, see example.py which uses proper ADK Runner setup.
"""

from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent

# --------------------------------------------------------------------
# Import sub-agent modules (factories)
# --------------------------------------------------------------------
from agents.user_intent import agent as user_intent_module
from agents.safety import agent as safety_module
from agents.worldbuilder import agent as worldbuilder_module
from agents.character_forge import agent as character_forge_module
from agents.plot_architect import agent as plot_architect_module
from agents.story_writer import agent as story_writer_module
from agents.story_quality_loop import agent as story_quality_loop_module
from agents.story_editor import agent as story_editor_module
from agents.story_guide import agent as story_guide_module



def create_orchestrator(enable_refinement: bool = True, mode: str = "create"):
    """
    Get the appropriate orchestrator based on mode and refinement preference.
    Creates FRESH agent instances for every call to avoid state pollution.
    
    Args:
        enable_refinement: If True, returns the default orchestrator with quality loop (only for 'create' mode).
        mode: One of "create", "edit", "question".
              - create: Full story generation pipeline
              - edit: Modifies existing story
              - question: Answers questions about existing story
    
    Returns:
        The appropriate Agent orchestrator
    """
    
    # Always create a fresh safety agent
    safety_agent = safety_module.create_agent()
    
    # ----------------------------------------------------------------
    # EDIT MODE
    # ----------------------------------------------------------------
    if mode == "edit":
        editor_agent = story_editor_module.create_agent()
        
        return SequentialAgent(
            name="story_editor_orchestrator",
            description="Editor pipeline: safety → editor",
            sub_agents=[
                safety_agent,
                editor_agent,
            ],
        )
        
    # ----------------------------------------------------------------
    # QUESTION MODE
    # ----------------------------------------------------------------
    if mode == "question":
        guide_agent = story_guide_module.create_agent()
        
        return SequentialAgent(
            name="story_guide_orchestrator",
            description="Guide pipeline: safety → story guide",
            sub_agents=[
                safety_agent,
                guide_agent,
            ],
        )

    # ----------------------------------------------------------------
    # CREATE MODE (Default)
    # ----------------------------------------------------------------
    
    # Create fresh instances of all sub-agents
    user_intent_agent = user_intent_module.create_agent()
    worldbuilder_agent = worldbuilder_module.create_agent()
    character_forge_agent = character_forge_module.create_agent()
    plot_architect_agent = plot_architect_module.create_agent()
    story_writer_agent = story_writer_module.create_agent()
    
    # 1. Parallel content generation
    parallel_content_generation = ParallelAgent(
        name="parallel_content_generation",
        description="Generates world, characters, and plot simultaneously for efficiency",
        sub_agents=[
            worldbuilder_agent,
            character_forge_agent,
            plot_architect_agent,
        ],
    )
    
    # Build the chain
    sub_agents = [
        safety_agent,
        user_intent_agent,
        parallel_content_generation,
        story_writer_agent,
    ]
    
    # Add refinement loop if enabled
    if enable_refinement:
        story_quality_loop = story_quality_loop_module.create_agent()
        sub_agents.append(story_quality_loop)
        
        return SequentialAgent(
            name="story_orchestrator",
            description="Top-level orchestrator: safety → intent → content → writer → quality loop",
            sub_agents=sub_agents,
        )
    else:
        return SequentialAgent(
            name="story_orchestrator_fast",
            description="Fast orchestrator: intent → content → writer (no refinement)",
            sub_agents=sub_agents,
        )

# Backwards compatibility alias for function
get_orchestrator = create_orchestrator

# --------------------------------------------------------------------
# CLI Compatibility — ADK expects `root_agent`
# --------------------------------------------------------------------
root_agent = create_orchestrator()
