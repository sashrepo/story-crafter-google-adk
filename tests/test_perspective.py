
import pytest
import sys
import os
import json
import urllib.error
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import using sys.modules logic to handle potential reloads or direct imports
try:
    from services.perspective import check_toxicity, PerspectiveError, SafetyViolationError
except ImportError:
    # Fallback or direct path manipulation
    sys.path.append(str(project_root))
    from services.perspective import check_toxicity, PerspectiveError, SafetyViolationError

# Mock API response helper
def mock_perspective_response(score):
    return {
        'attributeScores': {
            'TOXICITY': {
                'summaryScore': {
                    'value': score
                }
            }
        }
    }

@patch('services.perspective.PERSPECTIVE_API_KEY', None)
def test_check_toxicity_no_api_key():
    """Test behavior when API key is missing."""
    # Should log warning and return safe
    result = check_toxicity("some text")
    assert result["safe"] is True
    assert result["score"] == 0.0
    assert "No API key" in result["reason"]

@patch('services.perspective.PERSPECTIVE_API_KEY', 'fake_key')
@patch('urllib.request.urlopen')
def test_check_toxicity_safe(mock_urlopen):
    """Test safe content (low score)."""
    # Mock successful API response with low toxicity
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_perspective_response(0.1)).encode('utf-8')
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    result = check_toxicity("Hello world")
    assert result["safe"] is True
    assert result["score"] == 0.1
    assert result["reason"] == "Safe"

@patch('services.perspective.PERSPECTIVE_API_KEY', 'fake_key')
@patch('urllib.request.urlopen')
def test_check_toxicity_unsafe(mock_urlopen):
    """Test unsafe content (high score)."""
    # Mock successful API response with high toxicity
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_perspective_response(0.9)).encode('utf-8')
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    result = check_toxicity("I hate you", threshold=0.7)
    assert result["safe"] is False
    assert result["score"] == 0.9
    assert "exceeds threshold" in result["reason"]

@patch('services.perspective.PERSPECTIVE_API_KEY', 'fake_key')
@patch('urllib.request.urlopen')
def test_api_error(mock_urlopen):
    """Test API failure handling."""
    # Mock API error
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="http://api", code=403, msg="Forbidden", hdrs={}, fp=None
    )
    
    with pytest.raises(PerspectiveError):
        check_toxicity("text")
