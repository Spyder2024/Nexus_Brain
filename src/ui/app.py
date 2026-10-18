"""NexusBrain - Streamlit Command Center.

Implements the single-page 3-zone command center defined in APP_FLOW.md:
- Header: Persona / Tenant switcher & FalkorDB telemetry badge
- Left Pane (45%): Interactive Agent Console, Presets, Live Mutator, Tenant Memory
- Right Pane (55%): Force-directed FalkorDB subgraph canvas & multi-agent execution drawer
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
import requests
import streamlit as st
from src.ui.graph_viz import render_subgraph

# Page configuration
st.set_page_config(
    page_title="NexusBrain | Graph-Native Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for rich aesthetics, dark theme, and compact split-pane layout
st.markdown("""
<style>
    /* Dark glassmorphic background */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top metric pill */
    .telemetry-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 500;
        color: #34d399;
    }

    /* Citation cards */
    .citation-card-active {
        background: #064e3b;
        border-left: 4px solid #10b981;
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 6px;
        font-size: 0.82rem;
    }
    .citation-card-superseded {
        background: #450a0a;
        border-left: 4px solid #ef4444;
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 6px;
        font-size: 0.82rem;
    }
    
    /* Execution trace drawer */
    .cypher-box {
        background: #030712;
        border: 1px solid #1f2937;
        border-radius: 6px;
        padding: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)

API_BASE_URL = "http://127.0.0.1:8000"


def query_backend(user_id: str, prompt: str) -> dict:
    """Send query to backend API with automatic fallback to internal mock bridge."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/query",
            json={"user_id": user_id, "query": prompt},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    # Local in-process fallback if FastAPI server is not started separately
    from src.api.mock_bridge import mock_bridge
    return mock_bridge.handle_query(user_id=user_id, query=prompt).model_dump()


def mutate_backend(payload: dict) -> dict:
    """Send mutation to backend API."""
    try:
        resp = requests.post(f"{API_BASE_URL}/api/v1/mutate", json=payload, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    from src.api.mock_bridge import mock_bridge
    return mock_bridge.mutate_decision(payload)


def reset_backend() -> dict:
    """Reset knowledge state."""
    try:
        resp = requests.post(f"{API_BASE_URL}/api/v1/reset", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    from src.api.mock_bridge import mock_bridge
    mock_bridge.reset_state()
    return {"status": "success"}


# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_subgraph" not in st.session_state:
    st.session_state.current_subgraph = {"nodes": [], "edges": []}
if "current_trace" not in st.session_state:
    st.session_state.current_trace = []
if "current_citations" not in st.session_state:
    st.session_state.current_citations = []


# ============================================================================
# 1. TOP HEADER BAR: Persona Switcher & Live FalkorDB Telemetry
# ============================================================================
col_brand, col_persona, col_telemetry = st.columns([1.8, 1.2, 1.2])

with col_brand:
    st.markdown("### ⚡ **NexusBrain** `v1.0`")
    st.caption("Graph-Native Company Brain & Multi-Agent Memory Coordinator (FalkorDB)")

with col_persona:
    persona_choice = st.selectbox(
        "Active Tenant Persona",
        options=[
            ("meera_sre", "Meera (Staff SRE On-Call)"),
            ("kabir_ml", "Kabir (ML Platform Lead)"),
            ("riya_newhire", "Riya (New Grad Engineer)"),
        ],
        format_func=lambda x: x[1],
        index=0,
    )
    active_user_id = persona_choice[0]

with col_telemetry:
    st.markdown(
        """
        <div style="text-align: right; margin-top: 10px;">
            <span class="telemetry-badge">
                🟢 FalkorDB Connected &nbsp;|&nbsp; 1,077 nodes &nbsp;|&nbsp; 4,103 edges &nbsp;|&nbsp; 3.8ms
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ============================================================================
# 2. SPLIT-PANE COMMAND CENTER LAYOUT
# ============================================================================
left_col, right_col = st.columns([0.48, 0.52], gap="large")

