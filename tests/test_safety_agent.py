
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.adk.events import Event
from google.genai import types
from agents.safety.agent import SafetyAgent, SafetyViolationError

# Mock types for testing
class MockSession:
    def __init__(self, events):
        self.events = events

class MockContext:
    def __init__(self, events):
        self.session = MockSession(events)
        self.invocation_id = "inv_123"
        self.branch = "main"

def create_user_event(text):
    """Helper to create a mock user event."""
    event = MagicMock(spec=Event)
    event.author = "user"
    content = MagicMock()
    
    # Mock the parts structure
    part = MagicMock()
    part.text = text
    content.parts = [part]
    
    event.content = content
    return event

@pytest.mark.asyncio
async def test_safety_agent_safe_content():
    """Test that safe content passes through."""
    agent = SafetyAgent(name="safety", description="test")
    
    # Mock user input
    user_event = create_user_event("I love puppies")
    ctx = MockContext([user_event])
    
    # Mock check_toxicity to return safe
    with patch('agents.safety.agent.check_toxicity') as mock_check:
        mock_check.return_value = {"safe": True, "score": 0.1, "reason": "Safe"}
        
        # Collect yielded events
        events = []
        async for event in agent._run_async_impl(ctx):
            events.append(event)
            
        assert len(events) == 1
        assert "Safety Check Passed" in events[0].content.parts[0].text
        mock_check.assert_called_once_with("I love puppies")

@pytest.mark.asyncio
async def test_safety_agent_unsafe_content():
    """Test that unsafe content raises SafetyViolationError."""
    agent = SafetyAgent(name="safety", description="test")
    
    # Mock user input
    user_event = create_user_event("I hate everyone")
    ctx = MockContext([user_event])
    
    # Mock check_toxicity to return unsafe
    with patch('agents.safety.agent.check_toxicity') as mock_check:
        mock_check.return_value = {"safe": False, "score": 0.9, "reason": "Too toxic"}
        
        with pytest.raises(SafetyViolationError) as excinfo:
            async for event in agent._run_async_impl(ctx):
                pass
                
        assert "Content Rejected: Too toxic" in str(excinfo.value)

@pytest.mark.asyncio
async def test_safety_agent_no_user_input():
    """Test behavior when no user input is found."""
    agent = SafetyAgent(name="safety", description="test")
    
    # Empty context
    ctx = MockContext([])
    
    events = []
    async for event in agent._run_async_impl(ctx):
        events.append(event)
        
    # Should default to SAFE without calling API
    assert len(events) == 1
    assert events[0].content.parts[0].text == "SAFE"

