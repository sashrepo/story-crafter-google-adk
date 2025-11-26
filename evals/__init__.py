"""
Evaluation framework for Story Crafter ADK.

This package provides tools for evaluating the multi-agent story generation system
at unit, integration, and end-to-end levels.

Usage:
    # Run evals programmatically
    from evals import EvalRunner, EvalDataset, RouteAccuracy
    
    runner = EvalRunner(verbose=True)
    summary = await runner.run_router_evals()
    summary.print_summary()
    
    # Run via CLI
    uv run python -m evals.runner
    
    # Run via pytest
    uv run pytest tests/test_evals.py -v
"""

from .datasets import EvalDataset, EvalCase
from .metrics import (
    Metric,
    MetricResult,
    RouteAccuracy,
    StructuredOutputValidity,
    StoryQualityScore,
    SafetyCompliance,
    AgeAppropriatenessScore,
)
from .runner import EvalRunner, EvalResult, EvalSummary

__all__ = [
    # Datasets
    "EvalDataset",
    "EvalCase",
    # Metrics
    "Metric",
    "MetricResult",
    "RouteAccuracy",
    "StructuredOutputValidity",
    "StoryQualityScore",
    "SafetyCompliance",
    "AgeAppropriatenessScore",
    # Runner
    "EvalRunner",
    "EvalResult",
    "EvalSummary",
]
