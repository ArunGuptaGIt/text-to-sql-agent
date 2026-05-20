"""
ui/app.py — Chat UI for the Text-to-SQL pipeline.

This Streamlit app acts as a client to the FastAPI backend.
"""

import sys
import json
import streamlit as st
import requests

# ─────────────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Query Interface",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }
    .stChatMessage { border-radius: 8px; }
    .badge {
        padding: 4px 10px; border-radius: 4px;
        font-weight: 600; font-size: 0.8rem; display: inline-block;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .badge-success { background-color: #2e7d32; color: white; }
    .badge-failed { background-color: #c62828; color: white; }
    .badge-retry { background-color: #f57f17; color: white; margin-left: 6px; }
    
    .header-text {
        font-size: 2rem; font-weight: 600; letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# Helper: Render a pipeline result
# ─────────────────────────────────────────────────────────────────────
def render_response(data: dict):
    """Render a pipeline result as a structured chat response."""

    # Status badge
    if data.get("status") == "success":
        badge = '<span class="badge badge-success">Success</span>'
    else:
        badge = '<span class="badge badge-failed">Failed</span>'
    
    if data.get("retry_needed"):
        badge += ' <span class="badge badge-retry">Retried</span>'
        
    st.markdown(badge, unsafe_allow_html=True)

    # Decomposition plan
    if data.get("plan"):
        with st.expander("Query Plan", expanded=False):
            st.json(data["plan"])

    # Generated SQL
    if data.get("sql"):
        with st.expander("Generated SQL", expanded=True):
            st.code(data["sql"], language="sql")

    # Error
    if data.get("error"):
        st.error(f"Execution Error: {data['error']}")

    # Results table
    if data.get("status") == "success" and data.get("result"):
        with st.expander(f"Results ({data.get('row_count', 0)} rows)", expanded=True):
            st.dataframe(data["result"], use_container_width=True, height=300)

    # Summary
    if data.get("summary"):
        st.markdown("---")
        st.markdown(f"**Analysis:** {data['summary']}")


def call_api(question: str, skip_summary: bool, dry_run: bool) -> dict:
    import os
    # Default to api container hostname in docker, fallback to localhost
    API_URL = os.getenv("API_URL", "http://api:8000")
    try:
        response = requests.post(
            f"{API_URL}/agent/sql",
            json={"question": question, "skip_summary": skip_summary, "dry_run": dry_run},
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "status": "failed",
            "error": f"API request failed: {e}",
            "summary": "Sorry, I could not reach the backend API."
        }


# ─────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Data Query Interface")
    st.markdown("---")

    st.markdown("#### Example Queries")
    examples = [
        "How many customers are from the USA?",
        "List all products with their prices",
        "Get total revenue from payments",
        "Show orders with customer names",
        "Average MSRP per product line",
        "Get employees with office city",
        "Count customers per country",
        "Top 10 most expensive products",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state["prefill"] = ex

    st.markdown("---")
    st.markdown("#### Process Overview")
    st.markdown("""
    1. **Decompose** — Parse requirement limits
    2. **Generate** — Construct SQL query
    3. **Validate** — Verify structural safety
    4. **Execute** — Query database
    5. **Retry** — Auto-correct exceptions
    6. **Summarize** — Synthesize findings
    """)

    st.markdown("---")
    skip_summary = st.checkbox("Fast Mode (Skip Summary)", value=True, help="Omit the final analysis step to decrease response time.")
    dry_run = st.checkbox("Dry Run (Generate Only)", value=False, help="Construct the SQL query without executing it against the database.")
    
    st.markdown("---")
    if st.button("Clear History", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()


# ─────────────────────────────────────────────────────────────────────
# Main Chat Area
# ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="header-text">Data Query Interface</p>', unsafe_allow_html=True)
st.caption("Enter a plain text query to access and analyze the ClassicModels database.")

# Init chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        elif "data" in msg:
            render_response(msg["data"])
        else:
            st.markdown(msg.get("content", ""))

# Handle prefilled question from sidebar
prefill = st.session_state.pop("prefill", None)

# Chat input
user_input = st.chat_input("Ask a question about the database...", key="chat_input")
question = prefill or user_input

if question:
    # Add user message
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Run pipeline via API
    with st.chat_message("assistant"):
        with st.spinner("Processing query..."):
            result = call_api(question, skip_summary, dry_run)
        render_response(result)

    # Save assistant response
    st.session_state["messages"].append({
        "role": "assistant",
        "content": result.get("summary", ""),
        "data": result,
    })
    st.rerun()
