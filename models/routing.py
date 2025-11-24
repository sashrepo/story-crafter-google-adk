"""
Routing decision model for Story Crafter.

This model represents the router agent's classification of user requests.
"""

from pydantic import BaseModel, Field
from typing import Literal


class RoutingDecision(BaseModel):
    """Structured routing decision from the router agent.
    
    Attributes:
        decision: The classification of the user's request
        confidence: Optional confidence score for the decision
    """
    
    decision: Literal["NEW_STORY", "EDIT_STORY", "QUESTION"] = Field(
        description="The classification of the user's request."
    )
    confidence: float | None = Field(
        default=None,
        description="Confidence score for the routing decision (0-1)",
        ge=0.0,
        le=1.0,
    )

