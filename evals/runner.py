"""
Evaluation runner for Story Crafter agents.

Orchestrates running eval cases against agents and collecting results.

Usage:
    # Programmatic usage
    runner = EvalRunner(verbose=True)
    summary = await runner.run_router_evals()
    summary.print_summary()
    runner.save_results(summary)
    
    # CLI usage
    uv run python -m evals.runner
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .datasets import EvalCase, EvalDataset
from .metrics import Metric, MetricResult


@dataclass
class EvalResult:
    """Result of running a single eval case."""
    
    case_id: str
    input: str
    output: str
    metrics: list[MetricResult]
    latency_ms: float
    passed: bool
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def score(self) -> float:
        """Average score across all metrics."""
        if not self.metrics:
            return 0.0
        return sum(m.score for m in self.metrics) / len(self.metrics)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "case_id": self.case_id,
            "input": self.input,
            "output": self.output,
            "metrics": [
                {
                    "name": m.metric_name,
                    "passed": m.passed,
                    "score": m.score,
                    "details": m.details,
                }
                for m in self.metrics
            ],
            "latency_ms": self.latency_ms,
            "passed": self.passed,
            "score": self.score,
            "error": self.error,
            "timestamp": self.timestamp,
        }


@dataclass
class EvalSummary:
    """Summary of an evaluation run."""
    
    total_cases: int
    passed_cases: int
    failed_cases: int
    avg_score: float
    avg_latency_ms: float
    results: list[EvalResult]
    run_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    @property
    def pass_rate(self) -> float:
        """Percentage of cases that passed."""
        if self.total_cases == 0:
            return 0.0
        return self.passed_cases / self.total_cases
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "pass_rate": self.pass_rate,
            "avg_score": self.avg_score,
            "avg_latency_ms": self.avg_latency_ms,
            "results": [r.to_dict() for r in self.results],
        }
    
    def print_summary(self):
        """Print a human-readable summary."""
        print("\n" + "=" * 60)
        print(f"📊 EVALUATION SUMMARY - {self.run_id}")
        print("=" * 60)
        print(f"  Total Cases:  {self.total_cases}")
        print(f"  Passed:       {self.passed_cases} ({self.pass_rate:.1%})")
        print(f"  Failed:       {self.failed_cases}")
        print(f"  Avg Score:    {self.avg_score:.2f}")
        print(f"  Avg Latency:  {self.avg_latency_ms:.0f}ms")
        print("=" * 60)
        
        # Print failed cases
        failed = [r for r in self.results if not r.passed]
        if failed:
            print("\n❌ FAILED CASES:")
            for r in failed:
                print(f"\n  [{r.case_id}]")
                print(f"    Input:  {r.input[:60]}...")
                print(f"    Output: {r.output[:60]}..." if r.output else "    Output: <empty>")
                for m in r.metrics:
                    if not m.passed:
                        print(f"    ⚠️  {m.metric_name}: {m.details}")


class EvalRunner:
    """
    Runs evaluation cases against Story Crafter agents.
    
    Usage:
        runner = EvalRunner()
        
        # Run router evals
        summary = await runner.run_router_evals()
        summary.print_summary()
        
        # Run specific cases
        results = await runner.run_cases(
            cases=EvalDataset.get_by_tags("router", "edge_case"),
            agent_factory=create_router_agent,
            metrics=[RouteAccuracy()],
        )
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.session_service = InMemorySessionService()
    
    async def run_agent(
        self,
        agent,
        user_message: str,
        session_id: str = "eval_session",
        user_id: str = "eval_user",
    ) -> str:
        """Run an agent and return its output."""
        
        # Use "agents" as app_name to match the project structure
        app_name = "agents"
        
        runner = Runner(
            agent=agent,
            app_name=app_name,
            session_service=self.session_service,
        )
        
        # Create or get session
        try:
            session = await self.session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
        except Exception:
            session = await self.session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
        
        # Create proper Content object (ADK requires this format)
        content = types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        )
        
        # Run agent
        outputs = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            outputs.append(part.text)
                elif isinstance(event.content, str):
                    outputs.append(event.content)
        
        return "\n".join(outputs)
    
    async def run_case(
        self,
        case: EvalCase,
        agent_factory: Callable,
        metrics: list[Metric],
    ) -> EvalResult:
        """Run a single eval case."""
        
        if self.verbose:
            print(f"  Running case: {case.id}")
        
        start_time = time.time()
        error = None
        output = ""
        
        try:
            # Create fresh agent instance
            agent = agent_factory()
            
            # Use a unique session ID with timestamp to avoid conflicts
            unique_session_id = f"eval_{case.id}_{int(time.time() * 1000)}"
            
            # Run agent
            output = await self.run_agent(
                agent=agent,
                user_message=case.input,
                session_id=unique_session_id,
            )
            
        except Exception as e:
            error = str(e)
            if self.verbose:
                print(f"    Error: {e}")
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Evaluate metrics
        metric_results = []
        for metric in metrics:
            try:
                # Determine expected value based on metric type
                if metric.name == "route_accuracy":
                    expected = case.expected_route
                elif metric.name.startswith("structured_output_validity"):
                    expected = case.expected_intent
                elif metric.name == "safety_compliance":
                    expected = case.expected_behavior
                else:
                    expected = case.metadata
                
                result = metric.evaluate(output, expected)
                metric_results.append(result)
                
            except Exception as e:
                metric_results.append(MetricResult(
                    metric_name=metric.name,
                    passed=False,
                    score=0.0,
                    details=f"Metric evaluation error: {e}",
                ))
        
        # Determine overall pass/fail
        passed = all(m.passed for m in metric_results) and error is None
        
        return EvalResult(
            case_id=case.id,
            input=case.input,
            output=output,
            metrics=metric_results,
            latency_ms=latency_ms,
            passed=passed,
            error=error,
        )
    
    async def run_cases(
        self,
        cases: list[EvalCase],
        agent_factory: Callable,
        metrics: list[Metric],
    ) -> EvalSummary:
        """Run multiple eval cases and return summary."""
        
        results = []
        for case in cases:
            result = await self.run_case(case, agent_factory, metrics)
            results.append(result)
        
        # Compute summary stats
        passed_cases = sum(1 for r in results if r.passed)
        avg_score = sum(r.score for r in results) / len(results) if results else 0.0
        avg_latency = sum(r.latency_ms for r in results) / len(results) if results else 0.0
        
        return EvalSummary(
            total_cases=len(results),
            passed_cases=passed_cases,
            failed_cases=len(results) - passed_cases,
            avg_score=avg_score,
            avg_latency_ms=avg_latency,
            results=results,
        )
    
    async def run_router_evals(self) -> EvalSummary:
        """Run all router agent evaluations."""
        from agents.router.agent import create_agent
        from .metrics import RouteAccuracy
        
        print("\n🚦 Running Router Agent Evals...")
        
        return await self.run_cases(
            cases=EvalDataset.ROUTER_CASES,
            agent_factory=create_agent,
            metrics=[RouteAccuracy()],
        )
    
    async def run_safety_evals(self) -> EvalSummary:
        """Run all safety agent evaluations."""
        from agents.safety.agent import create_agent
        from .metrics import SafetyCompliance
        
        print("\n🛡️ Running Safety Agent Evals...")
        
        return await self.run_cases(
            cases=EvalDataset.SAFETY_CASES,
            agent_factory=create_agent,
            metrics=[SafetyCompliance()],
        )
    
    def save_results(self, summary: EvalSummary, output_dir: str = "eval_results"):
        """Save evaluation results to JSON file."""
        
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"eval_{summary.run_id}.json")
        
        with open(filepath, "w") as f:
            json.dump(summary.to_dict(), f, indent=2)
        
        print(f"\n💾 Results saved to: {filepath}")
        return filepath


async def main():
    """Run all evaluations."""
    
    runner = EvalRunner(verbose=True)
    
    # Run router evals
    router_summary = await runner.run_router_evals()
    router_summary.print_summary()
    runner.save_results(router_summary)
    
    # # Uncomment to run safety evals (requires Perspective API key)
    # safety_summary = await runner.run_safety_evals()
    # safety_summary.print_summary()
    # runner.save_results(safety_summary)


if __name__ == "__main__":
    asyncio.run(main())

