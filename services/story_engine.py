"""
Story Engine - Backend service for story generation and management.

This module encapsulates all agent orchestration, session management,
and story processing logic, keeping the frontend (app.py) clean and focused
on UI concerns.

Supports both InMemory and Vertex AI session/memory services.
"""

import json
import logging
import os
from typing import AsyncGenerator, Dict, Any, Optional

import vertexai
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.genai import types
from pydantic import ValidationError

# Import agent modules (factories)
from agents.router import agent as router_module
from agents.orchestrator.story_orchestrator import agent as orchestrator_module

# Import models for structured parsing
from models.routing import RoutingDecision

# Import safety check for pre-processing
from services.perspective import check_toxicity

# Constants
STORY_PREVIEW_MAX_LENGTH = 2000

logger = logging.getLogger(__name__)


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
    - Session management (InMemory or Vertex AI)
    - Memory retrieval and injection
    - Routing logic (create/edit/question)
    - Event streaming
    """
    
    def __init__(
        self, 
        session_service: Optional[InMemorySessionService] = None,
        memory_service: Optional[Any] = None,
        agent_engine_id: Optional[str] = None
    ):
        """
        Initialize the Story Engine.
        
        Args:
            session_service: Optional SessionService instance. 
                           If not provided, creates a new InMemorySessionService.
            memory_service: Optional MemoryService instance (Vertex AI or InMemory).
            agent_engine_id: Optional agent engine ID for Vertex AI services.
                           Required when using VertexAiSessionService.
        """
        self.session_service = session_service or InMemorySessionService()
        self.memory_service = memory_service
        
        # Determine the app_name to use for session operations
        # For Vertex AI, this needs to be the agent_engine_id
        # For InMemory, we can use any string like "agents"
        is_vertex = self._is_vertex_session_service()
        if is_vertex and agent_engine_id:
            self.app_name = agent_engine_id
        else:
            self.app_name = "agents"
    
    def _is_vertex_session_service(self) -> bool:
        """Check if using Vertex AI session service."""
        return "VertexAiSessionService" in self.session_service.__class__.__name__
        
    async def get_or_create_session(self, user_id: str, session_id: str):
        """
        Get existing session or create a new one.
        
        For Vertex AI, session IDs must be valid resource IDs (numeric).
        UUIDs from the frontend are detected and trigger new session creation.
        """
        try:
            is_vertex = self._is_vertex_session_service()
            
            if is_vertex:
                # UUIDs (with dashes) are not valid Vertex AI session IDs
                # Skip the get attempt and directly create a new session
                is_uuid_format = "-" in session_id
                
                if not is_uuid_format:
                    # Might be a valid Vertex AI ID, try to retrieve it
                    try:
                        session = await self.session_service.get_session(
                            app_name=self.app_name,
                            user_id=user_id,
                            session_id=session_id
                        )
                        return session
                    except Exception:
                        pass  # Fall through to create
                
                # Create new session - Vertex AI generates a valid resource ID
                session = await self.session_service.create_session(
                    app_name=self.app_name,
                    user_id=user_id
                )
                return session
            else:
                # InMemory path - try create first, then get
                try:
                    return await self.session_service.create_session(
                        app_name=self.app_name,
                        user_id=user_id,
                        session_id=session_id
                    )
                except Exception:
                    return await self.session_service.get_session(
                        app_name=self.app_name,
                        user_id=user_id,
                        session_id=session_id
                    )
        except Exception as e:
            logger.error(f"Error in get_or_create_session: {e}")
            raise
    
    def _get_session_id(self, session) -> str:
        """Extract the actual session ID from a session object."""
        if hasattr(session, 'id') and session.id:
            return session.id
        elif hasattr(session, 'name') and session.name:
            return session.name
        return ""
    
    async def determine_mode(
        self,
        prompt: str,
        user_id: str,
        session_id: str,
        has_current_story: bool
    ) -> str:
        """
        Determine the processing mode using the router agent.
        
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
        
        router_runner = Runner(
            agent=router_agent,
            app_name=self.app_name,
            session_service=self.session_service,
            memory_service=self.memory_service,
            plugins=[LoggingPlugin()]
        )
        
        router_input = types.Content(
            role="user",
            parts=[types.Part(text=f"User Input: {prompt}")]
        )
        
        # Resolve the actual session ID for Vertex AI
        try:
            session = await self.get_or_create_session(user_id, session_id)
            actual_session_id = self._get_session_id(session) or session_id
        except Exception:
            actual_session_id = session_id

        # Collect the router's response
        router_response_text = ""
        async for event in router_runner.run_async(
            user_id=user_id,
            session_id=actual_session_id,
            new_message=router_input
        ):
            if hasattr(event, 'content') and isinstance(event.content, str):
                router_response_text += event.content
            elif hasattr(event, 'content') and hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        router_response_text += part.text
        
        return self._parse_routing_decision(router_response_text)
    
    def _parse_routing_decision(self, router_response: str) -> str:
        """
        Parse the router agent's structured output into a mode string.
        
        Args:
            router_response: Raw JSON string from router agent
            
        Returns:
            Mode string: "create", "edit", or "question"
        """
        decision_to_mode = {
            "NEW_STORY": "create",
            "EDIT_STORY": "edit",
            "QUESTION": "question"
        }
        
        router_response = router_response.strip()
        
        if router_response.startswith('{'):
            try:
                router_data = json.loads(router_response)
                
                try:
                    routing_decision = RoutingDecision(**router_data)
                    return decision_to_mode.get(routing_decision.decision, "create")
                except ValidationError:
                    decision = router_data.get('decision', 'NEW_STORY')
                    return decision_to_mode.get(decision, "create")
                    
            except json.JSONDecodeError:
                pass
        
        # Fallback: string matching for malformed responses
        if "EDIT_STORY" in router_response:
            return "edit"
        elif "QUESTION" in router_response:
            return "question"
        elif "NEW_STORY" in router_response:
            return "create"
        
        return "create"
    
    async def _retrieve_memories(self, user_id: str, prompt: str) -> str:
        """
        Retrieve relevant memories for the user to inject into the prompt.
        
        Args:
            user_id: User identifier
            prompt: Current user prompt (used as search query)
            
        Returns:
            Formatted memory context string, or empty string if none found
        """
        if not self.memory_service or not hasattr(self.memory_service, 'search_memory'):
            return ""
        
        try:
            response = await self.memory_service.search_memory(
                query="story preferences",  # Broad query for user preferences
                app_name=self.app_name,
                user_id=user_id
            )
            
            if not hasattr(response, 'memories') or not response.memories:
                return ""
            
            memory_texts = []
            for mem in response.memories:
                if hasattr(mem, 'content') and hasattr(mem.content, 'parts'):
                    for part in mem.content.parts:
                        if hasattr(part, 'text') and part.text:
                            memory_texts.append(part.text)
                            break
            
            if memory_texts:
                return "\n\n**IMPORTANT USER PREFERENCES/MEMORIES:**\n" + "\n".join(f"- {m}" for m in memory_texts)
                
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")
        
        return ""
    
    async def _save_session_to_memory(self, user_id: str, session_id: str):
        """
        Save session events to long-term memory using Vertex Memory Bank.
        
        Args:
            user_id: User identifier
            session_id: Session identifier (resolved Vertex AI resource ID)
        """
        if not self.memory_service or not hasattr(self.memory_service, 'add_session_to_memory'):
            return
        
        try:
            # Refresh session to get all events including newly generated ones
            refreshed_session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            event_count = len(refreshed_session.events) if refreshed_session.events else 0
            logger.info(f"Saving session to memory: {event_count} events")
            
            await self.memory_service.add_session_to_memory(refreshed_session)
            logger.info(f"Memory generation initiated for session {session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to save session to memory: {e}")
    
    async def _save_story_content_to_memory(self, user_id: str, story_content: str, user_prompt: str):
        """
        Save story content directly as memories for continuity.
        
        This uses the generate_memories API with direct_memories_source to
        explicitly store story facts that might not be extracted automatically.
        
        Args:
            user_id: User identifier
            story_content: The generated story text
            user_prompt: The original user prompt
        """
        try:
            project = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            
            if not project or not self.app_name:
                logger.warning("Cannot save story content: missing project or agent_engine_id")
                return
            
            client = vertexai.Client(project=project, location=location)
            
            agent_engine_name = f"projects/{project}/locations/{location}/reasoningEngines/{self.app_name}"
            
            # Truncate story to avoid token limits
            story_preview = story_content[:STORY_PREVIEW_MAX_LENGTH] if len(story_content) > STORY_PREVIEW_MAX_LENGTH else story_content
            
            # Build conversation events that include the story
            # This helps Memory Bank extract story content
            events = [
                {
                    "content": {
                        "role": "user",
                        "parts": [{"text": user_prompt}]
                    }
                },
                {
                    "content": {
                        "role": "model",
                        "parts": [{"text": f"Here is the story I created:\n\n{story_preview}"}]
                    }
                }
            ]
            
            # Use generate_memories with direct contents to trigger extraction
            response = client.agent_engines.memories.generate(
                name=agent_engine_name,
                direct_contents_source={"events": events},
                scope={"user_id": user_id},
                config={"wait_for_completion": False}  # Don't block
            )
            
            logger.info(f"Story content memory generation initiated for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to save story content to memory: {e}")
    
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
            # ============================================================
            # PRE-CHECK: Safety validation BEFORE any session/LLM operations
            # This prevents unnecessary API calls and session writes for toxic content
            # ============================================================
            yield StoryEvent("status", "safety", "Running safety pre-check...")
            
            safety_result = check_toxicity(prompt)
            if not safety_result["safe"]:
                yield StoryEvent(
                    "error",
                    "safety_precheck",
                    f"Content Rejected: {safety_result['reason']}",
                    {"is_safety_violation": True, "score": safety_result["score"]}
                )
                return
            
            yield StoryEvent("status", "safety", "Safety pre-check passed")
            
            # Ensure session exists and get the valid session object
            session = await self.get_or_create_session(user_id, session_id)
            actual_session_id = self._get_session_id(session) or session_id
            
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
                app_name=self.app_name,
                session_service=self.session_service,
                memory_service=self.memory_service,
                plugins=[LoggingPlugin()]
            )
            
            # Retrieve and inject memories
            memory_context = await self._retrieve_memories(user_id, prompt)
            
            # Build the user prompt based on mode
            user_prompt = prompt
            
            if mode == "edit" and current_story:
                # For edit mode, include the current story in the prompt
                user_prompt = f"CURRENT STORY:\n{current_story}\n\nEDIT REQUEST:\n{prompt}"
                yield StoryEvent("status", "editor", "Preparing to edit story...")
            elif mode == "question" and current_story:
                # For question mode, include the story context
                user_prompt = f"STORY CONTEXT:\n{current_story}\n\nQUESTION:\n{prompt}"
            
            # Prepend memory context if available
            if memory_context:
                user_prompt = f"{memory_context}\n\n{user_prompt}"
                yield StoryEvent("status", "memory", "Applied user preferences from memory")
                
            user_message = types.Content(
                role="user",
                parts=[types.Part(text=user_prompt)]
            )
            
            # Stream agent responses
            iteration_count = 0
            final_story_content = ""  # Track the final story for memory saving
            
            async for event in runner.run_async(
                user_id=user_id,
                session_id=actual_session_id,
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
                            final_story_content = content_text  # Track refined story
                            yield StoryEvent(
                                "refined_story",
                                agent_name,
                                content_text,
                                {"iteration": iteration_count}
                            )
                            
                        elif agent_name == "story_writer_agent":
                            final_story_content = content_text  # Track initial draft
                            yield StoryEvent("draft_story", agent_name, content_text)
                            
                        elif agent_name == "story_editor_agent":
                            final_story_content = content_text  # Track edited story
                            yield StoryEvent("edited_story", agent_name, content_text)
                            
                        elif agent_name == "story_guide_agent":
                            yield StoryEvent("guide_answer", agent_name, content_text)
                        
                        else:
                            yield StoryEvent("agent_output", agent_name, content_text)
            
            # Save session to memory for future context
            yield StoryEvent("status", "memory", "Saving session to memory...")
            await self._save_session_to_memory(user_id, actual_session_id)
            
            # Explicitly save story content to memory for extraction
            if final_story_content:
                yield StoryEvent("status", "memory", "Saving story content to memory...")
                await self._save_story_content_to_memory(user_id, final_story_content, prompt)
            
            yield StoryEvent("status", "memory", "Memory saved")

            # Signal completion
            yield StoryEvent("complete", "engine", "Story processing complete")
            
        except Exception as e:
            logger.error(f"Error processing story request: {e}")
            yield StoryEvent("error", "engine", str(e))
    
    def _extract_content_text(self, content) -> str:
        """Extract text from event content, handling None values safely."""
        content_text = ""
        
        if hasattr(content, 'parts'):
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    content_text += part.text
        elif isinstance(content, str):
            content_text = content
        
        return content_text
