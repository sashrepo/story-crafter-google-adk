"""
Memory Bank Configuration for Story Crafter.

This module defines custom memory topics that control what information
Memory Bank extracts and persists from user-agent conversations.

Simplified to focus on story content extraction for continuity.

Reference: https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/generate-memories
"""

from typing import Any


# ============================================================================
# STORY CONTENT TOPIC - The only custom topic we need
# ============================================================================

STORY_CONTENT_TOPIC = {
    "custom_memory_topic": {
        "label": "story_content",
        "description": """Extract and remember ALL important elements from generated stories:

FROM THE STORY TEXT, extract:
- Character names and descriptions (e.g., "Zara is a young wizard with silver hair")
- The setting and world details (e.g., "The story takes place in the floating city of Aethon")
- Major plot events that happened (e.g., "Zara discovered a hidden library beneath the castle")
- Relationships between characters (e.g., "Kira is Zara's mentor and teaches her fire magic")
- Any magical systems, abilities, or rules (e.g., "Magic requires speaking ancient words")
- Important objects or artifacts (e.g., "The Starlight Amulet can reveal hidden truths")
- Unresolved mysteries or cliffhangers (e.g., "The identity of the shadow figure is unknown")

FROM THE USER REQUEST, extract:
- What kind of story they asked for (e.g., "User requested a fantasy adventure story")
- Specific elements they wanted (e.g., "User wanted dragons and a young hero")

ALWAYS extract character names, settings, and key plot points from the model's story response.
This information is critical for story continuity in future sessions."""
    }
}


# ============================================================================
# COMBINED CONFIGURATION
# ============================================================================

def get_memory_topics() -> list[dict[str, Any]]:
    """
    Get all memory topics for Story Crafter.
    
    Returns:
        List of memory topic configurations.
    """
    return [
        STORY_CONTENT_TOPIC,
    ]


def get_customization_config() -> dict[str, Any]:
    """
    Get the full Memory Bank customization configuration.
    
    Returns:
        Dictionary with memory_topics configuration.
    """
    return {
        "memory_topics": get_memory_topics()
    }

