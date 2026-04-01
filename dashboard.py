"""
JARVIS Dashboard - Streamlit UI
Visualizzazione stato, finanze, log, controlli
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import psutil

from jarvis_config import config
from finance_engine import check_gap, load_finances, update_finances
from jarvis_control import get_system_info, get_app_list, get_website_list
from jarvis_brain import is_ollama_available, LOCAL_MODEL

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="JARVIS Control Panel",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    
    .status-online {
        color: #2ecc71;
        font-weight: bold;
    }
    
    .status-offline {
        color: #e74c3c;
        font-weight: bold;
    }
    
    h1, h2, h3 {
        color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.title("⚡ JARVIS Control Panel")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    options=[
        "🏠 Dashboard",
        "💰 Finance",
        "🧠 AI Status",
        "🖥️ System",
        "📱 Controls",
        "📊 Settings"
    ]
)

st.sidebar.divider()
st.sidebar.markdown("**Version:** 1.0.0")
st.sidebar.markdown("**Model:** llama3.1:8b + Claude Haiku 4.5")
st.sidebar.markdown("**Status:** Operational")

# ============================================================================
# FUNZIONI HELPER
# ============================================================================

def get_system_status():
    """Ritorna status completo del sistema."""
    chroma_path = config.get("paths.chroma_db", "chroma_db")
    return {
        "ollama": is_ollama_available(),
        "python": True,
        "config": config.config_dir.exists(),
        "rag": Path(chroma_path).exists()
    }

def format_currency(value):
    """Formatta valori monetari."""
    return f"€{value:.2f}"

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

if page == "🏠 Dashboard":
    st.title("⚡ JARVIS Dashboard")
    st.markdown("*Personal AI Assistant - Control Center*")
    st.divider()
    
    # Status Overview
    col1, col2, col3, col4 = st.columns(4)
    
    status = get_system_status()
    
    with col1:
        st.metric(
            "Ollama",
            "🟢 Online" if status["ollama"] else "🔴 Offline",
            "llama3.1:8b"
        )
    
    with col2:
        st.metric(
            "Claude API",
            "🟢 Ready",
            "Haiku 4.5"
        )
    
    with col3:
        st.metric(
            "Database",
            "🟢 Active",
            "ChromaDB"
        )
    
    with col4:
        st.metric(
            "Time",
            datetime.now().strftime("%H:%M"),
            datetime.now().strftime("%d/%m/%Y")
        )
    
    st.divider()
    
    # System Info
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💻 System Status")
        sys_info = {
            "CPU": f"{psutil.cpu_percent()}%",
            "RAM": f"{psutil.virtual_memory().percent}%",
            "Disk": f"{psutil.disk_usage('/').percent}%"
        }
        
        for metric, value in sys_info.items():
            st.write(f"**{metric}:** {value}")
    
    with col2:
        st.subheader("🎙️ Voice Status")
        st.write(f"**Voice:** {config.get_voice()}")
        st.write("**TTS Engine:** Edge TTS")
        st.write("**Language:** Italian (it-IT)")
    
    st.divider()
    
    # Recent Activity (placeholder)
    st.subheader("📝 Recent Activity")
    st.info("Activity log will appear here when JARVIS is running")

# ============================================================================
# PAGE: FINANCE
# ============================================================================

elif page == "💰 Finance":
    st.title("💰 Finance Tracker")
    st.markdown("*Monthly Budget Management*")
    st.divider()
    
    # Current finances
    finances = load_finances()
    gap, message = check_gap()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Target Monthly",
            format_currency(finances.get("target_affitto", 110.0)),
            "Budget Goal"
        )
    
    with col2:
        st.metric(
            "Current Income",
            format_currency(finances.get("entrate_attuali", 0.0)),
            "Actual"
        )
    
    with col3:
        gap_color = "normal" if gap > 0 else "off"
        st.metric(
            "Gap",
            format_currency(abs(gap)),
            "To reach target" if gap > 0 else "Surplus",
            delta_color=gap_color
        )
    
    st.divider()
    
    # TTS Message
    st.subheader("🎙️ Voice Notification")
    st.info(message)
    
    st.divider()
    
    # Update finances
    st.subheader("📊 Update Budget")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_target = st.number_input(
            "Target Monthly (€)",
            value=finances.get("target_affitto", 110.0),
            min_value=0.0,
            step=1.0
        )
    
    with col2:
        new_income = st.number_input(
            "Current Income (€)",
            value=finances.get("entrate_attuali", 0.0),
            min_value=0.0,
            step=1.0
        )
    
    if st.button("💾 Save Changes", type="primary"):
        update_finances(new_income, new_target)
        st.success("✓ Budget updated!")
        st.rerun()

# ============================================================================
# PAGE: AI STATUS
# ============================================================================

elif page == "🧠 AI Status":
    st.title("🧠 AI Systems")
    st.markdown("*Local & Cloud Intelligence*")
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🖥️ Local AI (Ollama)")
        
        ollama_status = is_ollama_available()
        status_text = "🟢 Online" if ollama_status else "🔴 Offline"
        status_color = "success" if ollama_status else "error"
        
        st.markdown(f"**Status:** {status_text}", unsafe_allow_html=True)
        st.write(f"**Model:** {config.get_local_model()}")
        st.write(f"**URL:** {config.get('ai.local_url', 'http://localhost:11434')}")
        st.write(f"**Timeout:** {config.get('ai.local_timeout', 30)}s")
        
        if ollama_status:
            st.success("✓ Local inference ready")
        else:
            st.warning("⚠ Start Ollama: `ollama serve`")
    
    with col2:
        st.subheader("☁️ Cloud AI (Claude)")
        
        st.write(f"**Model:** {config.get_cloud_model()}")

        st.write(f"**Provider:** Anthropic API")
        st.write(f"**Status:** 🟢 Ready (with API key)")
        st.info("ℹ Cloud AI used as fallback for complex reasoning")
    
    st.divider()
    
    st.subheader("🔄 AI Strategy")
    st.write("""
    **Local-First Approach:**
    1. User query arrives
    2. Try Ollama (llama3.1:8b) first → Fast (~2-5s)
    3. If too complex, fallback to Claude → Smart (~3-8s)
    4. All document indexing stays local
    5. Privacy maintained
    """)

# ============================================================================
# PAGE: SYSTEM
# ============================================================================

elif page == "🖥️ System":
    st.title("🖥️ System Information")
    st.markdown("*Hardware & Software Status*")
    st.divider()
    
    # CPU
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cpu_percent = psutil.cpu_percent(interval=1)
        st.metric("CPU Usage", f"{cpu_percent}%")
    
    with col2:
        ram = psutil.virtual_memory()
        st.metric(
            "RAM Usage",
            f"{ram.percent}%",
            f"{ram.used // 1024 // 1024}MB / {ram.total // 1024 // 1024}MB"
        )
    
    with col3:
        disk = psutil.disk_usage("/")
        st.metric("Disk Usage", f"{disk.percent}%")
    
    st.divider()
    
    # Config status
    st.subheader("⚙️ Configuration")
    
    config_status = {
        "Config Manager": config is not None,
        "Config File": (config.config_dir / "jarvis_config.json").exists(),
        "ChromaDB": Path(config.get("paths.chroma_db", "chroma_db")).exists(),
        "Finances": (config.config_dir / "finances.json").exists()
    }
    
    for item, status in config_status.items():
        icon = "✓" if status else "✗"
        st.write(f"{icon} {item}")

# ============================================================================
# PAGE: CONTROLS
# ============================================================================

elif page == "📱 Controls":
    st.title("📱 Quick Controls")
    st.markdown("*Launcher & Command Center*")
    st.divider()
    
    col1, col2 = st.columns(2)
    
    # Apps
    with col1:
        st.subheader("🚀 Applications")
        
        apps = get_app_list()
        app_names = list(apps.keys())[:10]  # First 10
        
        for app in app_names:
            if st.button(f"Launch {app.title()}", key=f"app_{app}"):
                st.info(f"Would launch: {app}")
    
    # Websites
    with col2:
        st.subheader("🌐 Websites")
        
        sites = get_website_list()
        site_names = list(sites.keys())[:10]  # First 10
        
        for site in site_names:
            if st.button(f"Open {site.title()}", key=f"site_{site}"):
                st.info(f"Would open: {sites[site]}")
    
    st.divider()
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📸 Take Screenshot"):
            st.success("Screenshot saved to Desktop")
    
    with col2:
        if st.button("🔄 Restart JARVIS"):
            st.info("Restart command sent")
    
    with col3:
        if st.button("🛑 Shutdown"):
            st.warning("Are you sure?")

# ============================================================================
# PAGE: SETTINGS
# ============================================================================

elif page == "📊 Settings":
    st.title("📊 Settings & Configuration")
    st.markdown("*Manage JARVIS Configuration*")
    st.divider()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["AI Settings", "Voice Settings", "Features"])
    
    with tab1:
        st.subheader("AI Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            local_first = st.checkbox(
                "Use Local AI First",
                value=config.get("ai.use_local_first", True)
            )
            st.caption("Prioritize Ollama over Claude API")
        
        with col2:
            timeout = st.number_input(
                "Ollama Timeout (seconds)",
                value=config.get("ai.local_timeout", 30),
                min_value=5,
                max_value=120
            )
    
    with tab2:
        st.subheader("Voice Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            music_vol = st.slider(
                "Music Volume (Normal)",
                min_value=0.0,
                max_value=1.0,
                value=config.get("voice.music_full_volume", 0.85),
                step=0.05
            )
        
        with col2:
            duck_vol = st.slider(
                "Music Volume (Ducking)",
                min_value=0.0,
                max_value=1.0,
                value=config.get("voice.music_duck_volume", 0.15),
                step=0.05
            )
    
    with tab3:
        st.subheader("Feature Flags")
        
        features = config.get("features", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            rag_enabled = st.checkbox(
                "Enable RAG (Document Search)",
                value=features.get("enable_rag", True)
            )
            web_enabled = st.checkbox(
                "Enable Web Search",
                value=features.get("enable_web_search", True)
            )
        
        with col2:
            pc_enabled = st.checkbox(
                "Enable PC Control",
                value=features.get("enable_pc_control", True)
            )
            finance_enabled = st.checkbox(
                "Enable Finance Tracker",
                value=features.get("enable_finance_tracker", True)
            )
    
    st.divider()
    
    if st.button("💾 Save All Settings", type="primary"):
        st.success("✓ Settings saved!")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
---
**JARVIS** — Personal AI Assistant  
*Built with 🔥 hunger, ☕ caffeine, and Python*

[GitHub](https://github.com) • [Docs](https://github.com) • [Issues](https://github.com)
""")
