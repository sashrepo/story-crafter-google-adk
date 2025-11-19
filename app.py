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
    import agents.user_intent.agent
    import agents.worldbuilder.agent
    import agents.character_forge.agent
    import agents.plot_architect.agent
    import agents.story_writer.agent
    
    # Reload modules to ensure fresh clients for each run
    importlib.reload(agents.user_intent.agent)
    importlib.reload(agents.worldbuilder.agent)
    importlib.reload(agents.character_forge.agent)
    importlib.reload(agents.plot_architect.agent)
    importlib.reload(agents.story_writer.agent)
    importlib.reload(agents.orchestrator.story_orchestrator.agent)
    
    from agents.orchestrator.story_orchestrator.agent import story_orchestrator
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.info("Make sure you have installed the package dependencies.")
    st.stop()

# Initialize Session Service
def get_session_service():
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
    - 🎭 **User Intent**: Understands request
    - 🌍 **Worldbuilder**: Creates the setting
    - 👥 **Character Forge**: Creates characters
    - 📈 **Plot Architect**: Structures the narrative
    - ✍️ **Story Writer**: Writes the content
    """)

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
        with st.spinner("🤖 Orchestrating agents... (This may take 1-2 minutes)"):
            try:
                # Setup Runner
                runner = Runner(
                    agent=story_orchestrator,
                    app_name="story-crafter-adk",
                    session_service=session_service
                )
                
                # Manage Session
                user_id = "streamlit_user"
                
                # Check if session needs to be created
                should_create_session = False
                if "session_id" not in st.session_state:
                    should_create_session = True
                    new_session_id = str(uuid.uuid4())
                else:
                    # Check if session exists in the (potentially new) service
                    existing_session = asyncio.run(session_service.get_session(
                        app_name="story-crafter-adk",
                        user_id=user_id,
                        session_id=st.session_state.session_id
                    ))
                    if not existing_session:
                        should_create_session = True
                        new_session_id = st.session_state.session_id

                if should_create_session:
                    asyncio.run(session_service.create_session(
                        app_name="story-crafter-adk",
                        user_id=user_id,
                        session_id=new_session_id
                    ))
                    st.session_state.session_id = new_session_id
                
                session_id = st.session_state.session_id
                
                # Run
                # Note: This is synchronous and might block the UI. 
                events = runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=types.UserContent(parts=[types.Part(text=user_request)])
                )
                
                # Display results
                with results_placeholder:
                    st.markdown("### 📘 Generated Story Output")
                    
                    for event in events:
                        # Display event content
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
                                with st.expander(f"Output from: **{agent_name}**", expanded=True):
                                    st.markdown(content_text)

                st.success("Generation Complete!")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)

