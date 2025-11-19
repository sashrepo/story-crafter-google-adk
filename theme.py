
import streamlit as st
import itertools

def apply_google_kids_theme():
    st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@300;400;500;600;700&family=Quicksand:wght@300;400;500;600;700&display=swap');

        :root {
            --google-blue: #4285F4;
            --google-red: #DB4437;
            --google-yellow: #F4B400;
            --google-green: #0F9D58;
            --bg-color: #FAFAFA;
            --sidebar-bg: #FFFFFF;
            --text-color: #3C4043;
            --card-radius: 24px;
            --button-radius: 50px;
            --shadow-soft: 0 4px 20px rgba(0,0,0,0.08);
        }

        /* General App Styling */
        .stApp {
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(rgba(66, 133, 244, 0.1) 2px, transparent 2px), 
                radial-gradient(rgba(219, 68, 55, 0.1) 2px, transparent 2px);
            background-size: 40px 40px;
            background-position: 0 0, 20px 20px;
            font-family: 'Quicksand', sans-serif;
            color: var(--text-color);
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Fredoka', sans-serif !important;
            font-weight: 600 !important;
            color: var(--text-color);
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: var(--sidebar-bg);
            border-right: 2px solid #E8EAED;
            box-shadow: 4px 0 10px rgba(0,0,0,0.02);
        }
        
        section[data-testid="stSidebar"] .block-container {
            padding-top: 2rem;
        }

        /* Buttons */
        .stButton button {
            background-color: var(--google-blue) !important;
            color: white !important;
            border-radius: var(--button-radius) !important;
            border: none !important;
            font-family: 'Fredoka', sans-serif !important;
            font-weight: 500 !important;
            padding: 0.6rem 1.5rem !important;
            box-shadow: 0 4px 6px rgba(66, 133, 244, 0.2) !important;
            transition: transform 0.1s, box-shadow 0.1s !important;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(66, 133, 244, 0.3) !important;
        }
        
        .stButton button:active {
            transform: translateY(1px);
        }

        /* Inputs - Force light mode appearance even if system is dark */
        .stTextInput input, .stTextArea textarea, .stSelectbox, div[data-baseweb="select"] {
            background-color: #FFFFFF !important;
            color: #3C4043 !important;
            border-radius: var(--card-radius) !important;
            border: 2px solid #E8EAED !important;
            padding: 1rem !important;
            font-family: 'Quicksand', sans-serif !important;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: var(--google-blue) !important;
            box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2) !important;
        }
        
        /* Specific fix for label colors in sidebar which might be white on white */
        .stTextInput label, .stCheckbox label, .stSelectbox label {
            color: #3C4043 !important;
            font-family: 'Fredoka', sans-serif !important;
            font-weight: 500 !important;
        }
        
        /* Sidebar specific text overrides */
        section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
             color: #3C4043 !important;
        }

        /* Chat Messages */
        .stChatMessage {
            background-color: transparent;
            padding: 1rem;
            border-radius: var(--card-radius);
            margin-bottom: 1rem;
        }

        div[data-testid="stChatMessage"] {
            background-color: white;
            border-radius: var(--card-radius);
            box-shadow: var(--shadow-soft);
            border: 1px solid #F1F3F4;
            margin-bottom: 1.5rem;
            transition: transform 0.2s;
        }
        
        div[data-testid="stChatMessage"]:hover {
            transform: scale(1.01);
        }
        
        div[data-testid="stChatMessage"] .stMarkdown {
            font-family: 'Quicksand', sans-serif;
            font-size: 1.1rem;
        }

        /* Avatars */
        div[data-testid="stChatMessage"] .stImage {
            border-radius: 50%;
            border: 3px solid var(--google-yellow);
            background-color: white;
        }
        
        /* User Avatar specific */
        div[data-testid="stChatMessage"][class*="user"] .stImage {
             border-color: var(--google-blue);
        }

        /* Custom Header Bar */
        .google-bar {
            height: 8px;
            width: 100%;
            display: flex;
            margin-bottom: 2rem;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .google-bar div { height: 100%; flex: 1; }
        .bar-blue { background-color: var(--google-blue); }
        .bar-red { background-color: var(--google-red); }
        .bar-yellow { background-color: var(--google-yellow); }
        .bar-green { background-color: var(--google-green); }

        /* Expanders */
        .streamlit-expanderHeader {
            background-color: white !important;
            border-radius: var(--card-radius) !important;
            font-family: 'Fredoka', sans-serif !important;
            color: var(--text-color) !important;
            border: 1px solid #E8EAED !important;
        }
        
        .streamlit-expanderContent {
            background-color: white !important;
            border-radius: 0 0 var(--card-radius) var(--card-radius) !important;
            border: 1px solid #E8EAED !important;
            border-top: none !important;
        }

        /* Chat Input - Bottom Bar Styling */
        .stChatInputContainer {
            padding-bottom: 1.5rem;
            padding-top: 1rem;
            background-color: transparent !important;
        }
        
        .stChatInputContainer > div {
            background-color: transparent !important;
        }
        
        .stChatInputContainer textarea {
            background-color: white !important;
            color: #3C4043 !important;
            border-radius: 30px !important;
            border: 2px solid var(--google-blue) !important;
            box-shadow: 0 4px 12px rgba(66, 133, 244, 0.15) !important;
        }
        
        /* Placeholder text color */
        ::placeholder {
            color: #9AA0A6 !important;
            opacity: 1 !important;
        }

        /* Header adjustments */
        header {
            background-color: transparent !important;
        }
        
        /* Adjust main container to not be hidden by header */
        .block-container {
            padding-top: 3rem !important;
        }

        /* Hide the default Streamlit menu if possible to clean up, or style it */
        #MainMenu {visibility: visible;}
        footer {visibility: hidden;}

        /* Toggle Switch */
        .stToggle {
            font-family: 'Fredoka', sans-serif !important;
        }
        
        .stToggle label {
            color: #3C4043 !important;
        }
        
        div[data-testid="stToggle"] {
             background-color: white;
             padding: 10px;
             border-radius: 20px;
             border: 1px solid #E8EAED;
        }

        /* Status / Toast */
        div[data-testid="stStatusWidget"] {
            border-radius: var(--card-radius);
            border: 2px solid var(--google-green);
            background-color: #E6F4EA;
        }

        /* Custom specific for our app content */
        .google-title {
            font-family: 'Fredoka', sans-serif;
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 0px rgba(0,0,0,0.05);
        }
        
        .google-subtitle {
            font-family: 'Quicksand', sans-serif;
            color: #5F6368;
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }

        </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown("""
        <div class="google-bar">
            <div class="bar-blue"></div>
            <div class="bar-red"></div>
            <div class="bar-yellow"></div>
            <div class="bar-green"></div>
        </div>
    """, unsafe_allow_html=True)

def render_custom_title(title_text, subtitle_text=""):
    colors = ["#4285F4", "#DB4437", "#F4B400", "#0F9D58"]
    color_cycle = itertools.cycle(colors)
    
    colored_html = ""
    for char in title_text:
        if char.strip():
            color = next(color_cycle)
            colored_html += f"<span style='color:{color}'>{char}</span>"
        else:
            colored_html += " "
            
    st.markdown(f"""
        <div class='google-title'>{colored_html}</div>
        <div class='google-subtitle'>{subtitle_text}</div>
    """, unsafe_allow_html=True)
