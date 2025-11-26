"""
Evaluation metrics for Story Crafter agents.

Provides both deterministic metrics (exact match, structure validation)
and LLM-as-judge metrics (quality scoring, coherence assessment).

Metrics:
    - RouteAccuracy: Validates router classification (NEW_STORY/EDIT_STORY/QUESTION)
    - StructuredOutputValidity: Validates Pydantic schema conformance
    - StoryQualityScore: Heuristic or LLM-based story quality evaluation
    - SafetyCompliance: Validates safety agent decisions (PASS/BLOCK)
    - AgeAppropriatenessScore: Readability analysis for target age
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel, ValidationError


@dataclass
class MetricResult:
    """Result of evaluating a single metric.
    
    Attributes:
        metric_name: Name of the metric that produced this result
        passed: Whether the evaluation passed
        score: Numeric score from 0.0 to 1.0
        details: Human-readable explanation of the result
        metadata: Additional data (raw output, parsed values, etc.)
    """
    
    metric_name: str
    passed: bool
    score: float  # 0.0 to 1.0
    details: str
    metadata: dict = field(default_factory=dict)


class Metric(ABC):
    """Base class for evaluation metrics."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the metric."""
        pass
    
    @abstractmethod
    def evaluate(self, output: Any, expected: Any, **kwargs) -> MetricResult:
        """Evaluate the metric and return a result."""
        pass


class RouteAccuracy(Metric):
    """Evaluates if the router correctly classified the request."""
    
    @property
    def name(self) -> str:
        return "route_accuracy"
    
    def evaluate(
        self, 
        output: str,  # Router output (JSON or text)
        expected: str,  # Expected route: "create", "edit", or "question"
        **kwargs
    ) -> MetricResult:
        """Check if the router output matches expected route."""
        
        # Parse the output
        parsed_route = self._parse_route(output)
        
        passed = parsed_route == expected
        score = 1.0 if passed else 0.0
        
        return MetricResult(
            metric_name=self.name,
            passed=passed,
            score=score,
            details=f"Expected '{expected}', got '{parsed_route}'",
            metadata={"raw_output": output, "parsed": parsed_route}
        )
    
    def _parse_route(self, output: str) -> str:
        """Parse router output to determine route."""
        output_upper = output.upper()
        
        # Try JSON parsing first
        try:
            data = json.loads(output)
            decision = data.get("decision", "").upper()
        except (json.JSONDecodeError, TypeError):
            decision = output_upper
        
        # Map to route
        if "NEW_STORY" in decision:
            return "create"
        elif "EDIT_STORY" in decision:
            return "edit"
        elif "QUESTION" in decision:
            return "question"
        
        # Fallback string matching
        if "NEW_STORY" in output_upper:
            return "create"
        elif "EDIT_STORY" in output_upper or "EDIT" in output_upper:
            return "edit"
        elif "QUESTION" in output_upper:
            return "question"
        
        return "unknown"


class StructuredOutputValidity(Metric):
    """Validates that agent output matches the expected Pydantic schema."""
    
    def __init__(self, schema: type[BaseModel]):
        self.schema = schema
    
    @property
    def name(self) -> str:
        return f"structured_output_validity_{self.schema.__name__}"
    
    def evaluate(
        self,
        output: str | dict,
        expected: Any = None,  # Optional expected values for specific fields
        **kwargs
    ) -> MetricResult:
        """Validate output against schema."""
        
        # Parse if string
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except json.JSONDecodeError as e:
                return MetricResult(
                    metric_name=self.name,
                    passed=False,
                    score=0.0,
                    details=f"JSON parse error: {e}",
                )
        
        # Validate against schema
        try:
            validated = self.schema.model_validate(output)
            
            # Check specific expected values if provided
            if expected:
                mismatches = []
                for field, expected_value in expected.items():
                    actual_value = getattr(validated, field, None)
                    if actual_value != expected_value:
                        mismatches.append(f"{field}: expected {expected_value}, got {actual_value}")
                
                if mismatches:
                    return MetricResult(
                        metric_name=self.name,
                        passed=False,
                        score=0.5,  # Partial credit for valid structure
                        details=f"Schema valid but field mismatches: {'; '.join(mismatches)}",
                        metadata={"validated": validated.model_dump()},
                    )
            
            return MetricResult(
                metric_name=self.name,
                passed=True,
                score=1.0,
                details="Output validates against schema",
                metadata={"validated": validated.model_dump()},
            )
            
        except ValidationError as e:
            return MetricResult(
                metric_name=self.name,
                passed=False,
                score=0.0,
                details=f"Schema validation failed: {e}",
            )


