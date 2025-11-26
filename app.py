"""
Story Crafter ADK - Streamlit Frontend

A collaborative AI-powered story creation application using Google's
Agent Development Kit (ADK) with Vertex AI Memory Bank integration.
"""

import asyncio
import streamlit as st
import os
import uuid
from pathlib import Path
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Load environment variables
load_dotenv()

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import backend services
try:
    from services.story_engine import StoryEngine
    from services.memory import get_session_service, get_memory_service
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.info("Make sure you have installed the package dependencies.")
    st.stop()

# Initialize Services (cached to persist across Streamlit reruns)
session_service = get_session_service()
memory_service = get_memory_service()


@st.cache_resource
def get_story_engine(_session_service, _memory_service):
    """Create and cache the story engine."""
    agent_engine_id = os.getenv("AGENT_ENGINE_ID") or os.getenv("MEMORY_BANK_ID")
    return StoryEngine(
        session_service=_session_service, 
        memory_service=_memory_service,
        agent_engine_id=agent_engine_id
    )


story_engine = get_story_engine(session_service, memory_service)

# Page config
st.set_page_config(
    page_title="Story Crafter ADK",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme
from ui import theme
theme.apply_google_kids_theme()


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
    
    # User Config
    st.subheader("👤 Identity")
    new_user_id = st.text_input("User ID", value=st.session_state.user_id)
    if new_user_id != st.session_state.user_id:
        st.session_state.user_id = new_user_id

    if st.button("🔄 New Conversation", type="primary"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    # Memory Bank
    st.subheader("🧠 Memory Bank")
    if st.button("🔍 Check Memories"):
        with st.spinner("Searching memories..."):
            try:
                agent_engine_id = os.getenv("AGENT_ENGINE_ID") or os.getenv("MEMORY_BANK_ID")
                
                async def fetch_memories():
                    return await memory_service.search_memory(
                        query="*",
                        app_name=agent_engine_id or "agents",
                        user_id=st.session_state.user_id
                    )
                
                response = asyncio.run(fetch_memories())
                
                if hasattr(response, 'memories') and response.memories:
                    st.success(f"Found {len(response.memories)} memories:")
                    for m in response.memories:
                        st.info(m)
                else:
                    st.warning("No memories found yet. (They may take 5-10 mins to appear)")
                    
            except Exception as e:
                st.error(f"Failed to fetch memories: {e}")

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
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Run Agent Process
    if not os.environ.get("GOOGLE_API_KEY"):
        st.error("Please set your Google API Key in the environment or sidebar.")
    else:
        with st.chat_message("assistant", avatar="🤖"):
            status_placeholder = st.status("✨ Magic in progress... ✨", expanded=True)
            state_tracker = {"final_story": "", "iteration_count": 0}
            
            def show_expander_message(avatar: str, title: str, content: str, is_final: bool = False):
                """Display an expander message and save to session state."""
                with st.chat_message("assistant", avatar=avatar):
                    with st.expander(title, expanded=False):
                        st.markdown(content)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": content,
                    "title": title,
                    "is_expander": True,
                    "avatar": avatar
                })
                if is_final:
                    state_tracker["final_story"] = content

            async def run_chat_turn():
                user_id = st.session_state.user_id
                session_id = st.session_state.session_id
                
                async for event in story_engine.process_story_request(
                    prompt=prompt,
                    user_id=user_id,
                    session_id=session_id,
                    current_story=st.session_state.current_story,
                    enable_refinement=enable_refinement
                ):
                    if event.event_type == "status":
                        status_placeholder.write(event.content)
                        
                    elif event.event_type == "critique":
                        state_tracker["iteration_count"] = event.metadata.get("iteration", 0)
                        status_placeholder.write(f"Quality Check #{state_tracker['iteration_count']}: {event.content[:50]}...")
                        show_expander_message("🧐", f"🔍 Critique #{state_tracker['iteration_count']}", event.content)
                        if event.metadata.get("approved"):
                            status_placeholder.update(label="Story Approved!", state="complete")
                            
                    elif event.event_type == "refined_story":
                        status_placeholder.write(f"Refining Story (Iteration {state_tracker['iteration_count']})...")
                        show_expander_message("✍️", f"📝 Refined Draft (Iter {state_tracker['iteration_count']})", event.content, is_final=True)
                        
                    elif event.event_type == "draft_story":
                        status_placeholder.write("Drafting initial story...")
                        show_expander_message("✍️", "📝 Initial Draft", event.content, is_final=True)
                        
                    elif event.event_type == "edited_story":
                        status_placeholder.write("Editing story...")
                        show_expander_message("✍️", "📝 Edited Story", event.content, is_final=True)
                        
                    elif event.event_type == "guide_answer":
                        status_placeholder.write("Consulting Story Guide...")
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
                        show_expander_message("🤖", f"Output: {event.agent_name}", event.content)
                        
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
                        return
                        
                    elif event.event_type == "complete":
                        status_placeholder.update(label="Generation Complete", state="complete", expanded=False)

            # Run the async loop
            try:
                asyncio.run(run_chat_turn())
                
                if state_tracker["final_story"]:
                    st.markdown("### ✨ Final Story")
                    st.markdown(state_tracker["final_story"])
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": state_tracker["final_story"],
                        "avatar": "📖"
                    })
                    
                    st.session_state.current_story = state_tracker["final_story"]
                        
            except Exception as e:
                st.error(f"An error occurred: {e}")
                status_placeholder.update(label="Error", state="error")
