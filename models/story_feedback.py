"""
Story Feedback model for quality review loop.

Lightweight model for critic feedback during iterative refinement.
"""

from pydantic import BaseModel, Field


class StoryFeedback(BaseModel):
    """Feedback from quality critic.
    
    Attributes:
        status: Either "APPROVED" or "NEEDS_REVISION"
        feedback: Specific suggestions if revision needed, empty if approved
    """
    
    status: str = Field(
        description="Either 'APPROVED' if story meets quality standards, or 'NEEDS_REVISION' if improvements needed",
    )
    
    feedback: str = Field(
        description="If status is NEEDS_REVISION: 2-3 specific, actionable suggestions for improvement. If APPROVED: empty string",
        default="",
    )