class StoryQualityScore(Metric):
    """
    LLM-as-judge metric for evaluating story quality.
    
    Evaluates: coherence, creativity, age-appropriateness, engagement,
    and adherence to the requested parameters.
    """
    
    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: Optional LLM client for evaluation. If None, uses
                        a simple heuristic-based evaluation.
        """
        self.llm_client = llm_client
    
    @property
    def name(self) -> str:
        return "story_quality_score"
    
    def evaluate(
        self,
        output: str,  # The generated story
        expected: dict = None,  # Expected attributes (age, themes, etc.)
        **kwargs
    ) -> MetricResult:
        """Evaluate story quality."""
        
        if self.llm_client:
            return self._evaluate_with_llm(output, expected, **kwargs)
        else:
            return self._evaluate_heuristic(output, expected, **kwargs)
    
    def _evaluate_heuristic(
        self, 
        output: str, 
        expected: dict = None,
        **kwargs
    ) -> MetricResult:
        """Simple heuristic-based evaluation."""
        
        scores = {}
        
        # Length check
        word_count = len(output.split())
        if expected:
            min_words = expected.get("min_words", 100)
            max_words = expected.get("max_words", 2000)
            
            if min_words <= word_count <= max_words:
                scores["length"] = 1.0
            elif word_count < min_words:
                scores["length"] = word_count / min_words
            else:
                scores["length"] = max_words / word_count
        else:
            scores["length"] = 1.0 if 100 <= word_count <= 2000 else 0.5
        
        # Structure check (has beginning, middle, end)
        has_structure = len(output) > 200 and "\n" in output
        scores["structure"] = 1.0 if has_structure else 0.5
        
        # Required elements check
        if expected and "required_elements" in expected:
            found = sum(
                1 for elem in expected["required_elements"]
                if elem.lower() in output.lower()
            )
            total = len(expected["required_elements"])
            scores["required_elements"] = found / total if total > 0 else 1.0
        else:
            scores["required_elements"] = 1.0
        
        # Average score
        avg_score = sum(scores.values()) / len(scores)
        passed = avg_score >= 0.7
        
        return MetricResult(
            metric_name=self.name,
            passed=passed,
            score=avg_score,
            details=f"Heuristic scores: {scores}",
            metadata={"scores": scores, "word_count": word_count},
        )
    
    def _evaluate_with_llm(
        self,
        output: str,
        expected: dict = None,
        **kwargs
    ) -> MetricResult:
        """LLM-as-judge evaluation (requires llm_client)."""
        
        prompt = f"""You are evaluating a generated story for quality.

STORY:
{output}

EXPECTED ATTRIBUTES:
{json.dumps(expected, indent=2) if expected else "None specified"}

Rate the story on these dimensions (1-10 each):
1. COHERENCE: Does the story flow logically? Are there plot holes?
2. CREATIVITY: Is the story original and imaginative?
3. AGE_APPROPRIATENESS: Is vocabulary and content suitable for the target age?
4. ENGAGEMENT: Is the story interesting and compelling?
5. ADHERENCE: Does it match the requested themes, tone, and length?

