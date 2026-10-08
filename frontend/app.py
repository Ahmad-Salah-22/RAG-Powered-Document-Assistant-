import os
import sys
import json
import time

# Ensure frontend directory is in sys.path
_frontend_dir = os.path.dirname(os.path.abspath(__file__))
if _frontend_dir not in sys.path:
    sys.path.insert(0, _frontend_dir)

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from api_client import RAGApiClient

# ---------------------------------------------------------
# Page Configuration & Metadata
# ---------------------------------------------------------
st.set_page_config(
    page_title="RAG Document Assistant Studio",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Comprehensive Modern CSS (Cyber-Glassmorphism Design System)
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --bg-main: #090d16;
        --bg-card: rgba(22, 30, 49, 0.72);
        --bg-card-hover: rgba(30, 41, 67, 0.85);
        --border-glass: rgba(255, 255, 255, 0.08);
        --border-accent: rgba(99, 102, 241, 0.4);
        --accent-indigo: #6366f1;
        --accent-violet: #8b5cf6;
        --accent-cyan: #06b6d4;
        --accent-emerald: #10b981;
        --accent-amber: #f59e0b;
        --accent-rose: #f43f5e;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    .stApp {
        background: radial-gradient(ellipse at 15% 10%, #111a33 0%, #090d16 60%, #060910 100%);
        color: var(--text-primary);
    }

    /* Custom Modern Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.6);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(99, 102, 241, 0.4);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(99, 102, 241, 0.7);
    }

    /* Top Hero Studio Header Card */
    .hero-container {
        position: relative;
        background: linear-gradient(135deg, rgba(30, 41, 67, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 28px 36px;
        margin-bottom: 24px;
        box-shadow: 0 20px 50px -15px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        overflow: hidden;
    }

    .hero-glow-orb {
        position: absolute;
        top: -60px;
        right: -40px;
        width: 240px;
        height: 240px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.35) 0%, rgba(139, 92, 246, 0.1) 70%, transparent 100%);
        filter: blur(40px);
        pointer-events: none;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
        border: 1px solid rgba(139, 92, 246, 0.4);
        color: #c7d2fe;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 5px 14px;
        border-radius: 30px;
        margin-bottom: 12px;
    }

    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #60a5fa 0%, #a855f7 50%, #f43f5e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
        line-height: 1.2;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 400;
        line-height: 1.6;
        max-width: 820px;
    }

    .hero-specs-row {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 18px;
        padding-top: 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
    }

    .hero-spec-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.82rem;
        color: #cbd5e1;
        background: rgba(15, 23, 42, 0.6);
        padding: 4px 12px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* KPI Metric Cards */
    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border-glass);
        border-radius: 16px;
        padding: 20px 22px;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        border-color: var(--border-accent);
        box-shadow: 0 12px 30px -10px rgba(99, 102, 241, 0.25);
    }
    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.6), transparent);
        opacity: 0;
        transition: opacity 0.25s ease;
    }
    .kpi-card:hover::before {
        opacity: 1;
    }
    .kpi-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        margin-top: 6px;
        letter-spacing: -0.02em;
    }
    .kpi-subtext {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 4px;
    }

    /* Citation Card Redesign */
    .citation-card {
        background: rgba(22, 30, 49, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
        backdrop-filter: blur(10px);
        transition: border-color 0.2s ease, transform 0.2s ease;
    }
    .citation-card:hover {
        border-color: rgba(99, 102, 241, 0.6);
        transform: translateX(2px);
    }
    .citation-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 10px;
    }
    .citation-title {
        font-weight: 700;
        font-size: 0.92rem;
        color: #e2e8f0;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    .citation-page-badge {
        background: rgba(148, 163, 184, 0.12);
        color: #cbd5e1;
        padding: 2px 9px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .citation-conf-badge {
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .conf-high {
        background: rgba(16, 185, 129, 0.18);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .conf-med {
        background: rgba(245, 158, 11, 0.18);
        color: #fcd34d;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    .conf-low {
        background: rgba(239, 68, 68, 0.18);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }

    .citation-meter-bar {
        width: 100%;
        height: 4px;
        background: rgba(15, 23, 42, 0.8);
        border-radius: 3px;
        overflow: hidden;
        margin-bottom: 10px;
    }
    .citation-meter-fill {
        height: 100%;
        background: linear-gradient(90deg, #6366f1, #10b981);
        border-radius: 3px;
    }

    .citation-snippet-quote {
        background: rgba(15, 23, 42, 0.5);
        border-left: 3px solid #6366f1;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        color: #cbd5e1;
        font-size: 0.88rem;
        line-height: 1.6;
        font-style: italic;
    }

    /* Diagnostics & Latency Pill */
    .metric-pill-container {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        margin-top: 10px;
    }
    .metric-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        color: #94a3b8;
        background: rgba(15, 23, 42, 0.7);
        padding: 5px 12px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Suggestion Chips Section */
    .chip-category-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Streamlit Tab Bar Customization */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(15, 23, 42, 0.5);
        padding: 8px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.92rem;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(139, 92, 246, 0.25) 100%) !important;
        border: 1px solid rgba(99, 102, 241, 0.5) !important;
        color: #ffffff !important;
        font-weight: 700;
        box-shadow: 0 4px 15px -4px rgba(99, 102, 241, 0.3);
    }

    /* Architecture Flow Box */
    .arch-flow-box {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }
    .arch-step-badge {
        display: inline-block;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: #6366f1;
        color: #fff;
        text-align: center;
        line-height: 26px;
        font-weight: 700;
        font-size: 0.8rem;
        margin-right: 8px;
    }

    /* Streamlit Chat Messages Override */
    .stChatMessage {
        background-color: rgba(22, 30, 49, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        padding: 16px 20px !important;
        margin-bottom: 16px !important;
        backdrop-filter: blur(12px) !important;
    }

    /* Custom Toast / Alert Styling */
    div[data-testid="stNotification"] {
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Initialization & Presets
# ---------------------------------------------------------
api_client = RAGApiClient()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "top_k" not in st.session_state:
    st.session_state.top_k = 4

if "model_name" not in st.session_state:
    st.session_state.model_name = "llama3:8b"

if "prompt_mode" not in st.session_state:
    st.session_state.prompt_mode = "academic"

if "selected_docs" not in st.session_state:
    st.session_state.selected_docs = []

if "sim_threshold" not in st.session_state:
    st.session_state.sim_threshold = 1.0

if "query_history" not in st.session_state:
    st.session_state.query_history = []

if "feedback_store" not in st.session_state:
    st.session_state.feedback_store = {}

if "preset_mode" not in st.session_state:
    st.session_state.preset_mode = "⚖️ Balanced Assistant"

# Helper for streaming responses
def text_stream_generator(full_text: str):
    words = full_text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(0.012)

# Helper for confidence class
def get_confidence_meta(conf_val):
    if conf_val is None:
        return "conf-med", "Medium", 65
    c = float(conf_val)
    if c >= 80:
        return "conf-high", "High", min(100, max(0, c))
    elif c >= 55:
        return "conf-med", "Medium", min(100, max(0, c))
    else:
        return "conf-low", "Low", min(100, max(0, c))

# ---------------------------------------------------------
# Check Backend Health (Cached check per rerun)
# ---------------------------------------------------------
is_online, health_data = api_client.check_health()
ping_ms = health_data.get("ping_ms", 0)
doc_count = health_data.get("document_count", 0)
active_docs = health_data.get("active_documents", [])
vector_ok = health_data.get("vector_db_loaded", False)
ollama_ok = health_data.get("ollama_available", False)

# ---------------------------------------------------------
# Sidebar Controls & System Diagnostics
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <span style="font-size: 2.2rem;">📚</span>
        <div>
            <div style="font-weight: 800; font-size: 1.15rem; color: #f8fafc; letter-spacing: -0.01em;">RAG Assistant</div>
            <div style="font-size: 0.76rem; color: #94a3b8; font-weight: 600;">ENTERPRISE STUDIO PRO</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Real-Time Service Status Badges
    st.markdown("##### 🛰️ System Status")
    if is_online:
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 10px; padding: 10px 14px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.85rem; font-weight: 700; color: #6ee7b7;">🟢 API Online</span>
                <span style="font-size: 0.75rem; color: #a7f3d0; font-family: 'JetBrains Mono';">{ping_ms} ms</span>
            </div>
            <div style="font-size: 0.76rem; color: #cbd5e1; margin-top: 4px;">
                ChromaDB: <b>{'Active' if vector_ok else 'Inactive'}</b> ({doc_count} chunks)<br>
                LLM Engine: <b>{'Ollama Online' if ollama_ok else 'Extractive Fallback'}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 10px; padding: 10px 14px; margin-bottom: 12px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #fca5a5;">🔴 Backend Offline</div>
            <div style="font-size: 0.74rem; color: #e2e8f0; margin-top: 4px;">
                Run: <code>uvicorn backend.app.main:app --reload</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### ⚡ Quick Optimization Presets")

    preset_choice = st.selectbox(
        "Load Preset Profile",
        options=[
            "🎯 Precision & Strict Grounding",
            "⚖️ Balanced Assistant",
            "📖 Deep Research & Comprehensive",
            "⚡ Rapid Quick-Fire",
            "🛠️ Custom Tuning"
        ],
        index=["🎯 Precision & Strict Grounding", "⚖️ Balanced Assistant", "📖 Deep Research & Comprehensive", "⚡ Rapid Quick-Fire", "🛠️ Custom Tuning"].index(
            st.session_state.preset_mode if st.session_state.preset_mode in [
                "🎯 Precision & Strict Grounding", "⚖️ Balanced Assistant", "📖 Deep Research & Comprehensive", "⚡ Rapid Quick-Fire", "🛠️ Custom Tuning"
            ] else "⚖️ Balanced Assistant"
        )
    )

    if preset_choice != st.session_state.preset_mode:
        st.session_state.preset_mode = preset_choice
        if preset_choice == "🎯 Precision & Strict Grounding":
            st.session_state.top_k = 2
            st.session_state.sim_threshold = 0.75
            st.session_state.prompt_mode = "academic"
        elif preset_choice == "⚖️ Balanced Assistant":
            st.session_state.top_k = 4
            st.session_state.sim_threshold = 1.00
            st.session_state.prompt_mode = "academic"
        elif preset_choice == "📖 Deep Research & Comprehensive":
            st.session_state.top_k = 8
            st.session_state.sim_threshold = 1.30
            st.session_state.prompt_mode = "detailed"
        elif preset_choice == "⚡ Rapid Quick-Fire":
            st.session_state.top_k = 2
            st.session_state.sim_threshold = 1.00
            st.session_state.prompt_mode = "concise"

    # Quick tuning parameters
    st.markdown("---")
    st.markdown("##### 🎛️ Active Runtime Tuning")
    st.session_state.top_k = st.slider(
        "Context Chunks (Top-K)",
        min_value=1,
        max_value=12,
        value=st.session_state.top_k,
        help="Higher values inject more context excerpts into the LLM prompt."
    )

    st.session_state.prompt_mode = st.selectbox(
        "Response Persona",
        options=["academic", "concise", "detailed", "summary"],
        index=["academic", "concise", "detailed", "summary"].index(st.session_state.prompt_mode),
        format_func=lambda x: {
            "academic": "🎓 Academic & Formal",
            "concise": "⚡ Ultra-Concise Bullets",
            "detailed": "📖 Comprehensive Tutorial",
            "summary": "📑 Executive Summary"
        }.get(x, x)
    )

    st.markdown("---")
    st.markdown("##### 📊 Session Activity")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("Queries", len(st.session_state.query_history))
    with col_s2:
        avg_lat = (
            sum(q.get("latency_ms", 0) for q in st.session_state.query_history) / len(st.session_state.query_history)
            if st.session_state.query_history else 0
        )
        st.metric("Avg Latency", f"{avg_lat:.0f}ms")

    st.markdown("---")
    # Chat History Maintenance
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with c_btn2:
        if st.button("🔄 Sync Status", use_container_width=True):
            st.rerun()

    # Chat Export
    if st.session_state.messages:
        # Markdown Export
        md_export = "# RAG Assistant Studio - Conversation Transcript\n\n"
        md_export += f"- Export Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        md_export += f"- Active Model: {st.session_state.model_name}\n"
        md_export += f"- Top-K Chunks: {st.session_state.top_k}\n\n---\n\n"
        for m in st.session_state.messages:
            role = m['role'].capitalize()
            md_export += f"### {role}\n{m['content']}\n\n"
            if m.get("sources"):
                md_export += "**Cited Sources:**\n"
                for s in m["sources"]:
                    md_export += f"- *{s.get('document', 'Unknown')}* (Page {s.get('page', 1)})\n"
                md_export += "\n"

        st.download_button(
            label="📥 Export Markdown",
            data=md_export,
            file_name=f"rag_conversation_{int(time.time())}.md",
            mime="text/markdown",
            use_container_width=True
        )

        # JSON Export
        json_export = json.dumps(st.session_state.messages, indent=2)
        st.download_button(
            label="📦 Export JSON",
            data=json_export,
            file_name=f"rag_transcript_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True
        )

# ---------------------------------------------------------
# Main Top Hero Studio Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-glow-orb"></div>
    <div class="hero-badge">⚡ RAG DOCUMENT ASSISTANT STUDIO • PRO V2.0</div>
    <div class="hero-title">Intelligent Document Assistant & Vector Studio</div>
    <div class="hero-subtitle">
        High-performance Retrieval-Augmented Generation platform featuring sub-100ms dense semantic vector search, 
        automatic document page citations, recursive chunking, and multi-persona local LLM reasoning.
    </div>
    <div class="hero-specs-row">
        <div class="hero-spec-item">🔍 <b>Embedding Model:</b> all-MiniLM-L6-v2 (384-D)</div>
        <div class="hero-spec-item">🗄️ <b>Vector Database:</b> ChromaDB Persistent Storage</div>
        <div class="hero-spec-item">🤖 <b>Reasoning Engine:</b> Ollama Local LLM & Extractive Fallback</div>
        <div class="hero-spec-item">📄 <b>Supported Formats:</b> PDF, TXT, Markdown</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Main Navigation Tabs
# ---------------------------------------------------------
tab_chat, tab_docs, tab_settings, tab_analytics = st.tabs([
    "💬 Intelligent Assistant",
    f"📁 Document Library ({len(active_docs)})",
    "⚙️ RAG Studio Settings",
    "📊 Analytics & Performance"
])

# =========================================================
# TAB 1: Intelligent Assistant & Chat Studio
# =========================================================
with tab_chat:
    # Notification Banner if filtering is active
    if st.session_state.selected_docs:
        docs_str = ", ".join([f"<code>{d}</code>" for d in st.session_state.selected_docs])
        c_notice1, c_notice2 = st.columns([5, 1])
        with c_notice1:
            st.markdown(
                f"<div style='background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 10px; padding: 8px 16px; margin-bottom: 12px; font-size: 0.88rem; color: #c7d2fe;'>"
                f"🎯 <b>Document Filter Active:</b> Query is constrained exclusively to {docs_str}."
                f"</div>",
                unsafe_allow_html=True
            )
        with c_notice2:
            if st.button("Reset Filter", key="btn_reset_filter_chat"):
                st.session_state.selected_docs = []
                st.rerun()

    # Categorized Prompt Suggestions Bar
    st.markdown("<div class='chip-category-title'>💡 Suggested Topics & Prompt Library</div>", unsafe_allow_html=True)

    prompt_categories = {
        "🧱 Data Structures": [
            "What is the average lookup complexity of a hash table?",
            "What is the time complexity of MergeSort and how does divide-and-conquer apply?"
        ],
        "🧠 Machine Learning": [
            "What are the key differences between Supervised and Unsupervised Learning?",
            "How does gradient descent optimize weights during training?"
        ],
        "🐍 Python Internals": [
            "What are the four core pillars of Object-Oriented Programming?",
            "How does Python manage memory and what is the role of garbage collection?"
        ],
        "🔍 RAG Architecture": [
            "How does Retrieval-Augmented Generation (RAG) work?",
            "What role does dense vector cosine similarity play in semantic retrieval?"
        ]
    }

    selected_category = st.radio(
        "Choose prompt topic:",
        options=list(prompt_categories.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )

    curr_queries = prompt_categories.get(selected_category, [])
    chip_cols = st.columns(len(curr_queries))
    for idx, prompt_text in enumerate(curr_queries):
        if chip_cols[idx].button(f"👉 {prompt_text}", key=f"chip_btn_{idx}", use_container_width=True):
            st.session_state.pending_query = prompt_text

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    # Render Chat History
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

            # Rich Citation Cards
            if msg.get("sources"):
                st.markdown("<div style='margin-top: 14px; margin-bottom: 6px; font-weight: 700; font-size: 0.9rem; color: #cbd5e1;'>📚 Verified Evidence & Citations:</div>", unsafe_allow_html=True)
                for s_idx, src in enumerate(msg["sources"]):
                    doc = src.get("document", "Unknown")
                    page = src.get("page", 1)
                    snippet = src.get("snippet", "")
                    conf = src.get("confidence_percent")

                    badge_class, badge_label, conf_width = get_confidence_meta(conf)
                    conf_display = f"{conf}% Match ({badge_label})" if conf is not None else "Indexed Excerpt"

                    st.markdown(f"""
                    <div class="citation-card">
                        <div class="citation-header">
                            <span class="citation-title">📄 {doc}</span>
                            <div style="display: flex; gap: 8px; align-items: center;">
                                <span class="citation-page-badge">Page {page}</span>
                                <span class="citation-conf-badge {badge_class}">{conf_display}</span>
                            </div>
                        </div>
                        <div class="citation-meter-bar">
                            <div class="citation-meter-fill" style="width: {conf_width}%;"></div>
                        </div>
                        <div class="citation-snippet-quote">"{snippet}"</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Execution Diagnostics Pill
            if msg.get("metrics"):
                m = msg["metrics"]
                lat_total = m.get("latency_ms", 0)
                lat_ret = m.get("retrieval_latency_ms", 0)
                lat_gen = m.get("generation_latency_ms", 0)
                model_used = m.get("model_used", "Local LLM")
                fallback_used = m.get("fallback_used", False)
                fallback_tag = "<span style='color: #f59e0b; font-weight: 700;'>• Fallback Engine Active</span>" if fallback_used else ""

                st.markdown(f"""
                <div class="metric-pill-container">
                    <div class="metric-pill">⚡ Total: <b>{lat_total:.0f}ms</b> (Retrieval: {lat_ret:.0f}ms | Generation: {lat_gen:.0f}ms)</div>
                    <div class="metric-pill">🤖 Model: <b>{model_used}</b> {fallback_tag}</div>
                </div>
                """, unsafe_allow_html=True)

            # Assistant Turn Action Bar (Feedback & Copy)
            if msg["role"] == "assistant":
                action_c1, action_c2, action_c3 = st.columns([1, 1, 6])
                with action_c1:
                    if st.button("👍", key=f"thumb_up_{idx}", help="Mark response as helpful"):
                        st.session_state.feedback_store[idx] = "up"
                        st.toast("Thank you for your feedback! 👍")
                with action_c2:
                    if st.button("👎", key=f"thumb_down_{idx}", help="Mark response as inaccurate"):
                        st.session_state.feedback_store[idx] = "down"
                        st.toast("Feedback noted. We will refine grounding! 👎")
                with action_c3:
                    with st.expander("🔍 Inspect Grounding Diagnostics"):
                        st.json({
                            "metrics": msg.get("metrics", {}),
                            "citation_count": len(msg.get("sources", [])),
                            "timestamp": msg.get("timestamp", time.strftime("%H:%M:%S"))
                        })

    # Chat Input Box
    query_input = st.chat_input("Ask a question grounded in your document library...")

    if getattr(st.session_state, "pending_query", None):
        query_input = st.session_state.pending_query
        del st.session_state.pending_query

    if query_input:
        # Append User Turn
        st.session_state.messages.append({"role": "user", "content": query_input, "timestamp": time.strftime("%H:%M:%S")})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(query_input)

        # Process via API Client
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔍 Retrieving dense vector embeddings & generating grounded response..."):
                recent_history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[-5:-1]
                ]

                success, response = api_client.submit_query(
                    question=query_input,
                    top_k=st.session_state.top_k,
                    model=st.session_state.model_name,
                    document_filter=st.session_state.selected_docs if st.session_state.selected_docs else None,
                    similarity_threshold=st.session_state.sim_threshold,
                    system_prompt_mode=st.session_state.prompt_mode,
                    chat_history=recent_history
                )

                if success:
                    answer = response.get("answer", "No answer generated.")
                    sources = response.get("sources", [])
                    metrics = {
                        "latency_ms": response.get("latency_ms", 0),
                        "retrieval_latency_ms": response.get("retrieval_latency_ms", 0),
                        "generation_latency_ms": response.get("generation_latency_ms", 0),
                        "model_used": response.get("model_used", "N/A"),
                        "fallback_used": response.get("fallback_used", False)
                    }

                    # Stream Answer Dynamically
                    st.write_stream(text_stream_generator(answer))

                    # Render Verified Sources
                    if sources:
                        st.markdown("<div style='margin-top: 14px; margin-bottom: 6px; font-weight: 700; font-size: 0.9rem; color: #cbd5e1;'>📚 Verified Evidence & Citations:</div>", unsafe_allow_html=True)
                        for src in sources:
                            doc = src.get("document", "Unknown")
                            page = src.get("page", 1)
                            snippet = src.get("snippet", "")
                            conf = src.get("confidence_percent")

                            badge_class, badge_label, conf_width = get_confidence_meta(conf)
                            conf_display = f"{conf}% Match ({badge_label})" if conf is not None else "Indexed Excerpt"

                            st.markdown(f"""
                            <div class="citation-card">
                                <div class="citation-header">
                                    <span class="citation-title">📄 {doc}</span>
                                    <div style="display: flex; gap: 8px; align-items: center;">
                                        <span class="citation-page-badge">Page {page}</span>
                                        <span class="citation-conf-badge {badge_class}">{conf_display}</span>
                                    </div>
                                </div>
                                <div class="citation-meter-bar">
                                    <div class="citation-meter-fill" style="width: {conf_width}%;"></div>
                                </div>
                                <div class="citation-snippet-quote">"{snippet}"</div>
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="metric-pill-container">
                        <div class="metric-pill">⚡ Total: <b>{metrics['latency_ms']:.0f}ms</b> (Retrieval: {metrics['retrieval_latency_ms']:.0f}ms | Generation: {metrics['generation_latency_ms']:.0f}ms)</div>
                        <div class="metric-pill">🤖 Model: <b>{metrics['model_used']}</b></div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Save to Session State
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "metrics": metrics,
                        "timestamp": time.strftime("%H:%M:%S")
                    })

                    # Log to Session Query History for Analytics
                    st.session_state.query_history.append({
                        "question": query_input,
                        "latency_ms": metrics["latency_ms"],
                        "retrieval_ms": metrics["retrieval_latency_ms"],
                        "generation_ms": metrics["generation_latency_ms"],
                        "sources_count": len(sources),
                        "model": metrics["model_used"],
                        "timestamp": time.strftime("%H:%M:%S")
                    })
                else:
                    error_msg = response.get("error", "An error occurred.")
                    st.error(f"⚠️ {error_msg}")


# =========================================================
# TAB 2: Document Management & Dynamic Ingestion
# =========================================================
with tab_docs:
    st.markdown("### 📁 Document Library & Real-time Ingestion Engine")
    st.markdown("Upload new PDF, Markdown, or TXT documents to immediately extract text, generate 384-D dense embeddings, and persist them into ChromaDB.")

    col_up, col_info = st.columns([1.6, 1])

    with col_up:
        uploaded_files = st.file_uploader(
            "Upload Documents (PDF, TXT, MD)",
            type=["pdf", "txt", "md"],
            accept_multiple_files=True,
            help="Files will be parsed, cleaned, recursively chunked, and embedded."
        )

        # Quick Actions Row
        c_up1, c_up2 = st.columns([1.2, 1])
        with c_up1:
            if uploaded_files:
                if st.button("🚀 Ingest & Index Uploaded Documents", type="primary", use_container_width=True):
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for idx, file_item in enumerate(uploaded_files):
                        status_text.markdown(f"**Step 1/4:** Reading and extracting text from `{file_item.name}`...")
                        file_bytes = file_item.read()
                        status_text.markdown(f"**Step 2/4:** Recursive semantic chunking (size=800, overlap=150)...")
                        time.sleep(0.1)
                        status_text.markdown(f"**Step 3/4:** Generating 384-D dense vector embeddings...")

                        ok, resp = api_client.upload_document(file_bytes, file_item.name)

                        if ok:
                            st.success(f"✅ Indexed **{file_item.name}**: {resp.get('chunks_indexed', 0)} chunks across {resp.get('pages', 1)} pages.")
                        else:
                            st.error(f"❌ Failed to index **{file_item.name}**: {resp.get('error')}")

                        progress_bar.progress((idx + 1) / len(uploaded_files))

                    status_text.markdown("✨ **Batch Ingestion Complete!**")
                    time.sleep(1)
                    st.rerun()

        with c_up2:
            # One-click demo loader from local data/raw
            sample_files = api_client.get_sample_raw_files()
            if sample_files:
                if st.button("📥 Ingest Demo CS Coursework (3 PDFs)", use_container_width=True, help="Load pre-bundled CS sample PDFs into vector database"):
                    s_prog = st.progress(0)
                    s_status = st.empty()
                    for s_i, sf in enumerate(sample_files):
                        s_status.text(f"Ingesting {sf['filename']}...")
                        ok_s, resp_s = api_client.ingest_local_sample_file(sf["filepath"])
                        if ok_s:
                            st.success(f"✅ Indexed {sf['filename']} ({resp_s.get('chunks_indexed', 0)} chunks)")
                        s_prog.progress((s_i + 1) / len(sample_files))
                    s_status.text("Demo documents loaded successfully!")
                    time.sleep(1)
                    st.rerun()

    with col_info:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">⚡ Ingestion Pipeline Architecture</div>
            <div style="font-size: 0.88rem; margin-top: 10px; color: #cbd5e1; line-height: 1.7;">
                • <b>Recursive Chunk Size:</b> 800 characters<br>
                • <b>Chunk Overlap:</b> 150 characters<br>
                • <b>Dense Embeddings:</b> all-MiniLM-L6-v2 (384-D)<br>
                • <b>Storage Backend:</b> Disk Persistent ChromaDB<br>
                • <b>Citation Integrity:</b> Exact Page Tracking
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📑 Currently Indexed Documents")

    doc_ok, doc_data = api_client.get_documents()
    if doc_ok and doc_data.get("documents"):
        docs_list = doc_data.get("documents", [])

        # Search / filter within table
        search_filter = st.text_input("🔍 Filter Indexed Documents by Filename:", placeholder="Type to filter...")

        table_rows = []
        for d in docs_list:
            d_name = d.get("document_name", "")
            if search_filter and search_filter.lower() not in d_name.lower():
                continue

            size_kb = f"{d.get('file_size_bytes', 0) / 1024:.1f} KB" if d.get("file_size_bytes") else "N/A"
            table_rows.append({
                "Document Name": d_name,
                "Pages Detected": d.get("page_count", 1),
                "Vector Chunks": d.get("chunk_count", 0),
                "Characters Extracted": f"{d.get('char_count', 0):,}",
                "Estimated Size": size_kb
            })

        if table_rows:
            df_docs = pd.DataFrame(table_rows)
            st.dataframe(df_docs, use_container_width=True)
        else:
            st.info(f"No documents matched search filter '{search_filter}'.")

        # Document Drilldown Inspector
        st.markdown("##### 🔬 Document Details & Chunk Breakdown")
        doc_names = [d["Document Name"] for d in table_rows]
        inspected_doc = st.selectbox("Inspect metadata for document:", options=doc_names, key="inspect_doc_select")

        if inspected_doc:
            target_meta = next((d for d in docs_list if d.get("document_name") == inspected_doc), None)
            if target_meta:
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Total Pages", target_meta.get("page_count", 1))
                with m2:
                    st.metric("Indexed Chunks", target_meta.get("chunk_count", 0))
                with m3:
                    st.metric("Total Characters", f"{target_meta.get('char_count', 0):,}")
                with m4:
                    avg_c = target_meta.get("char_count", 0) / max(1, target_meta.get("chunk_count", 1))
                    st.metric("Avg Chunk Size", f"{avg_c:.0f} chars")

        st.markdown("---")
        # Document Management Actions
        del_col1, del_col2 = st.columns([3, 1])
        with del_col1:
            doc_to_delete = st.selectbox(
                "Select a document to permanently remove from ChromaDB vector index:",
                options=[d["Document Name"] for d in table_rows],
                key="select_del_doc"
            )
        with del_col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Delete Selected Document", type="secondary", use_container_width=True):
                if doc_to_delete:
                    del_ok, del_resp = api_client.delete_document(doc_to_delete)
                    if del_ok:
                        st.success(f"Removed '{doc_to_delete}' ({del_resp.get('chunks_deleted', 0)} chunks deleted).")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed to delete: {del_resp.get('error')}")

        st.markdown("---")
        if st.button("🔄 Trigger Full Re-Index of Raw Documents Directory", use_container_width=True):
            with st.spinner("Rebuilding entire vector index from scratch..."):
                re_ok, re_resp = api_client.reindex_documents()
                if re_ok:
                    st.success("Corpus successfully re-indexed into ChromaDB!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Reindexing failed: {re_resp.get('error')}")
    else:
        st.info("No documents currently indexed or vector store is empty. Upload documents above or click 'Ingest Demo CS Coursework' to begin!")


# =========================================================
# TAB 3: RAG Studio Settings & Pipeline Tuning
# =========================================================
with tab_settings:
    st.markdown("### ⚙️ RAG Pipeline Studio & Hyperparameter Tuning")
    st.markdown("Fine-tune dense retrieval mechanics, LLM temperature grounding, and prompt persona constraints.")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 🤖 LLM Reasoning Engine Configuration")

        # Check installed models from analytics
        an_ok, an_data = api_client.get_analytics()
        available_models = []
        if an_ok:
            available_models = an_data.get("ollama_status", {}).get("available_models", [])

        if available_models:
            model_options = list(set(available_models + [st.session_state.model_name, "llama3:8b", "mistral", "phi3", "gemma2"]))
            selected_model = st.selectbox(
                "Ollama Model Architecture",
                options=model_options,
                index=model_options.index(st.session_state.model_name) if st.session_state.model_name in model_options else 0,
                help="Detected models from local Ollama daemon."
            )
            st.session_state.model_name = selected_model
        else:
            model_input = st.text_input(
                "Ollama Model Name",
                value=st.session_state.model_name,
                help="Specify model tag (e.g. 'llama3:8b', 'mistral', 'phi3', 'gemma2')"
            )
            st.session_state.model_name = model_input

        st.markdown("#### 🎯 Target Document Scoping")
        all_docs = [d.get("document_name") for d in doc_data.get("documents", [])] if (doc_ok and doc_data.get("documents")) else []
        selected = st.multiselect(
            "Restrict vector retrieval to specific documents (Leave empty to search entire corpus):",
            options=all_docs,
            default=st.session_state.selected_docs
        )
        st.session_state.selected_docs = selected

        c_sel1, c_sel2 = st.columns(2)
        with c_sel1:
            if st.button("Select All Documents", use_container_width=True):
                st.session_state.selected_docs = all_docs
                st.rerun()
        with c_sel2:
            if st.button("Clear Document Scope", use_container_width=True):
                st.session_state.selected_docs = []
                st.rerun()

    with c2:
        st.markdown("#### 🔍 Semantic Vector Retrieval Tuning")
        st.session_state.top_k = st.slider(
            "Top-K Chunks to Retrieve",
            min_value=1,
            max_value=12,
            value=st.session_state.top_k,
            help="Higher values provide more context to the LLM but increase latency and token consumption."
        )

        st.session_state.sim_threshold = st.slider(
            "Cosine Distance Cutoff (Similarity Threshold)",
            min_value=0.2,
            max_value=1.5,
            value=float(st.session_state.sim_threshold),
            step=0.05,
            help="Filters out chunks with distance higher than this threshold (lower = stricter similarity)."
        )

        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.6); padding: 10px 14px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.05); font-size: 0.82rem; color: #94a3b8; margin-top: 6px;">
            <b>Threshold Guide:</b><br>
            • <code>&lt; 0.75</code>: Strict Grounding (High Precision, may reject loosely related text)<br>
            • <code>0.75 - 1.10</code>: Balanced Semantic Match (Optimal for standard Q&A)<br>
            • <code>&gt; 1.15</code>: Broad Recall (Retrieves peripheral contextual mentions)
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🛡️ Grounding Guardrails & Prompt Persona Template")

    persona_templates = {
        "academic": "You are a distinguished academic researcher and technical assistant. Provide rigorous, scholarly, and logically organized explanations citing exact document and page sources.",
        "concise": "You are a concise executive assistant. Provide direct, high-impact bulleted answers answering only what was explicitly asked. Do not include fluff.",
        "detailed": "You are an expert tutor. Provide comprehensive, step-by-step instructional breakdowns with intuitive examples and clear structural headers.",
        "summary": "You are an executive summary specialist. Synthesize key takeaways into clear, actionable executive summaries with highlighted bullet points."
    }

    st.markdown(f"**Active Mode:** `{st.session_state.prompt_mode.capitalize()}`")
    st.info(f"📋 **Injected System Persona Directive:**\n\n\"{persona_templates.get(st.session_state.prompt_mode, '')}\"")


# =========================================================
# TAB 4: Analytics & Performance Insights
# =========================================================
with tab_analytics:
    st.markdown("### 📊 Vector Corpus Analytics & Pipeline Performance")

    an_ok, an_data = api_client.get_analytics()

    if an_ok:
        total_docs = an_data.get("total_documents", 0)
        total_chunks = an_data.get("total_chunks", 0)
        emb_model = an_data.get("embedding_model", "all-MiniLM-L6-v2")
        ollama_status = an_data.get("ollama_status", {})

        # KPI Metrics Row
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Documents</div>
                <div class="kpi-value">{total_docs}</div>
                <div class="kpi-subtext">Active indexed files</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Vector Embeddings</div>
                <div class="kpi-value">{total_chunks}</div>
                <div class="kpi-subtext">Persisted in ChromaDB</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Vector Dimension</div>
                <div class="kpi-value">384-D</div>
                <div class="kpi-subtext">SentenceTransformer dense space</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">API Roundtrip Ping</div>
                <div class="kpi-value" style="font-size: 1.5rem;">{ping_ms} ms</div>
                <div class="kpi-subtext">FastAPI service latency</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Session Latency Chart if queries have been run
        if st.session_state.query_history:
            st.markdown("#### ⚡ Session Latency Trend (Retrieval vs Generation)")
            lat_df = pd.DataFrame([
                {
                    "Turn": f"Q{i+1}: {q['question'][:22]}...",
                    "Retrieval Latency (ms)": q["retrieval_ms"],
                    "Generation Latency (ms)": q["generation_ms"],
                    "Total Latency (ms)": q["latency_ms"]
                }
                for i, q in enumerate(st.session_state.query_history)
            ]).set_index("Turn")
            st.area_chart(lat_df[["Retrieval Latency (ms)", "Generation Latency (ms)"]], color=["#6366f1", "#a855f7"])

        # Chunks Distribution Bar Chart
        docs_info = an_data.get("documents", [])
        if docs_info:
            c_ch1, c_ch2 = st.columns(2)
            with c_ch1:
                st.markdown("#### 📈 Chunks Distribution per Document")
                chart_df = pd.DataFrame([
                    {"Document": d["document_name"], "Chunks": d["chunk_count"]}
                    for d in docs_info
                ]).set_index("Document")
                st.bar_chart(chart_df, color="#6366f1")

            with c_ch2:
                st.markdown("#### 🔤 Character Volume per Document")
                char_df = pd.DataFrame([
                    {"Document": d["document_name"], "Characters": d.get("char_count", 0)}
                    for d in docs_info
                ]).set_index("Document")
                st.bar_chart(char_df, color="#a855f7")

        st.markdown("---")
        st.markdown("#### 🏛️ System Runtime Architecture Matrix")
        col_srv1, col_srv2 = st.columns(2)
        with col_srv1:
            st.write("**Vector Store Persistent Path:**")
            st.code(an_data.get("vector_store_path", "N/A"))
            st.write("**ChromaDB Collection Identifier:**")
            st.code(an_data.get("collection_name", "rag_documents"))
        with col_srv2:
            st.write("**Ollama Daemon Endpoint:**")
            st.code(ollama_status.get("host", "http://localhost:11434"))
            models_list = ollama_status.get("available_models", [])
            if models_list:
                st.write(f"**Detected Local Models ({len(models_list)}):** {', '.join(models_list)}")
            else:
                st.caption("No models detected or daemon offline (Extractive fallback active).")
    else:
        st.warning("⚠️ Could not fetch analytics from backend API. Ensure the FastAPI server is running.")

st.markdown("""
<div style="text-align: center; margin-top: 40px; padding: 20px; color: #64748b; font-size: 0.8rem; border-top: 1px solid rgba(255, 255, 255, 0.05);">
    RAG-Powered Document Assistant • Engineered for Graduation & Training Project Demonstration • Local AI Architecture
</div>
""", unsafe_allow_html=True)
