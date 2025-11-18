"""
User Intent data model for Story Crafter.

This model captures structured information extracted from natural language
story requests by the User Intent Agent.
"""

from typing import Optional

from pydantic import BaseModel, Field


class UserIntent(BaseModel):
    """Structured representation of a user's story request.
    
    Attributes:
        age: Target age of the audience (e.g., 5, 8, 12)
        themes: Story themes or topics (e.g., ["mermaids", "adventure", "friendship"])
        tone: Desired emotional tone (e.g., "calming", "exciting", "mysterious")
        genre: Story genre (e.g., "fantasy", "sci-fi", "adventure", "bedtime")
        length_minutes: Approximate reading/listening time in minutes
        safety_constraints: Optional content restrictions (e.g., ["no scary elements", "no violence"])
    """
    
    age: int = Field(
        description="Target age of the audience in years",
        ge=1,
        le=100,
    )
    themes: list[str] = Field(
        description="List of story themes, topics, or elements requested",
        min_length=1,
    )
    tone: str = Field(
        description="Desired emotional tone or mood of the story",
        min_length=1,
    )
    genre: str = Field(
        description="Story genre or category",
        min_length=1,
    )
    length_minutes: int = Field(
        description="Approximate story length in minutes",
        ge=1,
        le=120,
    )
    safety_constraints: Optional[list[str]] = Field(
        default=None,
        description="Optional list of content restrictions or safety requirements",
    )