Respond in JSON format:
{{
    "coherence": <score>,
    "creativity": <score>,
    "age_appropriateness": <score>,
    "engagement": <score>,
    "adherence": <score>,
    "overall": <average>,
    "feedback": "<brief feedback>"
}}
"""
        
        try:
            # This would call the LLM - implementation depends on your client
            response = self.llm_client.generate(prompt)
            scores = json.loads(response)
            
            overall = scores.get("overall", 5.0)
            passed = overall >= 7.0
            
            return MetricResult(
                metric_name=self.name,
                passed=passed,
                score=overall / 10.0,
                details=scores.get("feedback", ""),
                metadata={"scores": scores},
            )
            
        except Exception as e:
            return MetricResult(
                metric_name=self.name,
                passed=False,
                score=0.0,
                details=f"LLM evaluation failed: {e}",
            )


class SafetyCompliance(Metric):
    """Evaluates if content passes safety checks."""
    
    @property
    def name(self) -> str:
        return "safety_compliance"
    
    def evaluate(
        self,
        output: str,  # Safety agent output or flag
        expected: str,  # "PASS" or "BLOCK"
        **kwargs
    ) -> MetricResult:
        """Check if safety decision matches expected."""
        
        output_upper = output.upper()
        
        # Determine actual safety decision
        if "SAFE" in output_upper or "PASS" in output_upper:
            actual = "PASS"
        elif "BLOCK" in output_upper or "REJECT" in output_upper or "VIOLATION" in output_upper:
            actual = "BLOCK"
        else:
            actual = "UNKNOWN"
        
        passed = actual == expected
        score = 1.0 if passed else 0.0
        
        return MetricResult(
            metric_name=self.name,
            passed=passed,
            score=score,
            details=f"Expected '{expected}', got '{actual}'",
            metadata={"raw_output": output},
        )


class AgeAppropriatenessScore(Metric):
    """Evaluates vocabulary and content complexity for target age."""
    
    # Average syllables per word thresholds by age
    SYLLABLE_THRESHOLDS = {
        5: 1.3,
        7: 1.5,
        10: 1.7,
        12: 1.9,
        14: 2.1,
    }
    
    @property
    def name(self) -> str:
        return "age_appropriateness"
    
    def evaluate(
        self,
        output: str,  # The story text
        expected: dict = None,  # Should contain {"age": <target_age>}
        **kwargs
    ) -> MetricResult:
        """Evaluate if vocabulary matches target age."""
        
        target_age = expected.get("age", 10) if expected else 10
        
        # Simple readability heuristics
        words = output.split()
        word_count = len(words)
        
        if word_count == 0:
            return MetricResult(
                metric_name=self.name,
                passed=False,
                score=0.0,
                details="Empty story",
            )
        
        # Count sentence-ending punctuation
        sentence_count = output.count('.') + output.count('!') + output.count('?')
        sentence_count = max(sentence_count, 1)
        
        # Average sentence length
        avg_sentence_length = word_count / sentence_count
        
        # Get threshold for target age
        threshold = self.SYLLABLE_THRESHOLDS.get(
            target_age, 
            self.SYLLABLE_THRESHOLDS[min(self.SYLLABLE_THRESHOLDS.keys(), 
                                         key=lambda k: abs(k - target_age))]
        )
        
        # Younger kids should have shorter sentences
        expected_sentence_length = target_age + 5  # Rough heuristic
        
        sentence_score = 1.0 if avg_sentence_length <= expected_sentence_length else (
            expected_sentence_length / avg_sentence_length
        )
        
        # Overall score
        score = sentence_score
        passed = score >= 0.7
        
        return MetricResult(
            metric_name=self.name,
            passed=passed,
            score=score,
            details=f"Target age {target_age}: avg sentence length {avg_sentence_length:.1f}",
            metadata={
                "target_age": target_age,
                "avg_sentence_length": avg_sentence_length,
                "word_count": word_count,
            },
        )

