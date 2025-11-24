"""
Story Engine - Backend service for story generation and management.

This module encapsulates all agent orchestration, session management,
and story processing logic, keeping the frontend (app.py) clean and focused
on UI concerns.
"""

import json
import uuid
from typing import AsyncGenerator, Dict, Any, Optional
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import agent modules (factories)
from agents.router import agent as router_module
from agents.orchestrator.story_orchestrator import agent as orchestrator_module


class StoryEvent:
    """Represents an event during story processing."""
    
    def __init__(
        self,
        event_type: str,
        agent_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.event_type = event_type  # "status", "content", "error", "complete"
        self.agent_name = agent_name
        self.content = content
        self.metadata = metadata or {}


class StoryEngine:
    """
    Backend service that handles story generation, editing, and management.
    
    This class encapsulates:
    - Agent orchestration
    - Session management (InMemory)
    - Routing logic (create/edit/question)
    - Event streaming
    """
    
    def __init__(self, session_service: Optional[InMemorySessionService] = None):
        """
        Initialize the Story Engine.
        
        Args:
            session_service: Optional InMemorySessionService instance. 
                           If not provided, creates a new InMemorySessionService.
        """
        self.session_service = session_service or InMemorySessionService()
        
    async def get_or_create_session(self, user_id: str, session_id: str):
        """Get existing session or create a new one."""
        try:
            return await self.session_service.create_session(
                app_name="agents",
                user_id=user_id,
                session_id=session_id
            )
        except:
            return await self.session_service.get_session(
                app_name="agents",
                user_id=user_id,
                session_id=session_id
            )
    
    async def determine_mode(
        self,
        prompt: str,
        user_id: str,
        session_id: str,
        has_current_story: bool
    ) -> str:
        """
        Determine the processing mode (create/edit/question) using the router agent.
        
        Args:
            prompt: User input
            user_id: User identifier
            session_id: Session identifier
            has_current_story: Whether there's an active story in the session
            
        Returns:
            Mode string: "create", "edit", or "question"
        """
        # Default to create if no story exists
        if not has_current_story:
            return "create"
        
        # Create fresh router agent
        router_agent = router_module.create_agent()
        
        # Run router agent
        router_runner = Runner(
            agent=router_agent,
            app_name="agents",
            session_service=self.session_service
        )
        
        router_input = types.Content(
            role="user",
            parts=[types.Part(text=f"User Input: {prompt}")]
        )
        
        router_response_text = ""
        async for event in router_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=router_input
        ):
            if hasattr(event, 'content') and isinstance(event.content, str):
                router_response_text += event.content
            elif hasattr(event, 'content') and hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    router_response_text += part.text
        
        # Parse decision
        mode = "create"  # Default
        
        # Try JSON parsing first
        if router_response_text.strip().startswith('{'):
            try:
                router_data = json.loads(router_response_text)
                mode = router_data.get('mode', 'create')
            except json.JSONDecodeError:
                pass
        
        # Fallback to string matching
        if "EDIT_STORY" in router_response_text:
            mode = "edit"
        elif "QUESTION" in router_response_text:
            mode = "question"
        elif "NEW_STORY" in router_response_text:
            mode = "create"
        
        return mode
    
    async def process_story_request(
        self,
        prompt: str,
        user_id: str,
        session_id: str,
        current_story: str = "",
        enable_refinement: bool = True
    ) -> AsyncGenerator[StoryEvent, None]:
        """
        Process a story request and stream events back.
        
        Args:
            prompt: User's input prompt
            user_id: User identifier
            session_id: Session identifier
            current_story: Current story text (if editing)
            enable_refinement: Whether to enable quality refinement loop
            
        Yields:
            StoryEvent objects representing the processing progress
        """
        try:
            # Ensure session exists
            await self.get_or_create_session(user_id, session_id)
            
            # Determine mode
            yield StoryEvent("status", "router", "Analyzing request...")
            
            has_story = bool(current_story and current_story.strip())
            mode = await self.determine_mode(prompt, user_id, session_id, has_story)
            
            yield StoryEvent("status", "router", f"Mode determined: {mode.upper()}", {"mode": mode})
            
            # Get fresh orchestrator
            orchestrator = orchestrator_module.create_orchestrator(
                enable_refinement=enable_refinement, 
                mode=mode
            )
            
            # Create runner
            runner = Runner(
                agent=orchestrator,
                app_name="agents",
                session_service=self.session_service
            )
            
            # Create user message
            user_message = types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
            
            # Stream agent responses
            iteration_count = 0
            
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message
            ):
                if hasattr(event, 'content') and event.content:
                    content_text = self._extract_content_text(event.content)
                    
                    if content_text.strip():
                        agent_name = getattr(event, 'author', 'Unknown Agent')
                        
                        # Route based on agent
                        if agent_name == "quality_critic":
                            iteration_count += 1
                            is_approved = "APPROVED" in content_text
                            
                            yield StoryEvent(
                                "critique",
                                agent_name,
                                content_text,
                                {
                                    "iteration": iteration_count,
                                    "approved": is_approved
                                }
                            )
                            
                        elif agent_name == "story_refiner":
                            yield StoryEvent(
                                "refined_story",
                                agent_name,
                                content_text,
                                {"iteration": iteration_count}
                            )
                            
                        elif agent_name == "story_writer_agent":
                            yield StoryEvent("draft_story", agent_name, content_text)
                            
                        elif agent_name == "story_editor_agent":
                            yield StoryEvent("edited_story", agent_name, content_text)
                            
                        elif agent_name == "story_guide_agent":
                            yield StoryEvent("guide_answer", agent_name, content_text)
                            
                        elif agent_name == "safety_agent":
                            if "Content Rejected" in content_text:
                                yield StoryEvent("error", agent_name, content_text, {"is_safety_violation": True})
                                return  # Stop processing
                            else:
                                yield StoryEvent("status", agent_name, "Safety check passed")
                        
                        else:
                            # Generic agent output
                            yield StoryEvent("agent_output", agent_name, content_text)
            
            # Signal completion
            yield StoryEvent("complete", "engine", "Story processing complete")
            
        except Exception as e:
            yield StoryEvent("error", "engine", str(e))
    
    def _extract_content_text(self, content) -> str:
        """Extract text from event content."""
        content_text = ""
        
        if hasattr(content, 'parts'):
            for part in content.parts:
                if hasattr(part, 'text'):
                    content_text += part.text
        elif isinstance(content, str):
            content_text = content
        
        return content_text
