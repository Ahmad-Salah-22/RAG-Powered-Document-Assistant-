import streamlit as st
from api_client import RAGApiClient

# Page Configuration
st.set_page_config(
    page_title="RAG Document Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern UI & Glassmorphism Aesthetics
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    
    /* Header Container */
    .header-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    .header-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
    }

    /* Response Cards */
    .answer-box {
        background: rgba(15, 23, 42, 0.8);
        border-left: 4px solid #3b82f6;
        border-radius: 12px;
        padding: 20px;
        margin-top: 16px;
        line-height: 1.6;
        font-size: 1.05rem;
    }

    /* Source Citation Badges */
    .source-badge {
        display: inline-block;
        background: rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(59, 130, 246, 0.4);
        color: #93c5fd;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    /* Status Badges */
    .status-online {
        color: #4ade80;
        font-weight: 600;
    }
    .status-offline {
        color: #f87171;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize API Client
api_client = RAGApiClient()

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Diagnostics & Configuration
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/books.png", width=64)
    st.title("System Diagnostic")
    
    # Check Backend Connection
    is_online, health_data = api_client.check_health()
    
    if is_online:
        st.markdown("🌐 **Backend API**: <span class='status-online'>Online</span>", unsafe_allow_html=True)
        
        vector_ok = health_data.get("vector_db_loaded", False)
        doc_count = health_data.get("document_count", 0)
        ollama_ok = health_data.get("ollama_available", False)
        
        st.write(f"📁 **Vector Store**: {'🟢 Active' if vector_ok else '🔴 Offline'} ({doc_count} chunks)")
        st.write(f"🦙 **Ollama Daemon**: {'🟢 Connected' if ollama_ok else '🟡 Not Reachable'}")
    else:
        st.markdown("🌐 **Backend API**: <span class='status-offline'>Offline</span>", unsafe_allow_html=True)
        st.error(health_data.get("error", "Backend server is unreachable."))
        st.info("💡 Start FastAPI server with:\n`uvicorn app.main:app --reload`")

    st.markdown("---")
    st.subheader("💡 Sample Questions")
    sample_queries = [
        "What is the average lookup complexity of a hash table?",
        "What are the four core pillars of Object-Oriented Programming?",
        "How does Retrieval-Augmented Generation (RAG) work?",
        "What is the time complexity of MergeSort?"
    ]
    
    for sq in sample_queries:
        if st.button(sq, key=f"btn_{sq}"):
            st.session_state.pending_query = sq

    st.markdown("---")
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# Main Application Layout
st.markdown("""
<div class="header-card">
    <div class="header-title">📚 RAG-Powered Document Assistant</div>
    <div class="header-subtitle">
        Ask questions grounded in academic CS course materials. Powered by SentenceTransformers, ChromaDB, FastAPI, & Ollama.
    </div>
</div>
""", unsafe_allow_html=True)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            st.markdown("**Sources Cited:**")
            for src in msg["sources"]:
                doc = src.get("document", "Unknown")
                page = src.get("page", 1)
                st.markdown(f"<span class='source-badge'>📄 {doc} — Page {page}</span>", unsafe_allow_html=True)

# Input Box / Pending Query
query_input = st.chat_input("Ask a question about your documents...")

# Handle sample button click selection
if getattr(st.session_state, "pending_query", None):
    query_input = st.session_state.pending_query
    del st.session_state.pending_query

if query_input:
    # Add User Message to History
    st.session_state.messages.append({"role": "user", "content": query_input})
    with st.chat_message("user"):
        st.markdown(query_input)

    # Process via Backend API
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching vector database & generating answer with Ollama..."):
            success, response = api_client.submit_query(query_input)

            if success:
                answer = response.get("answer", "No answer generated.")
                sources = response.get("sources", [])

                st.markdown(answer)

                if sources:
                    st.markdown("---")
                    st.markdown("#### 📚 Sources & Citations")
                    for src in sources:
                        doc = src.get("document", "Unknown")
                        page = src.get("page", 1)
                        snippet = src.get("snippet", "")
                        
                        with st.expander(f"📄 {doc} (Page {page})"):
                            st.write(f"**Extracted Snippet:** {snippet}")
                
                # Append Assistant Message to History
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
            else:
                error_msg = response.get("error", "An error occurred.")
                st.error(f"⚠️ {error_msg}")
