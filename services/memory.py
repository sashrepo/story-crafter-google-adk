"""
Memory and Session Service Configuration for Story Crafter.

This module provides session and memory services that support both:
- InMemory: Local storage (resets on app restart)
- Vertex AI: Cloud-based persistent storage via Memory Bank

Configuration is automatic based on environment variables:
- GOOGLE_CLOUD_PROJECT: GCP project ID
- GOOGLE_CLOUD_LOCATION: GCP region (e.g., us-central1)
- AGENT_ENGINE_ID or MEMORY_BANK_ID: Vertex AI Agent Engine ID

Memory Bank Custom Topics:
Memory Bank can be configured with custom memory topics to control what
information is extracted and persisted. See services/memory_config.py for
Story Crafter's custom topic definitions.

Reference: https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/generate-memories
"""

import os
import logging
import streamlit as st
from google.adk.memory import InMemoryMemoryService, VertexAiMemoryBankService
from google.adk.sessions import InMemorySessionService, VertexAiSessionService

# Import custom memory configuration
from services.memory_config import get_customization_config, get_memory_topics

logger = logging.getLogger(__name__)


def _get_vertex_config():
    """Get Vertex AI configuration from environment variables."""
    return {
        "project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "location": os.getenv("GOOGLE_CLOUD_LOCATION"),
        "agent_engine_id": os.getenv("AGENT_ENGINE_ID") or os.getenv("MEMORY_BANK_ID")
    }


def get_memory_bank_customization():
    """
    Get the Memory Bank customization configuration for Story Crafter.
    
    This includes custom memory topics for:
    - story_preferences: Genre, themes, complexity
    - character_preferences: Character types and arcs
    - world_preferences: Settings and world-building
    - story_feedback: User reactions to stories
    - narrative_style: Writing style preferences
    
    Returns:
        Dictionary with memory_topics configuration.
    """
    return get_customization_config()


def _is_vertex_configured(config: dict) -> bool:
    """Check if all required Vertex AI config is present."""
    return all([config["project"], config["location"], config["agent_engine_id"]])


@st.cache_resource
def get_memory_service():
    """
    Create and cache the memory service.
    
    Uses VertexAiMemoryBankService if configured, otherwise InMemoryMemoryService.
    
    Returns:
        MemoryService: Storage for agent memory.
    """
    config = _get_vertex_config()

    if _is_vertex_configured(config):
        logger.info(f"Initializing VertexAiMemoryBankService (Project: {config['project']}, "
                   f"Location: {config['location']}, ID: {config['agent_engine_id']})")
        try:
            return VertexAiMemoryBankService(
                project=config["project"],
                location=config["location"],
                agent_engine_id=config["agent_engine_id"]
            )
        except Exception as e:
            logger.warning(f"Failed to initialize VertexAiMemoryBankService: {e}")
            logger.info("Falling back to InMemoryMemoryService")
            return InMemoryMemoryService()
            
    logger.info("Initializing InMemoryMemoryService (Vertex AI config missing)")
    return InMemoryMemoryService()


@st.cache_resource
def get_session_service():
    """
    Create and cache the session service.
    
    Uses VertexAiSessionService if configured, otherwise InMemorySessionService.
    
    Returns:
        SessionService: Session storage for conversations.
    """
    config = _get_vertex_config()

    if _is_vertex_configured(config):
        logger.info(f"Initializing VertexAiSessionService (Project: {config['project']}, "
                   f"Location: {config['location']}, ID: {config['agent_engine_id']})")
        try:
            return VertexAiSessionService(
                project=config["project"],
                location=config["location"],
                agent_engine_id=config["agent_engine_id"]
            )
        except Exception as e:
            logger.warning(f"Failed to initialize VertexAiSessionService: {e}")
            logger.info("Falling back to InMemorySessionService")
            return InMemorySessionService()

    logger.info("Initializing InMemorySessionService (Vertex AI config missing)")
    return InMemorySessionService()


def print_memory_topics_for_setup():
    """
    Print the custom memory topics in a format suitable for Memory Bank setup.
    
    Use this output when configuring your Memory Bank instance via:
    - Google Cloud Console
    - Vertex AI Agent Engine API
    - gcloud CLI
    
    Example usage:
        python -c "from services.memory import print_memory_topics_for_setup; print_memory_topics_for_setup()"
    """
    import json
    topics = get_memory_topics()
    
    print("=" * 60)
    print("STORY CRAFTER - MEMORY BANK CUSTOM TOPICS")
    print("=" * 60)
    print("\nCopy these topics when setting up your Memory Bank instance:\n")
    print(json.dumps({"memory_topics": topics}, indent=2))
    print("\n" + "=" * 60)
    print("To apply these topics, use the Vertex AI SDK or API:")
    print("=" * 60)
    print("""
# Python SDK example:
from google.cloud import aiplatform
from vertexai.types import MemoryBankCustomizationConfig

# When creating/updating your Agent Engine with Memory Bank:
customization_config = {
    "memory_topics": [
        # ... paste topics from above
    ]
}
""")
