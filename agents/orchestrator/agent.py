"""
Orchestrator agent wrapper for ADK web compatibility.

This file re-exports the story_orchestrator's root_agent to satisfy
ADK web server's expected directory structure.

For CLI usage:
    adk run agents/orchestrator/story_orchestrator
    adk web agents/  (will now find this root_agent)

For Python usage:
    from agents.orchestrator.story_orchestrator.agent import story_orchestrator
"""

from agents.orchestrator.story_orchestrator.agent import story_orchestrator

# ADK web and CLI expect this name
root_agent = story_orchestrator

__all__ = ['root_agent', 'story_orchestrator']

