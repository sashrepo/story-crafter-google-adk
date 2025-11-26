"""
Memory and Session Service Configuration for Story Crafter.

This module provides session and memory services that support both:
- InMemory: Local storage (resets on app restart)
- Vertex AI: Cloud-based persistent storage via Memory Bank

Configuration is automatic based on environment variables:
- GOOGLE_CLOUD_PROJECT: GCP project ID
- GOOGLE_CLOUD_LOCATION: GCP region (e.g., us-central1)
- AGENT_ENGINE_ID or MEMORY_BANK_ID: Vertex AI Agent Engine ID
"""

import os
import logging
import streamlit as st
from google.adk.memory import InMemoryMemoryService, VertexAiMemoryBankService
from google.adk.sessions import InMemorySessionService, VertexAiSessionService

logger = logging.getLogger(__name__)


def _get_vertex_config():
    """Get Vertex AI configuration from environment variables."""
    return {
        "project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "location": os.getenv("GOOGLE_CLOUD_LOCATION"),
        "agent_engine_id": os.getenv("AGENT_ENGINE_ID") or os.getenv("MEMORY_BANK_ID")
    }


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
