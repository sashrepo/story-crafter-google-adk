"""
Memory and Session Service Configuration for Story Crafter.

This module provides simplified in-memory services for session management.
Sessions are stored in memory and will reset when the application restarts.
"""

import streamlit as st
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService


@st.cache_resource
def get_memory_service():
    """
    Create and cache the in-memory service so it persists across Streamlit reruns.
    
    Returns:
        InMemoryMemoryService: In-memory storage for agent memory.
    """
    print("Initializing InMemoryMemoryService")
    return InMemoryMemoryService()


@st.cache_resource
def get_session_service():
    """
    Create and cache the in-memory session service for agent conversations.
    
    Returns:
        InMemorySessionService: In-memory session storage.
    """
    print("Initializing InMemorySessionService")
    return InMemorySessionService()

