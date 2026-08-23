"""
ui.py — AFL Assistant Streamlit UI
====================================

Chat interface for the AFL assistant.

Usage:
    streamlit run ui.py

FIXED (vs. the earlier version):
- Enter now sends the message. `st.text_area` + a separate Send button
  never submits on Enter (Enter just inserts a newline in a text area).
  Switched to `st.chat_input`, the widget Streamlit specifically built for
  chat-style "type and press Enter" input.
- The input box now actually clears after sending. The old code tried to
  reset it by setting `st.session_state.user_input = ""`, but the
  `text_area`'s real displayed value lives in `st.session_state["input_area"]`
  (bound automatically via its `key=`), which that line never touched --
  a classic Streamlit gotcha. `st.chat_input` clears itself automatically
  on submit, so there's nothing to manually manage.
"""

import streamlit as st
import requests
import uuid
from datetime import datetime

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="AFL Assistant",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("🏈 AFL Assistant")
st.markdown("**Ask me about AFL matches, predictions, statistics, and more.**")

# ============================================================================
# SESSION STATE
# ============================================================================

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# ============================================================================
# SIDEBAR CONFIG
# ============================================================================

with st.sidebar:
    st.header("Settings")
    api_url = st.text_input(
        "API URL",
        value="http://localhost:8000",
        help="Base URL of the AFL Assistant API",
    )

    st.divider()
    st.markdown("### Examples")
    st.caption("Click to ask immediately.")
    examples = [
        "Will Melbourne beat Richmond this week?",
        "Who will top-score for Geelong?",
        "What's the Brownlow Medal?",
        "How many disposals did West Coast average this season?",
        "Tell me about the Grand Final.",
    ]
    for ex in examples:
        # Example buttons queue the query the same way a typed-and-submitted
        # chat_input message would, rather than trying to pre-fill a text
        # box (st.chat_input can't be pre-filled -- it's designed to be
        # typed into directly). Clicking immediately asks the question,
        # which is actually better for a live demo than "fill box, then
        # still have to click Send".
        if st.button(ex, key=ex, use_container_width=True):
            st.session_state.pending_query = ex

    st.divider()
    if st.button("New Chat 🔄", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.pending_query = None
        st.rerun()

# ============================================================================
# SEND LOGIC (shared by chat_input submissions and example-button clicks)
# ============================================================================

def send_message(user_input: str) -> None:
    user_input = user_input.strip()
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})

    try:
        response = requests.post(
            f"{api_url}/chat",
            json={
                "message": user_input,
                "conversation_id": st.session_state.conversation_id,
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            st.session_state.messages.append({
                "role": "assistant",
                "content": data["response"],
                "metadata": {
                    "intent": data.get("intent"),
                    "confidence": data.get("confidence"),
                    "latency_ms": int(data.get("latency_sec", 0) * 1000),
                    "tools": [t["name"] for t in data.get("tools_called", [])],
                },
            })
        else:
            try:
                detail = response.json().get("detail", "Unknown error")
            except Exception:
                detail = response.text[:200]
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ API Error ({response.status_code}): {detail}",
            })

    except requests.exceptions.ConnectionError:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Could not connect to API at {api_url}. "
                       f"Make sure the API is running: `python api.py`",
        })
    except requests.exceptions.Timeout:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "❌ The request timed out. The assistant took too long to respond -- try again.",
        })
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Unexpected error: {e}",
        })


# Process a query queued by an example button (see sidebar above)
if st.session_state.pending_query:
    q = st.session_state.pending_query
    st.session_state.pending_query = None
    with st.spinner("Thinking..."):
        send_message(q)

# ============================================================================
# CHAT DISPLAY + INPUT
# ============================================================================

col1, col2 = st.columns([0.7, 0.3])

with col1:
    st.markdown("### Conversation")

    chat_container = st.container(height=450, border=True)
    with chat_container:
        for msg in st.session_state.messages:
            avatar = "🧑" if msg["role"] == "user" else "🏈"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                if msg.get("metadata"):
                    with st.expander("📊 Details"):
                        st.json(msg["metadata"])

    # st.chat_input: Enter (or the built-in send arrow) submits, and the
    # box clears itself automatically afterwards -- no manual state
    # management needed, which is exactly what was broken before.
    typed = st.chat_input("Ask about a match, a prediction, or a stat...")
    if typed:
        with st.spinner("Thinking..."):
            send_message(typed)
        st.rerun()

# ============================================================================
# RIGHT SIDEBAR: STATS
# ============================================================================

with col2:
    st.markdown("### Chat Info")
    st.metric("Conversation ID", st.session_state.conversation_id[:8])
    st.metric("Messages", len(st.session_state.messages))

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        metadata = st.session_state.messages[-1].get("metadata", {})

        st.divider()
        st.markdown("### Last Response")

        if metadata.get("intent"):
            st.write(f"**Intent:** `{metadata['intent']}`")
        if metadata.get("confidence") is not None:
            st.write(f"**Confidence:** {metadata['confidence']:.0%}")
        if metadata.get("latency_ms") is not None:
            st.write(f"**Latency:** {metadata['latency_ms']}ms")
        if metadata.get("tools"):
            st.write(f"**Tools:** {', '.join(metadata['tools']) or 'N/A'}")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption(f"AFL Assistant v1.0 | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
