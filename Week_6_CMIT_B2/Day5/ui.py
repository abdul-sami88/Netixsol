import streamlit as st
import requests
import uuid
from datetime import datetime


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AFL Assistant",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

/* ---------- APP ---------- */

.stApp {
    background-color: #0b1117;
}

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 5rem;
}


/* ---------- SIDEBAR ---------- */

section[data-testid="stSidebar"] {
    background-color: #0d151d;
    border-right: 1px solid #202c36;
}

section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: white;
}


/* ---------- HEADER ---------- */

.header-box {
    background: linear-gradient(
        135deg,
        #123f35,
        #102d40
    );

    border: 1px solid #245247;
    border-radius: 18px;

    padding: 28px 32px;

    margin-bottom: 28px;
}

.header-title {
    font-size: 34px;
    font-weight: 750;
    color: white;
}

.header-subtitle {
    color: #aebbc5;
    font-size: 15px;
    margin-top: 5px;
}

.status {
    display: inline-block;

    margin-top: 15px;

    padding: 5px 12px;

    border-radius: 20px;

    background-color: #173c33;
    border: 1px solid #2c6657;

    color: #65d8ac;

    font-size: 12px;
    font-weight: 600;
}


/* ---------- SECTION HEADINGS ---------- */

.section-title {
    font-size: 20px;
    font-weight: 700;
    color: white;

    margin-bottom: 14px;
}


/* ---------- INFO CARDS ---------- */

.info-card {
    background-color: #111a23;

    border: 1px solid #22303b;

    border-radius: 14px;

    padding: 18px;

    margin-bottom: 12px;
}

.info-label {
    font-size: 11px;

    color: #7f8c98;

    text-transform: uppercase;

    letter-spacing: 0.08em;
}

.info-value {
    font-size: 21px;

    font-weight: 700;

    color: white;

    margin-top: 4px;
}


/* ---------- BUTTONS ---------- */

.stButton > button {
    border-radius: 10px;
    min-height: 42px;
}


/* ---------- CHAT INPUT ---------- */

.stChatInput {
    padding-bottom: 1rem;
}


/* ---------- DIVIDER ---------- */

