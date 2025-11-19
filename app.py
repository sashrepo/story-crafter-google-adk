import asyncio
import streamlit as st
import os
import uuid
from pathlib import Path
import sys
import importlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import ADK components
try:
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    
    # Import agent modules to reload them
    import agents.orchestrator.story_orchestrator.agent
    import agents.safety.agent
    import agents.user_intent.agent
    import agents.worldbuilder.agent
    import agents.character_forge.agent
    import agents.plot_architect.agent
    import agents.story_writer.agent
    import agents.story_quality_loop.agent
    
    # Reload modules to ensure fresh clients for each run
    importlib.reload(agents.safety.agent)
    importlib.reload(agents.user_intent.agent)
    importlib.reload(agents.worldbuilder.agent)
    importlib.reload(agents.character_forge.agent)
    importlib.reload(agents.plot_architect.agent)
    importlib.reload(agents.story_writer.agent)
    importlib.reload(agents.story_quality_loop.agent)
    importlib.reload(agents.orchestrator.story_orchestrator.agent)
    
    from agents.orchestrator.story_orchestrator.agent import get_orchestrator
    from services.perspective import SafetyViolationError
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.info("Make sure you have installed the package dependencies.")
    st.stop()

# Initialize Session Service - MUST be cached to persist across Streamlit reruns!
@st.cache_resource
def get_session_service():
    """Create and cache the session service so it persists across Streamlit reruns."""
    return InMemorySessionService()

session_service = get_session_service()

