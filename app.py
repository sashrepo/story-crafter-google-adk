import asyncio
import streamlit as st
import os
import uuid
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import ADK components and services
try:
    # Import backend services
    from services.story_engine import StoryEngine
    from services.memory import get_session_service
    
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.info("Make sure you have installed the package dependencies.")
    st.stop()

# Initialize Services - MUST be cached to persist across Streamlit reruns!
# Session service is imported from services.memory module
session_service = get_session_service()

@st.cache_resource
def get_story_engine(_session_service):
    """Create and cache the story engine with the session service."""
    return StoryEngine(session_service=_session_service)

story_engine = get_story_engine(session_service)

# Page config
st.set_page_config(
    page_title="Story Crafter ADK",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Theme ---
import theme
theme.apply_google_kids_theme()

# --- Session Management ---
def init_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = "user_" + str(uuid.uuid4())[:8]
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "current_story" not in st.session_state:
        st.session_state.current_story = ""

init_session_state()

# --- Sidebar ---
with st.sidebar:
    theme.render_header()
    theme.render_custom_title("Story Controls")
    
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

# --- Main Chat Interface ---

theme.render_header()
theme.render_custom_title("Story Crafter Chat", "Collaborate with AI agents to build your story.")


# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        if message.get("is_expander"):
             with st.expander(message["title"], expanded=False):
                 st.markdown(message["content"])
        else:
            st.markdown(message["content"])

# Handle Input
if prompt := st.chat_input("✨ Imagine a story... type your idea here! 🚀"):
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
            status_placeholder = st.status("✨ Magic in progress... ✨", expanded=True)
            
            # Variables to track state during streaming
            state_tracker = {"final_story": "", "iteration_count": 0}
            
            async def run_chat_turn():
                user_id = st.session_state.user_id
                session_id = st.session_state.session_id
                
                # Process the story request using the backend engine
                async for event in story_engine.process_story_request(
                    prompt=prompt,
                    user_id=user_id,
                    session_id=session_id,
                    current_story=st.session_state.current_story,
                    enable_refinement=enable_refinement
                ):
                    # Handle different event types
                    if event.event_type == "status":
                        status_placeholder.write(event.content)
                        
                    elif event.event_type == "critique":
                        state_tracker["iteration_count"] = event.metadata.get("iteration", 0)
                        status_placeholder.write(f"Quality Check #{state_tracker['iteration_count']}: {event.content[:50]}...")
                        
                        # Render immediately in collapsed expander
                        with st.chat_message("assistant", avatar="🧐"):
                            with st.expander(f"🔍 Critique #{state_tracker['iteration_count']}", expanded=False):
                                st.markdown(event.content)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": event.content,
                            "title": f"🔍 Critique #{state_tracker['iteration_count']}",
                            "is_expander": True,
                            "avatar": "🧐"
                        })
                        if event.metadata.get("approved"):
                            status_placeholder.update(label="Story Approved!", state="complete")
                            
                    elif event.event_type == "refined_story":
                        status_placeholder.write(f"Refining Story (Iteration {state_tracker['iteration_count']})...")
                        
                        # Render immediately in collapsed expander
                        with st.chat_message("assistant", avatar="✍️"):
                            with st.expander(f"📝 Refined Draft (Iter {state_tracker['iteration_count']})", expanded=False):
                                st.markdown(event.content)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": event.content,
                            "title": f"📝 Refined Draft (Iter {state_tracker['iteration_count']})",
                            "is_expander": True,
                            "avatar": "✍️"
                        })
                        state_tracker["final_story"] = event.content
                        
                    elif event.event_type == "draft_story":
                        status_placeholder.write("Drafting initial story...")
                        
                        # Render immediately in collapsed expander
                        with st.chat_message("assistant", avatar="✍️"):
                            with st.expander("📝 Initial Draft", expanded=False):
                                st.markdown(event.content)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": event.content,
                            "title": "📝 Initial Draft",
                            "is_expander": True,
                            "avatar": "✍️"
                        })
                        state_tracker["final_story"] = event.content
                        
                    elif event.event_type == "edited_story":
                        status_placeholder.write("Editing story...")
                        
                        # Render immediately in collapsed expander
                        with st.chat_message("assistant", avatar="✍️"):
                            with st.expander("📝 Edited Story", expanded=False):
                                st.markdown(event.content)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": event.content,
                            "title": "📝 Edited Story",
                            "is_expander": True,
                            "avatar": "✍️"
                        })
                        state_tracker["final_story"] = event.content
                        
                    elif event.event_type == "guide_answer":
                        status_placeholder.write("Consulting Story Guide...")
                        
                        # Render the answer immediately in expanded format (user asked for this)
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(f"### 🤔 Guide's Answer\n\n{event.content}")
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": event.content,
                            "title": "🤔 Guide's Answer",
                            "is_expander": True,
                            "avatar": "🤖"
                        })
                        
                    elif event.event_type == "agent_output":
                        status_placeholder.write(f"{event.agent_name} is thinking...")
                        
                        # Render immediately in collapsed expander
                        with st.chat_message("assistant", avatar="🤖"):
                            with st.expander(f"Output: {event.agent_name}", expanded=False):
                                st.markdown(event.content)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": event.content,
                            "title": f"Output: {event.agent_name}",
                            "is_expander": True,
                            "avatar": "🤖"
                        })
                        
                    elif event.event_type == "error":
                        if event.metadata.get("is_safety_violation"):
                            st.error(f"🛡️ Safety Rejection: {event.content}")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"❌ Safety Rejection: {event.content}",
                                "avatar": "🛡️"
                            })
                        else:
                            raise Exception(event.content)
                        return  # Stop processing
                        
                    elif event.event_type == "complete":
                        status_placeholder.update(label="Generation Complete", state="complete", expanded=False)

            # Run the async loop
            try:
                asyncio.run(run_chat_turn())
                
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
                    
                    # Update current story for editing
                    st.session_state.current_story = state_tracker["final_story"]
                        
            except Exception as e:
                st.error(f"An error occurred: {e}")
                status_placeholder.update(label="Error", state="error")