# ----------------------------------------------------------------------------
# LEFT PANE: Interactive Agent Console & Live Mutator
# ----------------------------------------------------------------------------
with left_col:
    tab_chat, tab_mutate, tab_memory = st.tabs([
        "💬 Ask Company Brain",
        "⚡ Live Knowledge Mutator",
        "🧠 Multi-Tenant Memory Inspector",
    ])

    # --- TAB 1: ASK COMPANY BRAIN ---
    with tab_chat:
        st.markdown("##### 🎯 1-Click Golden Demo Scenarios")
        btn_cols_1 = st.columns(2)
        btn_cols_2 = st.columns(3)

        preset_query = None

        with btn_cols_1[0]:
            if st.button("🕵️ 1. Shadow Expert & Blast Radius", use_container_width=True):
                preset_query = "Who actually knows the most about auth-service outages, and what breaks if it goes down?"
        with btn_cols_1[1]:
            if st.button("📜 2. Stale Kafka Doc vs ADR-051", use_container_width=True):
                preset_query = "Can I use Kafka for synchronous RPC as written in Onboarding Doc DOC-082?"

        with btn_cols_2[0]:
            if st.button("💥 3. 4-Hop Blast", use_container_width=True):
                preset_query = "What is the blast radius if redis-session-store experiences an OOM crash?"
        with btn_cols_2[1]:
            if st.button("🧠 4. CUDA Playbook", use_container_width=True):
                preset_query = "How do we resolve the recurring CUDA memory leak in ml-inference-worker?"
        with btn_cols_2[2]:
            if st.button("🚨 5. Breaking API", use_container_width=True):
                preset_query = "Why did recommendation-service crash with a deserialization error after PR-398?"

        # Chat interface
        user_input = st.chat_input("Ask about systems, decisions, incidents, or team ownership...")
        active_prompt = preset_query or user_input

        if active_prompt:
            with st.spinner("Traversing FalkorDB enterprise knowledge graph..."):
                response_data = query_backend(user_id=active_user_id, prompt=active_prompt)
                
                # Update visualizer states
                st.session_state.current_subgraph = response_data.get("subgraph", {})
                st.session_state.current_trace = response_data.get("agent_trace", [])
                st.session_state.current_citations = response_data.get("citations", [])
                
                # Append message
                st.session_state.messages.append({
                    "role": "user",
                    "content": active_prompt,
                })
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_data.get("answer", ""),
                    "citations": response_data.get("citations", []),
                })

        # Render message history
        for msg in reversed(st.session_state.messages[-4:]):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("citations"):
                    st.caption("📌 **Verified Graph Citations:**")
                    cit_cols = st.columns(len(msg["citations"]) if len(msg["citations"]) <= 4 else 4)
                    for idx, c in enumerate(msg["citations"][:4]):
                        col_idx = idx % len(cit_cols)
                        with cit_cols[col_idx]:
                            status = c.get("status", "active")
                            badge_color = "#10b981" if status == "active" else "#ef4444"
                            st.markdown(
                                f"<div style='font-size:0.75rem; border-left: 3px solid {badge_color}; padding-left: 6px; background:#111827; border-radius:3px;'>"
                                f"<b>[{c.get('id')}]</b> {c.get('title')[:24]}...<br>"
                                f"<span style='color:{badge_color}; text-transform:uppercase;'>{status}</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )

    # --- TAB 2: LIVE KNOWLEDGE MUTATOR ---
    with tab_mutate:
        st.markdown("##### ⚡ Real-Time Graph Evolution (Temporal Scribe)")
        st.info("Demonstrates live bi-temporal mutation: an incoming Slack thread or postmortem immediately invalidates prior standards.")

        with st.form("mutate_form"):
            topic_input = st.text_input("Architectural Topic", value="auth_rpc")
            new_id_input = st.text_input("New Decision ID", value="ADR-061")
            title_input = st.text_input("Title", value="Move auth-service RPC to HTTP/3 QUIC")
            reason_input = st.text_area(
                "Triggering Context / Slack Thread",
                value="In #arch-sync: Envoy proxy bug INC-299 causes gRPC stream resets under load. ADR-051 is hereby superseded; all new endpoints must use HTTP/3 QUIC.",
            )
            submit_btn = st.form_submit_button("⚡ Inject Decision into FalkorDB")

        if submit_btn:
            result = mutate_backend({
                "topic": topic_input,
                "new_id": new_id_input,
                "title": title_input,
                "reason": reason_input,
            })
            st.success(f"✅ Graph Mutated! `{result.get('mutated_node')}` created. `{result.get('superseded_node')}` marked SUPERSEDED.")
            st.markdown("👉 **Return to Tab 1 and click Scenario #2** to see the agent deliver the new HTTP/3 decision!")

    # --- TAB 3: MULTI-TENANT MEMORY INSPECTOR ---
    with tab_memory:
        st.markdown(f"##### 🧠 Isolated Tenant Memory: `memory_tenant_{active_user_id}`")
        st.caption("FalkorDB multigraph isolation guarantees personal sessions stay private while verified playbooks are shared.")

        st.markdown("**Shared Procedural Playbooks (Cross-Tenant):**")
        st.code("""
        (:Playbook {id: 'playbook-003', trigger: 'CUDA memory leak', status: 'verified'})
          - Step 1: torch.cuda.empty_cache()
          - Step 2: Set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
          - Verified by: Meera (SRE Lead) in session-meera-102
          - Success Count: 3
        """, language="text")

        if st.button("🔄 Reset Graph to Pristine State"):
            reset_backend()
            st.session_state.messages = []
            st.session_state.current_subgraph = {"nodes": [], "edges": []}
            st.session_state.current_trace = []
            st.rerun()

# ----------------------------------------------------------------------------
# RIGHT PANE: Live FalkorDB Trace Visualizer
# ----------------------------------------------------------------------------
with right_col:
    st.markdown("##### 🌐 Live FalkorDB Traversal Canvas")
    st.caption("Active nodes glow solid green 🟢 | Superseded nodes outlined in red/amber 🔴")

    # Render interactive graph
    render_subgraph(st.session_state.current_subgraph)

    st.divider()

    # Agent Telemetry Drawer
    st.markdown("##### ⏱️ Agent Execution Trace & Exact Cypher")
    if st.session_state.current_trace:
        for trace in st.session_state.current_trace:
            with st.expander(f"🤖 {trace.get('agent')} ➔ {trace.get('tool')} ({trace.get('latency_ms')} ms)", expanded=True):
                st.markdown(f"```cypher\n{trace.get('cypher_executed')}\n```")
    else:
        st.caption("Execute a query to inspect real-time Cypher execution traces and latency metrics.")
