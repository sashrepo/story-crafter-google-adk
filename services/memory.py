"""
Memory and Session Service Configuration for Story Crafter.

This module handles the initialization of memory and session services,
preferring Vertex AI Memory Bank for long-term storage if configured.
"""

import os
import streamlit as st
from google.adk.memory import VertexAiMemoryBankService, InMemoryMemoryService
from google.adk.sessions import VertexAiSessionService, InMemorySessionService

@st.cache_resource
def get_memory_service():
    """
    Create and cache the memory service so it persists across Streamlit reruns.
    
    Returns:
        BaseMemoryService: Configured memory service (Vertex AI or InMemory).
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    agent_engine_id = os.environ.get("VERTEX_AGENT_ENGINE_ID")
    
    if project_id and agent_engine_id:
        print(f"Initializing Vertex AI Memory Bank (Project: {project_id}, Engine: {agent_engine_id})")
        return VertexAiMemoryBankService(
            project=project_id,
            location=location,
            agent_engine_id=agent_engine_id
        )
    
    print("VERTEX_AGENT_ENGINE_ID not set. Falling back to InMemoryMemoryService.")
    return InMemoryMemoryService()


@st.cache_resource
def get_session_service():
    """
    Create and cache the session service for agent conversations.
    Uses Vertex AI Session Service if configured, otherwise falls back to InMemory.
    
    Returns:
        BaseSessionService: Configured session service (Vertex AI or InMemory).
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    agent_engine_id = os.environ.get("VERTEX_AGENT_ENGINE_ID")
    
    if project_id and agent_engine_id:
        print(f"Initializing Vertex AI Session Service (Project: {project_id}, Engine: {agent_engine_id})")
        return VertexAiSessionService(
            project=project_id,
            location=location,
            agent_engine_id=agent_engine_id
        )
    
    print("VERTEX_AGENT_ENGINE_ID not set. Falling back to InMemorySessionService.")
    return InMemorySessionService()

