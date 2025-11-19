import asyncio
import streamlit as st
import os
import uuid
import json
import datetime
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

# --- Helper Functions for Story Library ---
LIBRARY_FILE = "story_library.json"

def load_library():
    if os.path.exists(LIBRARY_FILE):
        try:
            with open(LIBRARY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_to_library(story_text, session_id, user_id):
    library = load_library()
    # Check if already exists (simple check)
    for item in library:
        if item['session_id'] == session_id and item['story_text'] == story_text:
            return
            
    library.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now().isoformat(),
        "session_id": session_id,
        "user_id": user_id,
        "story_text": story_text,
        "snippet": story_text[:100] + "..."
    })
    with open(LIBRARY_FILE, "w") as f:
        json.dump(library, f, indent=2)
        
    # Update session state immediately
    st.session_state.library = library

def render_library_list(container):
    with container.container():
        st.subheader("📚 Story Library")
        library = st.session_state.get("library", load_library())
        
        if not library:
            st.info("No approved stories yet.")
        else:
            for item in reversed(library):
                with st.expander(f"{item['timestamp'][:16]} ({item['user_id']})"):
                    st.markdown(item['story_text'])
                    st.caption(f"Session: {item['session_id']}")

# --- Session Management ---

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = "user_" + str(uuid.uuid4())[:8]
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "library" not in st.session_state:
        st.session_state.library = load_library()

init_session_state()

# --- Sidebar ---
with st.sidebar:
    st.title("Story Controls")
    
    # User & Session Config
    st.subheader("👤 Identity")
    new_user_id = st.text_input("User ID", value=st.session_state.user_id)
    if new_user_id != st.session_state.user_id:
        st.session_state.user_id = new_user_id
        
    new_session_id = st.text_input("Session ID", value=st.session_state.session_id)
    if new_session_id != st.session_state.session_id:
        st.session_state.session_id = new_session_id
        st.session_state.messages = [] # Clear chat on manual session change
        st.rerun()

    if st.button("🔄 New Conversation", type="primary"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.divider()
    
    # Settings
    st.subheader("⚙️ Settings")
    enable_refinement = st.toggle(
        "Enable Quality Refinement",
        value=True,
        help="Reviews and refines story up to 3 times."
    )
    
    st.divider()
    
    # Story Library - Use Placeholder
    library_placeholder = st.empty()
    render_library_list(library_placeholder)

# --- Main Chat Interface ---

st.title("📚 Story Crafter Chat")
st.caption("Collaborate with AI agents to build your story.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        if message.get("is_expander"):
             with st.expander(message["title"], expanded=False):
                 st.markdown(message["content"])
        else:
            st.markdown(message["content"])

# Handle Input
if prompt := st.chat_input("What kind of story would you like to create?"):
    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Run Agent Process
    if not os.environ.get("GOOGLE_API_KEY"):
        st.error("Please set your Google API Key in the environment or sidebar.")
    else:
        with st.chat_message("assistant", avatar="🤖"):
            response_placeholder = st.empty()
            status_placeholder = st.status("Agents are working...", expanded=True)
            
            # Variables to track state during streaming
            state_tracker = {"final_story": ""}
            iteration_count = [0]
            
            async def run_chat_turn():
                # Setup Session
                user_id = st.session_state.user_id
                session_id = st.session_state.session_id
                
                try:
                    session = await session_service.create_session(
                        app_name="agents",
                        user_id=user_id,
                        session_id=session_id
                    )
                except:
                    session = await session_service.get_session(
                        app_name="agents",
                        user_id=user_id,
                        session_id=session_id
                    )
                
                orchestrator = get_orchestrator(enable_refinement=enable_refinement)
                runner = Runner(
                    agent=orchestrator,
                    app_name="agents",
                    session_service=session_service
                )
                
                user_message = types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )
                
                # Stream responses
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=user_message
                ):
                    if hasattr(event, 'content') and event.content:
                        content_text = ""
                        if hasattr(event.content, 'parts'):
                            for part in event.content.parts:
                                if hasattr(part, 'text'): content_text += part.text
                        elif isinstance(event.content, str):
                            content_text = event.content
                            
                        if content_text.strip():
                            agent_name = getattr(event, 'author', 'Unknown Agent')
                            
                            # Handle different agents
                            if agent_name == "quality_critic":
                                iteration_count[0] += 1
                                status_placeholder.write(f"Quality Check #{iteration_count[0]}: {content_text[:50]}...")
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": content_text, 
                                    "title": f"🔍 Critique #{iteration_count[0]}",
                                    "is_expander": True,
                                    "avatar": "🧐"
                                })
                                if "APPROVED" in content_text:
                                    status_placeholder.update(label="Story Approved!", state="complete")
                                
                            elif agent_name == "story_refiner":
                                status_placeholder.write(f"Refining Story (Iteration {iteration_count[0]})...")
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": content_text,
                                    "title": f"📝 Refined Draft (Iter {iteration_count[0]})",
                                    "is_expander": True,
                                    "avatar": "✍️"
                                })
                                state_tracker["final_story"] = content_text # Update candidate for final story

                            elif agent_name == "story_writer_agent":
                                status_placeholder.write("Drafting initial story...")
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": content_text,
                                    "title": "📝 Initial Draft",
                                    "is_expander": True,
                                    "avatar": "✍️"
                                })
                                state_tracker["final_story"] = content_text # Update candidate for final story
                            
                            elif agent_name == "safety_agent":
                                if "Content Rejected" in content_text:
                                    st.error(f"🛡️ Safety Rejection: {content_text}")
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": f"❌ Safety Rejection: {content_text}",
                                        "avatar": "🛡️"
                                    })
                                    return # Stop processing
                                else:
                                     status_placeholder.write("Safety check passed.")

                            else:
                                # Other agents (World, Character, Plot, etc.)
                                status_placeholder.write(f"{agent_name} is thinking...")
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": content_text,
                                    "title": f"Output: {agent_name}",
                                    "is_expander": True,
                                    "avatar": "🤖"
                                })

            # Run the async loop
            try:
                asyncio.run(run_chat_turn())
                status_placeholder.update(label="Generation Complete", state="complete", expanded=False)
                
                # If we have a final story, show it clearly at the end
                if state_tracker["final_story"]:
                    st.markdown("### ✨ Final Story")
                    st.markdown(state_tracker["final_story"])
                    
                    # Save to history as main response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": state_tracker["final_story"],
                        "avatar": "📖"
                    })
                    
                    # Automatically save to library if it looks like a story
                    if len(state_tracker["final_story"]) > 100:
                        save_to_library(state_tracker["final_story"], st.session_state.session_id, st.session_state.user_id)
                        st.toast("Story saved to library!", icon="💾")
                        
                        # Force update the library list in sidebar
                        render_library_list(library_placeholder)
                        
            except Exception as e:
                st.error(f"An error occurred: {e}")
                status_placeholder.update(label="Error", state="error")