# Page config
st.set_page_config(
    page_title="Story Crafter ADK",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and Header
st.title("📚 Story Crafter ADK")
st.markdown("""
Generate immersive multi-agent stories using the **Google Agent Development Kit (ADK)**.
This system orchestrates multiple AI agents to create plots, characters, worlds, and stories.
""")

# Sidebar
with st.sidebar:
    st.markdown("### 🤖 Agents Active")
    st.markdown("""
    - 🛡️ **Safety**: Checks content safety
    - 🎭 **User Intent**: Understands request
    - 🌍 **Worldbuilder**: Creates the setting
    - 👥 **Character Forge**: Creates characters
    - 📈 **Plot Architect**: Structures the narrative
    - ✍️ **Story Writer**: Creates initial draft
    - 🔁 **Quality Loop**: Reviews & refines (max 3 iterations)
    """)

    st.markdown("---")
    
    # Debug: Show current session info
    st.markdown("### 🔍 Session Info")
    if "session_id" in st.session_state:
        st.success(f"✅ Active Session")
        st.code(st.session_state.session_id[:8] + "...", language=None)
        
        # Show session message count
        try:
            user_id = "streamlit_user"
            session = asyncio.run(session_service.get_session(
                app_name="agents",
                user_id=user_id,
                session_id=st.session_state.session_id
            ))
            if session:
                # Check for conversation data
                message_count = 0
                if hasattr(session, 'events'):
                    message_count = len(session.events)
                elif hasattr(session, 'messages'):
                    message_count = len(session.messages)
                elif hasattr(session, 'history'):
                    message_count = len(session.history)
                
                st.metric("Conversation Events", message_count)
            else:
                st.warning("Session not found in service")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.info("No active session")
    
    st.markdown("---")
    if st.button("🔄 Start New Story", type="secondary"):
        if "session_id" in st.session_state:
            del st.session_state.session_id
        st.rerun()

# Main Content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Story Request")
    default_prompt = """Create a 5-minute bedtime story for my 8-year-old daughter.
She loves mermaids, gymnastics, and stories about being brave.
Keep it calming and appropriate for bedtime."""
    
    user_request = st.text_area(
        "Describe the story you want:", 
        value=default_prompt,
        height=150
    )
    
    # Add refinement toggle
    enable_refinement = st.checkbox(
        "🔁 Enable Quality Refinement Loop",
        value=True,
        help="When enabled, the story will be reviewed and refined up to 3 times for better quality. Disable for faster generation."
    )
    
    generate_btn = st.button("✨ Generate Story", type="primary", disabled=not os.environ.get("GOOGLE_API_KEY"))

with col2:
    st.info("💡 **Tip:** Be specific about the genre, length, and audience for better results.")

# Results container
st.divider()
results_placeholder = st.container()

if generate_btn and user_request:
    if not os.environ.get("GOOGLE_API_KEY"):
        st.error("Please set your Google API Key in the sidebar.")
    else:
        spinner_text = "🤖 Generating story with quality refinement... (This may take 2-3 minutes)" if enable_refinement else "🤖 Generating story... (This may take 30-60 seconds)"
        with st.spinner(spinner_text):
            try:
                # Manage Session
                user_id = "streamlit_user"
                
                # Generate or reuse session_id
                if "session_id" not in st.session_state:
                    st.session_state.session_id = str(uuid.uuid4())
                
                session_id = st.session_state.session_id
                
                # Create or get session
                try:
                    session = asyncio.run(session_service.create_session(
                        app_name="agents",
                        user_id=user_id,
                        session_id=session_id
                    ))
                except Exception:
                    # Session might already exist, retrieve it
                    session = asyncio.run(session_service.get_session(
                        app_name="agents",
                        user_id=user_id,
                        session_id=session_id
                    ))
                    if not session:
                        st.error("Failed to create or retrieve session.")
                        st.stop()
                
                # Get the appropriate orchestrator from backend
                orchestrator = get_orchestrator(enable_refinement=enable_refinement)
                
                # Setup Runner
                runner = Runner(
                    agent=orchestrator,
                    app_name="agents",
                    session_service=session_service
                )
                
                # Convert user message to proper Content format
                user_message = types.Content(
                    role="user",
                    parts=[types.Part(text=user_request)]
                )
                
                # Display results with streaming
                iteration_count = [0]  # Use list to allow modification in nested function
                critique_texts = []
                
                with results_placeholder:
                    st.markdown("### 📘 Generated Story Output")
                    
                    # Process events one by one as they arrive
                    async def process_events_async():
                        try:
                            async for event in runner.run_async(
                                user_id=user_id,
                                session_id=session.id,
                                new_message=user_message
                            ):
                                if hasattr(event, 'content') and event.content:
                                    # Extract text from Content object
                                    content_text = ""
                                    if hasattr(event.content, 'parts'):
                                        for part in event.content.parts:
                                            if hasattr(part, 'text') and part.text:
                                                content_text += part.text
                                    elif isinstance(event.content, str):
                                        content_text = event.content
                                    
                                    if content_text.strip():
                                        agent_name = getattr(event, 'author', 'Unknown Agent')
                                        
                                        # Special handling for loop agents
                                        if agent_name == "quality_critic":
                                            iteration_count[0] += 1
                                            critique_texts.append(content_text)
                                            if "APPROVED" in content_text:
                                                st.success(f"✅ Story approved after {iteration_count[0]} iteration(s)!")
                                            else:
                                                st.warning(f"🔄 Iteration {iteration_count[0]}: Refining story based on feedback...")
                                            with st.expander(f"Critique #{iteration_count[0]}", expanded=False):
                                                st.markdown(content_text)
                                        
                                        elif agent_name == "story_refiner":
                                            with st.expander(f"📝 Refined Story (Iteration {iteration_count[0]})", expanded=(iteration_count[0] == len(critique_texts))):
                                                st.markdown(content_text)
                                        
                                        elif agent_name == "story_writer_agent":
                                            with st.expander(f"📝 Initial Story Draft", expanded=False):
                                                st.markdown(content_text)
                                                
                                        elif agent_name == "safety_agent":
                                            if "Content Rejected" in content_text:
                                                st.error(f"🛡️ {content_text}")
                                                st.stop()
                                            else:
                                                # Safety pass, show quietly
                                                with st.expander(f"🛡️ Safety Check Passed", expanded=False):
                                                    st.markdown(content_text)

                                        else:
                                            # Other agents (intent, world, character, plot)
                                            with st.expander(f"Output from: **{agent_name}**", expanded=False):
                                                st.markdown(content_text)
                        except Exception as e:
                            # Raise other exceptions to be caught by the outer handler
                            # But check if it's a safety violation wrapped in another exception
                            if "SafetyViolationError" in str(e) or "Content Rejected" in str(e):
                                raise SafetyViolationError(str(e))
                            raise e
                    
                    # Run the async processing
                    asyncio.run(process_events_async())

                # After all events are processed
                if enable_refinement:
                    st.success(f"✨ Story Generation Complete! ({iteration_count[0]} quality iteration(s))")
                else:
                    st.success(f"✨ Story Generation Complete! (Fast mode - no refinement)")
                    
            except ExceptionGroup as eg:
                st.error(f"⚠️ Multiple errors occurred in parallel execution:")
                for i, e in enumerate(eg.exceptions):
                    st.error(f"Error {i+1}: {type(e).__name__}: {str(e)}")
            except SafetyViolationError as e:
                st.error(f"🛡️ Content Safety Alert: {str(e)}")
            except Exception as e:
                # Check if it's a wrapped safety violation
                if "SafetyViolationError" in str(e) or "Content Rejected" in str(e):
                     st.error(f"🛡️ Content Safety Alert: {str(e)}")
                else:
                    st.error(f"An error occurred: {type(e).__name__}: {str(e)}")
                    st.exception(e)
