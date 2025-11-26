"""
Pytest-based evaluation tests for Story Crafter agents.

Run with:
    uv run pytest tests/test_evals.py -v
    uv run pytest tests/test_evals.py -k router -v  # Run only router tests
    uv run pytest tests/test_evals.py -k "not Integration" -v  # Skip integration tests
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evals.datasets import EvalDataset, EvalCase
from evals.metrics import (
    AgeAppropriatenessScore,
    RouteAccuracy,
    SafetyCompliance,
    StoryQualityScore,
    StructuredOutputValidity,
)
from models.routing import RoutingDecision


# =============================================================================
# ROUTER AGENT EVALS
# =============================================================================

class TestRouterAccuracy:
    """Test the RouteAccuracy metric."""
    
    def test_parse_new_story_json(self):
        metric = RouteAccuracy()
        result = metric.evaluate('{"decision": "NEW_STORY"}', "create")
        assert result.passed is True
        assert result.score == 1.0
    
    def test_parse_edit_story_json(self):
        metric = RouteAccuracy()
        result = metric.evaluate('{"decision": "EDIT_STORY"}', "edit")
        assert result.passed is True
    
    def test_parse_question_json(self):
        metric = RouteAccuracy()
        result = metric.evaluate('{"decision": "QUESTION"}', "question")
        assert result.passed is True
    
    def test_parse_with_confidence(self):
        metric = RouteAccuracy()
        result = metric.evaluate('{"decision": "NEW_STORY", "confidence": 0.95}', "create")
        assert result.passed is True
    
    def test_parse_string_fallback(self):
        metric = RouteAccuracy()
        result = metric.evaluate("NEW_STORY", "create")
        assert result.passed is True
    
    def test_wrong_classification(self):
        metric = RouteAccuracy()
        result = metric.evaluate('{"decision": "NEW_STORY"}', "edit")
        assert result.passed is False
        assert result.score == 0.0


@pytest.mark.parametrize("case", EvalDataset.ROUTER_CASES, ids=lambda c: c.id)
def test_router_dataset_structure(case: EvalCase):
    """Ensure all router test cases have required fields."""
    assert case.id is not None
    assert case.input is not None
    assert case.expected_route in ["create", "edit", "question"]
    assert "router" in case.tags


# =============================================================================
# STRUCTURED OUTPUT EVALS  
# =============================================================================

class TestStructuredOutputValidity:
    """Test structured output validation."""
    
    def test_valid_routing_decision(self):
        metric = StructuredOutputValidity(RoutingDecision)
        result = metric.evaluate({"decision": "NEW_STORY", "confidence": 0.9})
        assert result.passed is True
    
    def test_invalid_routing_decision(self):
        metric = StructuredOutputValidity(RoutingDecision)
        result = metric.evaluate({"decision": "INVALID_VALUE"})
        assert result.passed is False
    
    def test_valid_json_string(self):
        metric = StructuredOutputValidity(RoutingDecision)
        result = metric.evaluate('{"decision": "EDIT_STORY"}')
        assert result.passed is True
    
    def test_invalid_json(self):
        metric = StructuredOutputValidity(RoutingDecision)
        result = metric.evaluate("not valid json")
        assert result.passed is False


# =============================================================================
# STORY QUALITY EVALS
# =============================================================================

class TestStoryQualityScore:
    """Test story quality heuristics."""
    
    def test_good_story_length(self):
        metric = StoryQualityScore()
        story = " ".join(["word"] * 300)  # 300 words
        result = metric.evaluate(story, {"min_words": 200, "max_words": 500})
        assert result.metadata["word_count"] == 300
        assert result.metadata["scores"]["length"] == 1.0
    
    def test_story_too_short(self):
        metric = StoryQualityScore()
        story = " ".join(["word"] * 50)  # 50 words
        result = metric.evaluate(story, {"min_words": 200, "max_words": 500})
        assert result.metadata["scores"]["length"] < 1.0
    
    def test_required_elements_found(self):
        metric = StoryQualityScore()
        story = "Once upon a time, a brave bunny learned to share with friends."
        result = metric.evaluate(story, {
            "min_words": 5,
            "required_elements": ["bunny", "share", "friends"],
        })
        assert result.metadata["scores"]["required_elements"] == 1.0
    
    def test_required_elements_missing(self):
        metric = StoryQualityScore()
        story = "A cat sat on a mat."
        result = metric.evaluate(story, {
            "min_words": 5,
            "required_elements": ["bunny", "share"],
        })
        assert result.metadata["scores"]["required_elements"] == 0.0


class TestAgeAppropriateness:
    """Test age-appropriateness scoring."""
    
    def test_simple_sentences_for_young_child(self):
        metric = AgeAppropriatenessScore()
        story = "The cat sat. The dog ran. They were friends."
        result = metric.evaluate(story, {"age": 5})
        assert result.passed is True
    
    def test_complex_sentences_for_young_child(self):
        metric = AgeAppropriatenessScore()
        # Very long sentences for a 5-year-old
        story = ("The magnificent dragon soared through the cumulonimbus clouds, "
                 "its iridescent scales shimmering in the ethereal moonlight as "
                 "ancient prophecies foretold of its inevitable arrival. " * 3)
        result = metric.evaluate(story, {"age": 5})
        # Should score lower due to long sentences
        assert result.metadata["avg_sentence_length"] > 15


# =============================================================================
# SAFETY COMPLIANCE EVALS
# =============================================================================

class TestSafetyCompliance:
    """Test safety compliance metric."""
    
    def test_safe_content_passes(self):
        metric = SafetyCompliance()
        result = metric.evaluate("SAFE - Content passed safety check", "PASS")
        assert result.passed is True
    
    def test_blocked_content_detected(self):
        metric = SafetyCompliance()
        result = metric.evaluate("BLOCKED - Content violates policy", "BLOCK")
        assert result.passed is True
    
    def test_mismatch_detection(self):
        metric = SafetyCompliance()
        result = metric.evaluate("SAFE", "BLOCK")
        assert result.passed is False


# =============================================================================
# DATASET TESTS
# =============================================================================

class TestEvalDataset:
    """Test the EvalDataset class."""
    
    def test_get_by_tags_single(self):
        cases = EvalDataset.get_by_tags("router")
        assert len(cases) > 0
        for case in cases:
            assert "router" in case.tags
    
    def test_get_by_tags_multiple(self):
        cases = EvalDataset.get_by_tags("router", "new_story")
        assert len(cases) > 0
        for case in cases:
            assert "router" in case.tags
            assert "new_story" in case.tags
    
    def test_get_by_id_found(self):
        case = EvalDataset.get_by_id("router_new_1")
        assert case is not None
        assert case.id == "router_new_1"
    
    def test_get_by_id_not_found(self):
        case = EvalDataset.get_by_id("nonexistent")
        assert case is None


# =============================================================================
# INTEGRATION TESTS (require API key)
# =============================================================================

@pytest.mark.skipif(
    not pytest.importorskip("os").environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set"
)
class TestRouterIntegration:
    """Integration tests that actually call the router agent."""
    
    @pytest.mark.asyncio
    async def test_router_new_story_classification(self):
        """Test router correctly classifies a new story request."""
        from evals.runner import EvalRunner
        from evals.metrics import RouteAccuracy
        from agents.router.agent import create_agent
        
        runner = EvalRunner()
        case = EvalCase(
            id="integration_new_1",
            input="Tell me a story about a dragon",
            expected_route="create",
            tags=["integration"],
        )
        
        result = await runner.run_case(
            case=case,
            agent_factory=create_agent,
            metrics=[RouteAccuracy()],
        )
        
        assert result.passed, f"Expected pass, got: {result.output}"
    
    @pytest.mark.asyncio
    async def test_router_edit_classification(self):
        """Test router correctly classifies an edit request."""
        from evals.runner import EvalRunner
        from evals.metrics import RouteAccuracy
        from agents.router.agent import create_agent
        
        runner = EvalRunner()
        case = EvalCase(
            id="integration_edit_1",
            input="Make it funnier please",
            expected_route="edit",
            tags=["integration"],
        )
        
        result = await runner.run_case(
            case=case,
            agent_factory=create_agent,
            metrics=[RouteAccuracy()],
        )
        
        assert result.passed, f"Expected pass, got: {result.output}"

