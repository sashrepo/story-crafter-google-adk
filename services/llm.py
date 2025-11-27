"""
Shared configuration for Story Crafter agents.

This module contains common configurations like retry settings
that are applied across all agents.
"""

from google.genai import types
from google.adk.models.google_llm import Gemini

# Shared retry configuration for all agents
RETRY_CONFIG = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,  # Initial delay in seconds
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# Helper function to create model instances with retry config
def create_gemini_model(model_name: str) -> Gemini:
    """Create a Gemini model instance with shared retry configuration.
    
    Args:
        model_name: The Gemini model name (e.g., "gemini-2.5-flash", "gemini-2.5-pro")
        
    Returns:
        Gemini model instance with retry configuration
    """
    return Gemini(
        model=model_name,
        retry_options=RETRY_CONFIG
    )

