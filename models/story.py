"""
Story data model for Story Crafter.

This model captures the final narrative prose output from the Story Writer Agent.
"""

from typing import Optional

from pydantic import BaseModel, Field


class StoryModel(BaseModel):
    """Structured representation of a complete story.
    
    This model contains the final narrative prose along with metadata
    about the story's structure and content.
    
    Attributes:
        title: Story title
        text: The complete narrative prose
        word_count: Total number of words in the story
        estimated_reading_time_minutes: Estimated reading time
        tone: The narrative tone/mood
        reading_level: Age-appropriate reading level description
    """
    
    title: str = Field(
        description="The story's title",
        min_length=1,
    )
    text: str = Field(
        description="The complete narrative prose of the story",
        min_length=100,
    )
    word_count: int = Field(
        description="Total number of words in the story",
        ge=50,
    )
    estimated_reading_time_minutes: int = Field(
        description="Estimated reading time in minutes at average reading speed",
        ge=1,
    )
    tone: str = Field(
        description="The narrative tone/mood (e.g., 'whimsical', 'adventurous', 'calming')",
        min_length=1,
    )
    reading_level: str = Field(
        description="Age-appropriate reading level description (e.g., 'Early reader (ages 5-7)', 'Middle grade (ages 8-12)')",
        min_length=1,
    )

