"""
Unit tests for router mode detection parsing.

Tests the _parse_routing_decision method in StoryEngine to ensure
robust parsing of structured router output.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.story_engine import StoryEngine


def test_parse_routing_decision_valid_json():
    """Test parsing valid JSON with decision field."""
    engine = StoryEngine()
    
    # Test NEW_STORY
    result = engine._parse_routing_decision('{"decision": "NEW_STORY"}')
    assert result == "create", f"Expected 'create', got '{result}'"
    
    # Test EDIT_STORY
    result = engine._parse_routing_decision('{"decision": "EDIT_STORY"}')
    assert result == "edit", f"Expected 'edit', got '{result}'"
    
    # Test QUESTION
    result = engine._parse_routing_decision('{"decision": "QUESTION"}')
    assert result == "question", f"Expected 'question', got '{result}'"
    
    print("✅ Valid JSON parsing tests passed")


def test_parse_routing_decision_with_confidence():
    """Test parsing JSON with optional confidence field."""
    engine = StoryEngine()
    
    result = engine._parse_routing_decision(
        '{"decision": "EDIT_STORY", "confidence": 0.95}'
    )
    assert result == "edit", f"Expected 'edit', got '{result}'"
    
    print("✅ JSON with confidence field test passed")


def test_parse_routing_decision_string_fallback():
    """Test fallback to string matching for backwards compatibility."""
    engine = StoryEngine()
    
    # Test raw decision strings (no JSON)
    result = engine._parse_routing_decision("EDIT_STORY")
    assert result == "edit", f"Expected 'edit', got '{result}'"
    
    result = engine._parse_routing_decision("QUESTION about the story")
    assert result == "question", f"Expected 'question', got '{result}'"
    
    result = engine._parse_routing_decision("NEW_STORY request")
    assert result == "create", f"Expected 'create', got '{result}'"
    
    print("✅ String fallback tests passed")


def test_parse_routing_decision_malformed():
    """Test handling of malformed input."""
    engine = StoryEngine()
    
    # Malformed JSON with EDIT_STORY - string fallback will find it
    result = engine._parse_routing_decision('{"decision": "EDIT_STORY"')
    assert result == "edit", f"Expected 'edit' (via string fallback), got '{result}'"
    
    # Unknown decision value - should use default
    result = engine._parse_routing_decision('{"decision": "INVALID_MODE"}')
    assert result == "create", f"Expected 'create' default, got '{result}'"
    
    # Empty string - should use default
    result = engine._parse_routing_decision("")
    assert result == "create", f"Expected 'create' default, got '{result}'"
    
    # Completely invalid input - should use default
    result = engine._parse_routing_decision("random gibberish text here")
    assert result == "create", f"Expected 'create' default, got '{result}'"
    
    print("✅ Malformed input tests passed")


def test_parse_routing_decision_whitespace():
    """Test handling of whitespace around JSON."""
    engine = StoryEngine()
    
    result = engine._parse_routing_decision('  {"decision": "QUESTION"}  ')
    assert result == "question", f"Expected 'question', got '{result}'"
    
    print("✅ Whitespace handling test passed")


def run_all_tests():
    """Run all router parsing tests."""
    print("\n" + "="*60)
    print("🧪 Running Router Mode Detection Tests")
    print("="*60 + "\n")
    
    try:
        test_parse_routing_decision_valid_json()
        test_parse_routing_decision_with_confidence()
        test_parse_routing_decision_string_fallback()
        test_parse_routing_decision_malformed()
        test_parse_routing_decision_whitespace()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()

