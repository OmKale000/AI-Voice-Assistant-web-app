import os
import json
import uuid
import time
import streamlit as st
import httpx
import urllib.parse
from dotenv import load_dotenv

# Load env variables
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "https://ai-voice-assistant-web-app-1.onrender.com")

st.set_page_config(
    page_title="AI Voice Assistant",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Premium Global CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;800&family=JetBrains+Mono&display=swap');
    
    /* Base styling & Dynamic Glass Background */
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b 0%, #020617 100%) !important;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { 
        background: rgba(255,255,255,0.15); 
        border-radius: 10px; 
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.25); }

    /* Animated Title */
    .hero-title {
        background: linear-gradient(135deg, #60a5fa 0%, #c084fc 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.8rem !important;
        font-weight: 800 !important;
        text-align: center;
        margin-top: 1rem !important;
        margin-bottom: 0.2rem !important;
        letter-spacing: -1.5px;
        text-shadow: 0 10px 30px rgba(96, 165, 250, 0.2);
    }
    
    .hero-subtitle {
        text-align: center;
        color: #94a3b8;
        font-weight: 400;
        letter-spacing: 2px;
        font-size: 0.9rem;
        margin-bottom: 3rem;
        text-transform: uppercase;
    }

    /* Message Bubbles */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        margin: 1rem 0 3rem 0;
        max-width: 850px;
        margin-left: auto;
        margin-right: auto;
        padding-bottom: 2rem;
    }

    .msg {
        padding: 1.25rem 1.75rem;
        border-radius: 1.25rem;
        line-height: 1.6;
        font-size: 1.05rem;
        animation: slide-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        position: relative;
        backdrop-filter: blur(12px);
        max-width: 85%;
        word-wrap: break-word;
    }

    @keyframes slide-up {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .user-msg {
        align-self: flex-end;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.85), rgba(29, 78, 216, 0.95));
        color: #ffffff;
        border-bottom-right-radius: 4px;
        box-shadow: 0 12px 24px -8px rgba(37, 99, 235, 0.5);
        border: 1px solid rgba(255,255,255,0.15);
    }

    .ai-msg {
        align-self: flex-start;
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-bottom-left-radius: 4px;
        color: #e2e8f0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    /* Animated Orb & Waveform Processing */
    .processing-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 2rem 0;
        gap: 1.5rem;
    }
    
    .orb-container {
        position: relative;
        width: 80px;
        height: 80px;
    }
    .orb {
        position: absolute;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle, #3b82f6 0%, transparent 70%);
        border-radius: 50%;
        filter: blur(12px);
        animation: pulse 2.5s infinite ease-in-out;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(0.9); opacity: 0.4; }
        50% { transform: scale(1.4); opacity: 0.9; }
    }

    .waveform {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        height: 40px;
    }
    .bar {
        width: 4px;
        background: #60a5fa;
        border-radius: 2px;
        animation: wave 1.2s ease-in-out infinite;
        box-shadow: 0 0 8px rgba(96, 165, 250, 0.5);
    }
    .bar:nth-child(1) { height: 12px; animation-delay: 0.0s; }
    .bar:nth-child(2) { height: 24px; animation-delay: 0.1s; }
    .bar:nth-child(3) { height: 36px; animation-delay: 0.2s; }
    .bar:nth-child(4) { height: 24px; animation-delay: 0.3s; }
    .bar:nth-child(5) { height: 12px; animation-delay: 0.4s; }
    
    @keyframes wave {
        0%, 100% { height: 10px; opacity: 0.5; }
        50% { height: 35px; opacity: 1; }
    }

    /* Audio Input Styling Adjustments */
    div[data-testid="stAudioInput"] {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 1.5rem;
        padding: 1.5rem;
        border: 1px solid rgba(255,255,255,0.05);
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
    }

    /* Floating Menu Button 
    .menu-toggle {
        position: fixed;
        top: 1.5rem;
        left: 1.5rem;
        z-index: 999999;
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        width: 2.8rem;
        height: 2.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        color: #cbd5e1;
        font-size: 1.2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .menu-toggle:hover {
        color: #ffffff;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        border-color: rgba(96, 165, 250, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    } */

    /* Sidebar Styling */
    div[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255,255,255,0.05) !important;
    }
    .sidebar-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    
    .status-panel {
        padding: 1rem;
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        font-size: 0.9rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .online { background: #10b981; box-shadow: 0 0 10px #10b981; }
    .offline { background: #ef4444; box-shadow: 0 0 10px #ef4444; }
    
    /* Buttons */
    div.stButton > button {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: #f8fafc;
        border-radius: 10px;
        transition: all 0.2s ease;
        font-weight: 500;
    }
    div.stButton > button:hover {
        background: rgba(255,255,255,0.1);
        border-color: #60a5fa;
        color: #60a5fa;
        transform: translateY(-2px);
    }
    
    /* Quick Actions */
    .quick-action-title {
        text-align: center; 
        font-size: 0.85rem; 
        color: #64748b; 
        margin-top: 3rem; 
        margin-bottom: 1rem;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "last_input_hash" not in st.session_state:
    st.session_state.last_input_hash = None
if "sidebar_state" in st.session_state:
    st.session_state.sidebar_state = "expanded"

# Custom JS for sidebar toggle
st.markdown(
    """
    <script>
    function toggleSidebar() {
        const doc = window.parent.document;
        
        // 1. If sidebar is open, find the close button inside it and click
        const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
        if (sidebar && sidebar.getAttribute('aria-expanded') === 'true') {
            const closeBtn = sidebar.querySelector('button');
            if (closeBtn) {
                closeBtn.click();
                return;
            }
        }
        
        // 2. If sidebar is closed, find the expand control and click
        const openBtn = doc.querySelector('[data-testid="collapsedControl"]');
        if (openBtn) {
            openBtn.click();
            return;
        }
        
        // Fallback: Trigger Streamlit native shortcut
        doc.dispatchEvent(new KeyboardEvent('keydown', {
            key: ']',
            keyCode: 221,
            which: 221,
            bubbles: true,
            composed: true
        }));
    }
    </script>
    <div class="menu-toggle" onclick="toggleSidebar()" title="Toggle Menu">
        
    </div>
    """,
    unsafe_allow_html=True
)

# --- Sidebar ---
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <span style="font-size: 1.8rem;">💠</span>
        <span style="font-size: 1.4rem; font-weight: 800; color: #fff; letter-spacing: 1px;">CONTROL</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ New Session", use_container_width=True, type="primary"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Advanced: Multimodal Input
    st.markdown("### 📸 Vision Input")
    uploaded_image = st.file_uploader("Upload image to analyze", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    if uploaded_image:
        st.image(uploaded_image, use_column_width=True, caption="Vision Source Active")
    
    st.markdown("---")
    
    # Provider Status
    st.markdown("### 📡 System Status")

    try:
        with httpx.Client(timeout=2.0) as client:
            status_resp = client.get(f"{BACKEND_URL}/health")
            status_data = status_resp.json()
            active_p = status_data.get("providers", {}).get("active", "Unknown")
            ver = status_data.get("version", "Unknown")
            status_class = "online"
    except:
        active_p = "Offline"
        ver = "N/A"
        status_class = "offline"
    
    st.markdown(f"""
    <div class="status-panel">
        <span style="display: flex; align-items: center;"><div class="indicator {status_class}"></div> Backend V{ver}</span>
        <span style="color: #60a5fa; font-weight: 600; font-size: 0.8rem;">{active_p.upper()}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📜 Session History")
    
    # Load history from backend
    try:
        with httpx.Client(timeout=3.0) as client:
            hist_resp = client.get(f"{BACKEND_URL}/api/history")
            if hist_resp.status_code == 200:
                sessions = hist_resp.json().get("sessions", [])
                if not sessions:
                    st.caption("No recent sessions found.")
                for s in sessions:
                    if st.button(f"Session: {s['id'][:8]}...", key=s['id'], use_container_width=True):
                        st.session_state.session_id = s['id']
                        # Load messages for this session
                        msg_resp = client.get(f"{BACKEND_URL}/api/history/{s['id']}")
                        msgs = msg_resp.json().get("messages", [])
                        st.session_state.messages = []
                        for m in msgs:
                            st.session_state.messages.append({"role": "user", "content": m["query"]})
                            st.session_state.messages.append({"role": "assistant", "content": m["response"]})
                        st.rerun()
            else:
                st.caption("History unavailable")
    except:
        st.caption("Log in or connect to backend to see history")

    st.markdown("---")
    st.markdown("### 📊 Analytics")
    try:
        with httpx.Client(timeout=3.0) as client:
            ana_resp = client.get(f"{BACKEND_URL}/api/analytics")
            if ana_resp.status_code == 200:
                ana = ana_resp.json()
                st.metric("Total Requests", ana.get("total_requests", 0))
                st.metric("Avg Latency", f"{ana.get('avg_latency_ms', 0)}ms")
                
                reqs = max(ana.get("total_requests", 1), 1) # prevent div by zero
                stability = max(0.0, min(1.0, 1.0 - (ana.get("fallbacks", 0) / reqs)))
                st.progress(stability, text=f"Stability: {active_p.upper()}")
            else:
                st.caption("Analytics unavailable")
    except:
        st.caption("Analytics offline")

# --- Main UI ---
st.markdown("<h1 class='hero-title'>AI Voice Assistant web app</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-subtitle'>Advanced Neural Interface</p>", unsafe_allow_html=True)

# Chat Display
if not st.session_state.messages and not st.session_state.is_processing:
    # Empty state placeholder
    st.markdown("""
    <div style='text-align: center; color: #475569; padding: 4rem 2rem;'>
        <div style='font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;'>🎙️</div>
        <h3>Awaiting your command</h3>
        <p>Speak to interact with Nexus, or use the quick actions below.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        cls = "user-msg" if msg["role"] == "user" else "ai-msg"
        st.markdown(f"<div class='msg {cls}'>{msg['content']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Orb / Processing State
if st.session_state.is_processing:
    st.markdown("""
        <div class="processing-container">
            <div class="orb-container">
                <div class="orb"></div>
            </div>
            <div class="waveform">
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
            </div>
            <p style='color: #94a3b8; font-size: 0.85rem; letter-spacing: 3px; text-transform: uppercase; font-weight: 600;'>AI Voice Assistant is processing...</p>
        </div>
    """, unsafe_allow_html=True)


# --- Input Area ---
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True) # Spacer
col1, col2, col3 = st.columns([1, 4, 1])

with col2:
    audio_value = st.audio_input("Speak to Nexus", disabled=st.session_state.is_processing)

# Quick Actions (Moved below input for better flow)
if not st.session_state.is_processing:
    st.markdown("<p class='quick-action-title'>QUICK EXPLORATION</p>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button("🌤️ Local Weather", use_container_width=True)
    with c2:
        st.button("📰 Latest News", use_container_width=True)
    with c3:
        st.button("🔍 Explain AI", use_container_width=True)
    with c4:
        st.button("🎨 Analyze Image", use_container_width=True)

# --- Processing Logic ---
if audio_value and not st.session_state.is_processing:
    # Debounce / Duplicate Prevention
    input_hash = hash(audio_value.read())
    audio_value.seek(0) # Reset buffer
    
    if input_hash != st.session_state.last_input_hash:
        st.session_state.is_processing = True
        st.session_state.last_input_hash = input_hash
        st.rerun() # Trigger immediate UI update to show "Processing"

# If we just triggered processing, run the backend call
if st.session_state.is_processing and audio_value:
    try:
        # Preparation
        files = {"audio": ("recording.wav", audio_value, "audio/wav")}
        if uploaded_image:
            # We need to seek(0) in case it was read for preview
            uploaded_image.seek(0)
            files["image"] = (uploaded_image.name, uploaded_image, uploaded_image.type)

        history_data = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[-10:]
            if m["role"] in ["user", "assistant"]
        ]
        
        # API Call
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{BACKEND_URL}/api/process-audio",
                files=files,
                data={
                    "chat_history": json.dumps(history_data),
                    "session_id": st.session_state.session_id
                }
            )

        if response.status_code == 200:
            q_raw = response.headers.get("X-Query-Text", "Unknown")
            r_raw = response.headers.get("X-Response-Text", "No response")
            
            q_text = urllib.parse.unquote(q_raw)
            r_text = urllib.parse.unquote(r_raw)
            is_safe = response.headers.get("X-Is-Safe", "true") == "true"
            
            # Update State
            st.session_state.messages.append({"role": "user", "content": q_text})
            st.session_state.messages.append({"role": "assistant", "content": r_text})
            
            # Play Audio
            st.audio(response.content, format="audio/mp3", autoplay=True)

        else:
            st.error(f"Error: {response.text}")
            
    except Exception as e:
        st.error(f"AI Voice Assistant Failure: {str(e)}")
    finally:
        st.session_state.is_processing = False
        st.rerun()