hr {
    border-color: #202c36 !important;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🏈 AFL Assistant")

    st.caption("Domain-scoped AFL AI assistant")

    st.divider()

    st.markdown("### ⚙️ API Configuration")

    api_url = st.text_input(
        "API URL",
        value="http://localhost:8000",
    )

    st.divider()

    st.markdown("### 💡 Example Questions")

    examples = [
        "Will Melbourne beat Richmond this week?",
        "Who will top-score for Geelong?",
        "What's the Brownlow Medal?",
        "How many disposals did West Coast average?",
        "Tell me about the Grand Final.",
    ]

    for i, example in enumerate(examples):

        if st.button(
            example,
            key=f"example_{i}",
            use_container_width=True,
        ):

            st.session_state.pending_question = example
            st.rerun()

    st.divider()

    if st.button(
        "🔄 New Conversation",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.conversation_id = str(uuid.uuid4())

        if "pending_question" in st.session_state:
            del st.session_state.pending_question

        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="header-box">
        <div class="header-title">
            🏈 AFL Assistant
        </div>

        <div class="header-subtitle">
            Your AI assistant for AFL statistics,
            matches, players, teams and predictions.
        </div>

        <div class="status">
            ● Assistant Online
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# MAIN LAYOUT
# ============================================================

chat_col, info_col = st.columns(
    [3.2, 1],
    gap="large",
)


# ============================================================
# CHAT AREA
# ============================================================

with chat_col:

    st.markdown(
        '<div class="section-title">💬 Conversation</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # WELCOME
    # --------------------------------------------------------

    if not st.session_state.messages:

        st.info(
            "👋 Welcome! Ask me anything about AFL."
        )

        st.markdown("**Try one of these:**")

        col1, col2, col3 = st.columns(3)

        with col1:

            if st.button(
                "🏆 Match Prediction",
                use_container_width=True,
            ):
                st.session_state.pending_question = (
                    "Will Melbourne beat Richmond this week?"
                )
                st.rerun()

        with col2:

            if st.button(
                "📊 Player Statistics",
                use_container_width=True,
            ):
                st.session_state.pending_question = (
                    "Who will top-score for Geelong?"
                )
                st.rerun()

        with col3:

            if st.button(
                "📚 AFL Knowledge",
                use_container_width=True,
            ):
                st.session_state.pending_question = (
                    "What's the Brownlow Medal?"
                )
                st.rerun()


    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    for message in st.session_state.messages:

        if message["role"] == "user":

            with st.chat_message(
                "user",
                avatar="👤",
            ):

                st.markdown(message["content"])

        else:

            with st.chat_message(
                "assistant",
                avatar="🏈",
            ):

                st.markdown(message["content"])

                metadata = message.get(
                    "metadata"
                )

                if metadata:

                    with st.expander(
                        "📊 Response details"
                    ):

                        if metadata.get("intent"):

                            st.write(
                                "**Intent:**",
                                metadata["intent"],
                            )

                        if metadata.get("confidence") is not None:

                            st.write(
                                "**Confidence:**",
                                f"{metadata['confidence']:.0%}",
                            )

                        if metadata.get("latency_ms"):

                            st.write(
                                "**Response time:**",
                                f"{metadata['latency_ms']} ms",
                            )

                        if metadata.get("tools"):

                            st.write(
                                "**Tools:**",
                                ", ".join(
                                    metadata["tools"]
                                ),
                            )


# ============================================================
# CHAT INPUT
# ============================================================

# Enter = Send
# Shift + Enter = New Line

pending = st.session_state.get(
    "pending_question",
    None,
)

if pending:

    # We can't programmatically insert into
    # st.chat_input, so show it as a small hint.
    st.caption(f"Selected: **{pending}**")


question = st.chat_input(
    "Ask about AFL...  (Enter to send)",
)


# ============================================================
# EXAMPLE QUESTION HANDLING
# ============================================================

if pending and not question:

    question = pending

    del st.session_state.pending_question


# ============================================================
# SEND TO API
# ============================================================

if question:

    question = question.strip()

    if question:

        # Add user message
        st.session_state.messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        # ----------------------------------------------------
        # API REQUEST
        # ----------------------------------------------------

        with st.spinner(
            "🏈 AFL Assistant is thinking..."
        ):

            try:

                response = requests.post(
                    f"{api_url.rstrip('/')}/chat",

                    json={
                        "message": question,
                        "conversation_id":
                            st.session_state.conversation_id,
                    },

                    timeout=30,
                )


                # ============================================
                # SUCCESS
                # ============================================

                if response.status_code == 200:

                    data = response.json()

                    tools_called = data.get(
                        "tools_called",
                        [],
                    )

                    tool_names = []

                    for tool in tools_called:

                        if isinstance(
                            tool,
                            dict,
                        ):

                            name = tool.get(
                                "name"
                            )

                            if name:
                                tool_names.append(
                                    name
                                )

                        elif isinstance(
                            tool,
                            str,
                        ):

                            tool_names.append(
                                tool
                            )


                    confidence = data.get(
                        "confidence"
                    )

                    latency = data.get(
                        "latency_sec",
                        0,
                    )


                    metadata = {
                        "intent":
                            data.get("intent"),

                        "confidence":
                            confidence,

                        "latency_ms":
                            int(latency * 1000),

                        "tools":
                            tool_names,
                    }


                    st.session_state.messages.append(
                        {
                            "role": "assistant",

                            "content":
                                data.get(
                                    "response",
                                    "No response received.",
                                ),

                            "metadata":
                                metadata,
                        }
                    )


                # ============================================
                # API ERROR
                # ============================================

                else:

                    try:

                        error_data = response.json()

                        detail = error_data.get(
                            "detail",
                            "Unknown API error",
                        )

                    except Exception:

                        detail = response.text


                    st.session_state.messages.append(
                        {
                            "role": "assistant",

                            "content":
                                f"❌ **API Error "
                                f"{response.status_code}**\n\n"
                                f"{detail}",
                        }
                    )


            # ================================================
            # CONNECTION ERROR
            # ================================================

            except requests.exceptions.ConnectionError:

                st.session_state.messages.append(
                    {
                        "role": "assistant",

                        "content":
                            "❌ **Could not connect to the API.**\n\n"
                            f"Make sure your API is running at:\n"
                            f"`{api_url}`",
                    }
                )


            # ================================================
            # TIMEOUT
            # ================================================

            except requests.exceptions.Timeout:

                st.session_state.messages.append(
                    {
                        "role": "assistant",

                        "content":
                            "⏱️ **Request timed out.**\n\n"
                            "The API took too long to respond.",
                    }
                )


            # ================================================
            # OTHER ERROR
            # ================================================

            except Exception as e:

                st.session_state.messages.append(
                    {
                        "role": "assistant",

                        "content":
                            f"❌ **Unexpected error:**\n\n"
                            f"`{str(e)}`",
                    }
                )


        st.rerun()


# ============================================================
# RIGHT PANEL
# ============================================================

with info_col:

    st.markdown(
        '<div class="section-title">📊 Session</div>',
        unsafe_allow_html=True,
    )

    # Conversation ID

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-label">
                Conversation
            </div>

            <div class="info-value">
                #{st.session_state.conversation_id[:8]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    # Message count

    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-label">
                Messages
            </div>

            <div class="info-value">
                {len(st.session_state.messages)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # LAST RESPONSE
    # --------------------------------------------------------

    if (
        st.session_state.messages
        and
        st.session_state.messages[-1]["role"]
        == "assistant"
    ):

        metadata = st.session_state.messages[-1].get(
            "metadata",
            {},
        )

        st.markdown("### 🧠 Last Response")


        # Intent

        if metadata.get("intent"):

            st.markdown(
                f"""
                <div class="info-card">

                    <div class="info-label">
                        Intent
                    </div>

                    <div class="info-value">
                        {metadata["intent"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


        # Confidence

        confidence = metadata.get(
            "confidence"
        )

        if confidence is not None:

            st.markdown("**Confidence**")

            st.progress(
                max(
                    0.0,
                    min(
                        1.0,
                        float(confidence),
                    ),
                )
            )

            st.caption(
                f"{confidence:.0%}"
            )


        # Latency

        latency = metadata.get(
            "latency_ms"
        )

        if latency:

            st.metric(
                "Response time",
                f"{latency} ms",
            )


        # Tools

        tools = metadata.get(
            "tools",
            [],
        )

        if tools:

            st.markdown("**🔧 Tools used**")

            for tool in tools:

                st.code(
                    tool,
                    language=None,
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🏈 AFL Assistant v1.0  •  "
    "Domain-Scoped AI  •  "
    f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
)