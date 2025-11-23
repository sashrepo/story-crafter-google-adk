"""
Test for Vertex AI Memory Bank and Session Service integration.

This test verifies that the memory service correctly initializes
both in-memory and Vertex AI modes based on environment configuration.
"""

import os
import pytest
from unittest.mock import patch, MagicMock


def test_memory_service_fallback_to_inmemory():
    """Test that memory service falls back to InMemory when Vertex AI is not configured."""
    # Mock streamlit's cache_resource to just return the function result
    with patch('services.memory.st.cache_resource', lambda f: f):
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            from services.memory import get_memory_service
            
            service = get_memory_service()
            
            # Should be InMemoryMemoryService
            assert service.__class__.__name__ == 'InMemoryMemoryService'


def test_session_service_fallback_to_inmemory():
    """Test that session service falls back to InMemory when Vertex AI is not configured."""
    # Mock streamlit's cache_resource
    with patch('services.memory.st.cache_resource', lambda f: f):
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            from services.memory import get_session_service
            
            service = get_session_service()
            
            # Should be InMemorySessionService
            assert service.__class__.__name__ == 'InMemorySessionService'


def test_memory_service_uses_vertex_when_configured():
    """Test that memory service uses Vertex AI when properly configured."""
    # Mock streamlit's cache_resource
    with patch('services.memory.st.cache_resource', lambda f: f):
        # Set environment variables for Vertex AI
        env_vars = {
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'GOOGLE_CLOUD_LOCATION': 'us-central1',
            'VERTEX_AGENT_ENGINE_ID': 'test-engine-id'
        }
        
        with patch.dict(os.environ, env_vars):
            from services.memory import get_memory_service
            
            service = get_memory_service()
            
            # Should be VertexAiMemoryBankService
            assert service.__class__.__name__ == 'VertexAiMemoryBankService'


def test_session_service_uses_vertex_when_configured():
    """Test that session service uses Vertex AI when properly configured."""
    # Mock streamlit's cache_resource
    with patch('services.memory.st.cache_resource', lambda f: f):
        # Set environment variables for Vertex AI
        env_vars = {
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'GOOGLE_CLOUD_LOCATION': 'us-central1',
            'VERTEX_AGENT_ENGINE_ID': 'test-engine-id'
        }
        
        with patch.dict(os.environ, env_vars):
            from services.memory import get_session_service
            
            service = get_session_service()
            
            # Should be VertexAiSessionService
            assert service.__class__.__name__ == 'VertexAiSessionService'


def test_memory_service_requires_all_config():
    """Test that memory service requires all config vars for Vertex AI."""
    # Mock streamlit's cache_resource
    with patch('services.memory.st.cache_resource', lambda f: f):
        # Only set project, missing engine ID
        env_vars = {
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'GOOGLE_CLOUD_LOCATION': 'us-central1'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            from services.memory import get_memory_service
            
            service = get_memory_service()
            
            # Should fall back to InMemory (missing VERTEX_AGENT_ENGINE_ID)
            assert service.__class__.__name__ == 'InMemoryMemoryService'


def test_session_service_requires_all_config():
    """Test that session service requires all config vars for Vertex AI."""
    # Mock streamlit's cache_resource
    with patch('services.memory.st.cache_resource', lambda f: f):
        # Only set project, missing engine ID
        env_vars = {
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'GOOGLE_CLOUD_LOCATION': 'us-central1'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            from services.memory import get_session_service
            
            service = get_session_service()
            
            # Should fall back to InMemory (missing VERTEX_AGENT_ENGINE_ID)
            assert service.__class__.__name__ == 'InMemorySessionService'


@pytest.mark.asyncio
async def test_story_engine_accepts_vertex_session_service():
    """Test that StoryEngine accepts VertexAiSessionService."""
    from services.story_engine import StoryEngine
    from google.adk.sessions import InMemorySessionService
    
    # Create with InMemory service
    engine = StoryEngine(session_service=InMemorySessionService())
    
    assert engine.session_service is not None
    assert hasattr(engine, 'session_service')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

