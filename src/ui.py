import streamlit as st
import dotenv
import time
from datetime import datetime

# Load env
dotenv.load_dotenv()

# -------------------------------------------------
# IMPORTS (EXISTING LOGIC)
# -------------------------------------------------
from nlu.slot_filler import SlotFiller
from nlu.llm_client import LLMClient
from planner.agent_planner import plan_and_retrieve
from utils.schema import find_missing_mandatory

from advisor.advisor_reasoner import (
    generate_advisor_output,
    generate_comparison_output,
    generate_competitor_analysis_output,
    generate_sector_screener_output,
    generate_sector_trend_output,
    generate_stock_news_output,
    generate_commodity_news_output,
    generate_commodity_trend_output,
    generate_info_general_output

)

from risk.risk_engine import compute_risk_score
from risk.explainer import explain_result

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Stock Risk Advisor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------
# ADVANCED TELEGRAM-STYLE CSS
# -------------------------------------------------
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Remove default Streamlit padding */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container with gradient background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Chat container wrapper */
    .chat-wrapper {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        margin: 20px auto;
        max-width: 1200px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        overflow: hidden;
        animation: slideUp 0.5s ease-out;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Header */
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px 30px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .header-title {
        font-size: 24px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .status-indicator {
        width: 10px;
        height: 10px;
        background: #4ade80;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Chat messages area */
    .chat-messages {
        padding: 30px;
        min-height: 500px;
        max-height: 600px;
        overflow-y: auto;
        background: #f8f9fa;
    }
    
    /* Custom scrollbar */
    .chat-messages::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-messages::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .chat-messages::-webkit-scrollbar-thumb {
        background: #cbd5e0;
        border-radius: 10px;
    }
    
    .chat-messages::-webkit-scrollbar-thumb:hover {
        background: #a0aec0;
    }
    
    /* Message bubbles */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 8px 0 !important;
    }
    
    [data-testid="stChatMessageContent"] {
        background: white !important;
        border-radius: 18px !important;
        padding: 12px 18px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
        max-width: 75% !important;
        animation: messageSlide 0.3s ease-out;
    }
    
    @keyframes messageSlide {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* User messages (right aligned) */
    [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        margin-left: auto !important;
        border-bottom-right-radius: 4px !important;
    }
    
    /* Assistant messages (left aligned) */
    [data-testid="stChatMessage"]:not([data-testid*="user"]) [data-testid="stChatMessageContent"] {
        background: white !important;
        color: #1a202c !important;
        border-bottom-left-radius: 4px !important;
        border: 1px solid #e2e8f0;
    }
    
    /* Avatar styling */
    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"] {
        width: 40px !important;
        height: 40px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 20px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Adjust message container to bring avatars much closer */
    [data-testid="stChatMessage"] {
        padding: 8px 0 !important;
        max-width: 95% !important;
        margin: 0 auto !important;
    }
    
    [data-testid="stChatMessage"] > div {
        display: flex !important;
        align-items: flex-start !important;
        gap: 12px !important;
        max-width: 100% !important;
    }
    
    /* User messages - align right */
    [data-testid="stChatMessage"]:has([data-testid*="user"]) {
        display: flex !important;
        justify-content: flex-end !important;
    }
    
    /* Assistant messages - align left */
    [data-testid="stChatMessage"]:not(:has([data-testid*="user"])) {
        display: flex !important;
        justify-content: flex-start !important;
    }
    
    /* Chat input */
    .stChatInputContainer {
        background: white;
        padding: 20px 30px;
        border-top: 1px solid #e2e8f0;
    }
    
    [data-testid="stChatInput"] {
        border-radius: 25px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 12px 20px !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stChatInput"]:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
        padding-top: 20px;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    [data-testid="stSidebar"] .stButton button {
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    /* Info boxes in sidebar */
    .stAlert {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        color: white !important;
        backdrop-filter: blur(10px);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Error messages */
    .stAlert[data-baseweb="notification"] {
        background: #fee2e2 !important;
        border-left: 4px solid #ef4444 !important;
        border-radius: 8px !important;
        color: #991b1b !important;
    }
    
    /* Markdown in messages */
    [data-testid="stChatMessageContent"] h1,
    [data-testid="stChatMessageContent"] h2,
    [data-testid="stChatMessageContent"] h3 {
        margin-top: 0;
        color: inherit;
    }
    
    [data-testid="stChatMessageContent"] strong {
        font-weight: 600;
    }
    
    [data-testid="stChatMessageContent"] code {
        background: rgba(0, 0, 0, 0.05);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.9em;
    }
    .stAlert {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        color: white !important;
        backdrop-filter: blur(10px);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Error messages */
    .stAlert[data-baseweb="notification"] {
        background: #fee2e2 !important;
        border-left: 4px solid #ef4444 !important;
        border-radius: 8px !important;
        color: #991b1b !important;
    }
    
    /* Markdown in messages */
    [data-testid="stChatMessageContent"] h1,
    [data-testid="stChatMessageContent"] h2,
    [data-testid="stChatMessageContent"] h3 {
        margin-top: 0;
        color: inherit;
    }
    
    [data-testid="stChatMessageContent"] strong {
        font-weight: 600;
    }
    
    [data-testid="stChatMessageContent"] code {
        background: rgba(0, 0, 0, 0.05);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.9em;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 12px;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        background: #94a3b8;
        border-radius: 50%;
        animation: typing 1.4s infinite;
    }
    
    .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.7;
        }
        30% {
            transform: translateY(-10px);
            opacity: 1;
        }
    }
    
    /* Welcome message */
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px;
        border-radius: 16px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .welcome-card h2 {
        margin: 0 0 10px 0;
        font-size: 28px;
        font-weight: 600;
    }
    
    .welcome-card p {
        margin: 0;
        opacity: 0.9;
        font-size: 16px;
    }
    
    /* Time stamp */
    .message-time {
        font-size: 11px;
        opacity: 0.6;
        margin-top: 4px;
    }
    
    /* Custom input styling for login */
    .stTextInput input {
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Login button */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Override for sidebar buttons */
    [data-testid="stSidebar"] .stButton button {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255, 255, 255, 0.3) !important;
    }


</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# INIT PIPELINE OBJECTS (ONCE PER SESSION)
# -------------------------------------------------
if "client" not in st.session_state:
    st.session_state.client = LLMClient()
    st.session_state.sf = SlotFiller(llm_client=st.session_state.client)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

if "pending_followup" not in st.session_state:
    st.session_state.pending_followup = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# Dummy credentials
DEMO_EMAIL = "demo@gmail.com"
DEMO_PASSWORD = "demo123"

# -------------------------------------------------
# LOGIN CHECK - Show login screen if not logged in
# -------------------------------------------------
if not st.session_state.logged_in:
    # Create centered login form
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);'>
            <div style='text-align: center; margin-bottom: 30px;'>
                <h1 style='font-size: 48px; margin: 0;'>📈</h1>
                <h2 style='color: #667eea; margin: 10px 0; font-size: 28px;'>Stock Risk Advisor</h2>
                <p style='color: #64748b; margin: 0;'>Sign in to access your AI market analysis</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("### 🔐 Welcome Back")
            st.markdown("Please sign in to continue")
            
            email = st.text_input("📧 Email", placeholder="demo@gmail.com", key="login_email")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter password", key="login_password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_a, col_b = st.columns([1, 1])
            
            with col_a:
                if st.button("🚀 Sign In", use_container_width=True, key="signin_btn"):
                    if email == DEMO_EMAIL and password == DEMO_PASSWORD:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials. Try demo@gmail.com / demo123")
            
            with col_b:
                if st.button("⚡ Demo Login", use_container_width=True, key="demo_btn"):
                    st.session_state.logged_in = True
                    st.session_state.user_email = DEMO_EMAIL
                    st.rerun()
            
            st.markdown("---")
            st.info("💡 **Demo Credentials**\n\n**Email:** demo@gmail.com\n\n**Password:** demo123")
    
    st.stop()

# -------------------------------------------------
# SIDEBAR UI
# -------------------------------------------------
with st.sidebar:
    # Profile Section
    st.markdown(f"""
    <div style='background: rgba(255,255,255,0.15); padding: 20px; border-radius: 15px; margin-bottom: 20px; backdrop-filter: blur(10px);'>
        <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 15px;'>
            <div style='width: 50px; height: 50px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px;'>
                👤
            </div>
            <div>
                <div style='font-weight: 600; font-size: 16px;'>Welcome!</div>
                <div style='font-size: 13px; opacity: 0.9;'>{st.session_state.user_email}</div>
            </div>
        </div>
        <div style='display: flex; gap: 8px;'>
            <div style='flex: 1; background: rgba(255,255,255,0.1); padding: 8px; border-radius: 8px; text-align: center;'>
                <div style='font-size: 11px; opacity: 0.8;'>Status</div>
                <div style='font-size: 13px; font-weight: 600;'>🟢 Active</div>
            </div>
            <div style='flex: 1; background: rgba(255,255,255,0.1); padding: 8px; border-radius: 8px; text-align: center;'>
                <div style='font-size: 11px; opacity: 0.8;'>Queries</div>
                <div style='font-size: 13px; font-weight: 600;'>{len([m for m in st.session_state.messages if m['role'] == 'user'])}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; padding: 10px 0;'>
        <h2 style='font-size: 20px; margin: 10px 0; font-weight: 600;'>📊 Control Panel</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.session_state.pending_followup = None
        st.rerun()
    
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.session_state.pending_followup = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Example Queries")
    
    example_prompts = [
        "What is the risk for Tata Motors?",
        "Compare TCS and Infosys",
        "Energy sector trends",
        "I have 5 lakh to invest for 3 years",
        "Latest news on Reliance",
        "Gold price trends"
    ]
    
    for prompt in example_prompts:
        st.info(f"💬 {prompt}")
    
    st.markdown("---")
    st.markdown("""
    <div style='background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 20px;'>
        <p style='margin: 0; font-size: 12px; opacity: 0.9;'>
            ⚠️ <strong>Disclaimer</strong><br>
            AI-generated analysis for informational purposes only. 
            Not financial advice. Please consult a professional advisor.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; opacity: 0.7; font-size: 12px;'>
        <p>Stock Risk Advisor v2.0</p>
        <p>Powered by AI • {datetime.now().strftime('%Y')}</p>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# MAIN CHAT UI - TELEGRAM STYLE HEADER
# -------------------------------------------------
st.markdown(f"""
<div class='chat-wrapper'>
    <div class='chat-header'>
        <div class='header-title'>
            <span>📈</span>
            <div>
                <div>Stock Risk Advisor</div>
                <div style='font-size: 13px; opacity: 0.9; font-weight: 400;'>
                    <span class='status-indicator'></span>
                    <span style='margin-left: 8px;'>AI Agent • Online</span>
                </div>
            </div>
        </div>
        <div style='display: flex; align-items: center; gap: 15px;'>
            <div style='font-size: 13px; opacity: 0.8;'>🔒 Secure Analysis</div>
            <div style='background: rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 15px; font-size: 13px; display: flex; align-items: center; gap: 6px;'>
                <span>👤</span>
                <span>{st.session_state.user_email.split('@')[0]}</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------
# WELCOME MESSAGE (ONLY IF NO MESSAGES)
# -------------------------------------------------
if not st.session_state.messages:
    st.markdown("""
    <div style='max-width: 1200px; margin: 0 auto; padding: 0 20px;'>
        <div class='welcome-card'>
            <h2>👋 Welcome to Stock Risk Advisor</h2>
            <p>Your intelligent AI partner for market analysis, risk assessment, and investment insights</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick action cards using columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style='background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: left; transition: all 0.3s ease; cursor: pointer;'>
            <div style='font-size: 32px; margin-bottom: 12px;'>📊</div>
            <div style='font-weight: 600; margin-bottom: 6px; font-size: 16px; color: #1a202c;'>Risk Analysis</div>
            <div style='font-size: 13px; color: #64748b;'>Evaluate individual stocks</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: left; transition: all 0.3s ease; cursor: pointer;'>
            <div style='font-size: 32px; margin-bottom: 12px;'>⚖️</div>
            <div style='font-weight: 600; margin-bottom: 6px; font-size: 16px; color: #1a202c;'>Compare Stocks</div>
            <div style='font-size: 13px; color: #64748b;'>Side-by-side comparison</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: left; transition: all 0.3s ease; cursor: pointer;'>
            <div style='font-size: 32px; margin-bottom: 12px;'>📈</div>
            <div style='font-weight: 600; margin-bottom: 6px; font-size: 16px; color: #1a202c;'>Sector Trends</div>
            <div style='font-size: 13px; color: #64748b;'>Industry insights</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style='background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: left; transition: all 0.3s ease; cursor: pointer;'>
            <div style='font-size: 32px; margin-bottom: 12px;'>📰</div>
            <div style='font-weight: 600; margin-bottom: 6px; font-size: 16px; color: #1a202c;'>Latest News</div>
            <div style='font-size: 13px; color: #64748b;'>Market updates</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------
# RENDER CHAT HISTORY
# -------------------------------------------------
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# -------------------------------------------------
# LOGIC HANDLER
# -------------------------------------------------
user_input = st.chat_input("💬 Type your message here...")

if user_input:
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # 2. Handle Exit Commands
    if user_input.lower() in ("exit", "quit", "reset"):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.session_state.pending_followup = None
        st.rerun()

    # 3. Process with AI (Wrapped in Spinner for UI feedback)
    sf = st.session_state.sf

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🔍 Analyzing market data..."):
            try:
                # -------------------------------------------------
                # LOGIC: HANDLE FOLLOW-UP
                # -------------------------------------------------
                if st.session_state.pending_followup:
                    combined_query = (
                        st.session_state.pending_query + " " + user_input
                    )
                    st.session_state.pending_followup = None
                    st.session_state.pending_query = None
                else:
                    combined_query = user_input

                # -------------------------------------------------
                # LOGIC: SLOT EXTRACTION
                # -------------------------------------------------
                slots = sf.extract_slots(combined_query)
                missing = find_missing_mandatory(slots)

                if missing:
                    followup = sf.generate_followup(slots)
                    st.markdown(followup)

                    st.session_state.pending_query = combined_query
                    st.session_state.pending_followup = followup

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": followup
                    })
                    st.stop()

                # -------------------------------------------------
                # LOGIC: PLANNER
                # -------------------------------------------------
                context = plan_and_retrieve(slots)
                print("context:", context)

                if "error" in context:
                    st.error(f"⚠️ Data retrieval error: {context['error']}")
                    st.stop()

                mode = context.get("mode")
                response_text = ""

                # -------------------------------------------------
                # LOGIC: MODE HANDLERS
                # -------------------------------------------------
                if mode == "portfolio_guidance":                    
                    # response_text = (
                    #     f"### 💰 Portfolio Insight\n\n"
                    #     f"With **₹{context['capital']:,}**, it's important to think about your investment horizon and risk comfort.\n\n"
                    #     "You may explore:\n"
                    #     "- 🎯 Diversified large-cap stocks\n"
                    #     "- 📊 Sector-based exposure\n"
                    #     "- 💎 Index funds for stability\n\n"
                    #     "*Would you like short-term, medium-term, or long-term guidance?*\n\n"
                    #     "> ⚠️ This is a data-based analytical insight, not financial advice."
                    # )
                    from advisor.advisor_reasoner import generate_portfolio_guidance_output
                    response_text = generate_portfolio_guidance_output(context, context["language"])
                
                elif mode == "stock_comparison":
                    response_text = generate_comparison_output(context, context["language"])

                elif mode == "competitor_analysis":
                    response_text = generate_competitor_analysis_output(context, context["language"])

                elif mode == "sector_screener":
                    response_text = generate_sector_screener_output(context, context["language"])

                elif mode == "sector_trend":
                    response_text = generate_sector_trend_output(context, context["language"])

                elif mode == "stock_news":
                    response_text = generate_stock_news_output(context, context["language"])
                
                elif context.get("mode") == "info_general":
                    response_text = generate_info_general_output(context, context["language"])

                elif context.get("mode") == "commodity_trend":
                    response_text = "### 🪙 Commodity Trend\n\n" + generate_commodity_trend_output(context, context["language"])

                elif context.get("mode") == "commodity_news":
                    response_text = "### 📰 Commodity News\n\n" + generate_commodity_news_output(context, context["language"])

                else:
                    # -------------------------------------------------
                    # LOGIC: SINGLE-STOCK MODES (Risk/Buy/Trend)
                    # -------------------------------------------------
                    analysis = compute_risk_score(context)

                    explanation = explain_result(
                        slots["stock_name"],
                        analysis,
                        context,
                        slots.get("language", "en"),
                    )

                    advisor = generate_advisor_output(
                        slots,
                        context,
                        analysis,
                        explanation
                    )
                    response_text = advisor["advisor_text"]

                # -------------------------------------------------
                # RENDER & SAVE RESPONSE
                # -------------------------------------------------
                st.markdown(response_text)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text
                })

            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {e}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ An unexpected error occurred: {e}"
                })