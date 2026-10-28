"""
Streamlit demo UI for the restaurant-ai-agent backend.

Run from the project root:
    streamlit run frontend/app.py

Environment variables:
    BACKEND_URL          Base URL of the FastAPI app (default http://localhost:8001)
    TABLE_POLL_SECONDS   How often the floor map checks the DB for changes
                         (default 5; set to 0 to poll only via the Refresh button)
    CHAT_HEIGHT          Chat panel height in px (default 520); longer
                         conversations scroll inside the panel
    MAP_HEIGHT           Floor map panel height in px (default 520)
"""

import base64
import concurrent.futures
import os
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001").rstrip("/")
POLL_SECONDS = float(os.getenv("TABLE_POLL_SECONDS", "5"))
# Fixed pixel heights of the chat and floor-map panels; content taller than
# this scrolls inside the panel. Tune to your screen (or set CHAT_HEIGHT /
# MAP_HEIGHT in the environment).
CHAT_HEIGHT = int(os.getenv("CHAT_HEIGHT", "520"))
MAP_HEIGHT = int(os.getenv("MAP_HEIGHT", "520"))

# Project root — PDFs placed there show up in the sidebar. In Docker the
# whole project is copied to /app inside the image; override with PDF_ROOT
# (e.g. a mounted volume) if your restaurant-info PDF lives elsewhere.
ROOT = Path(os.getenv("PDF_ROOT", Path(__file__).resolve().parent.parent))
IGNORED_DIRS = {".venv", ".git", "__pycache__", "node_modules"}
MAX_EMBED_BYTES = 10 * 1024 * 1024  # skip inlining giant PDFs

st.set_page_config(page_title="Restaurant AI Demo", page_icon="🍽️", layout="wide")

# --- Table card styling (inserted once, at the top level of the script)
# Chat and floor map use fixed-height scrollable containers (CHAT_HEIGHT /
# MAP_HEIGHT below); no page-level layout hacks.
st.markdown(
    """
    <style>
        .tgrid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 10px;
            margin: 4px 0 8px 0;
        }
        .tcard {
            border-radius: 10px;
            padding: 10px 12px;
            border: 1px solid rgba(0, 0, 0, 0.08);
            color: #1f2937;
        }
        .tcard.free {
            background: #ecf9f1;
            border-color: #56b877;
        }
        .tcard.reserved {
            background: #fdecea;
            border-color: #e08a83;
        }
        .tname { font-weight: 700; font-size: 0.95rem; }
        .tcap  { font-size: 0.8rem; opacity: 0.75; margin-top: 2px; }
        .tstate { font-size: 0.8rem; margin-top: 6px; font-weight: 600; }
        .tlegend { font-size: 0.85rem; opacity: 0.8; margin-top: 2px; }
        /* Thinking bubble inside the chat panel */
        .tspin {
            display: inline-block;
            width: 12px;
            height: 12px;
            margin-right: 6px;
            border: 2px solid currentColor;
            border-top-color: transparent;
            border-radius: 50%;
            opacity: 0.7;
            vertical-align: -2px;
            animation: tspin-rotate 0.8s linear infinite;
        }
        @keyframes tspin-rotate { to { transform: rotate(360deg); } }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Session state
st.session_state.setdefault(
    "messages",
    [{"role": "assistant", "content": "Hi! 👋 I'm you Restaurant AI Assistant, I can help you about the restaurant — menu, hours, policies — or book a table."}],
)
st.session_state.setdefault("session_id", None)


def fetch_version():
    """Cheap DB-change fingerprint: (count, last_updated)."""
    r = requests.get(f"{BACKEND_URL}/tables/version", timeout=5)
    r.raise_for_status()
    data = r.json()
    return (data.get("count"), data.get("last_updated"))


def fetch_tables():
    r = requests.get(f"{BACKEND_URL}/tables/", timeout=5)
    r.raise_for_status()
    return r.json()


def backend_health():
    """True if the FastAPI backend answers /health."""
    try:
        return requests.get(f"{BACKEND_URL}/health", timeout=3).ok
    except requests.RequestException:
        return False


# --- Background agent calls -------------------------------------------------
# The chat panel shows an in-box "Thinking…" bubble while the LLM works, so the
# request must not block the script. The worker below runs in a thread and only
# returns data; all Streamlit state stays on the script thread.
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="agent")
THINKING_HTML = '<div><span class="tspin"></span>Thinking…</div>'


def _call_agent(prompt: str, session_id: str | None):
    """Worker thread body: POST /run-agent. Returns (reply, session_id)."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/run-agent",
            json={"query": prompt, "session_id": session_id},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return (data.get("message") or "*(empty reply)*", data.get("session_id"))
    except requests.RequestException as e:
        return (f"⚠️ Could not reach the backend at `{BACKEND_URL}`: {e.__class__.__name__}", None)
    except Exception as e:  # malformed payloads etc.
        return (f"⚠️ Unexpected error: {e.__class__.__name__}: {e}", None)


def launch_agent(prompt: str):
    """Kick off a background request and show the in-box Thinking… bubble."""
    st.session_state["_future"] = _executor.submit(
        _call_agent, prompt, st.session_state["session_id"]
    )
    st.session_state["messages"].append({"role": "assistant", "content": THINKING_HTML})
    st.session_state["_pending_idx"] = len(st.session_state["messages"]) - 1


@st.fragment(run_every=1)
def poll_reply():
    """Promotes the Thinking… bubble to the real reply once the worker is done."""
    future = st.session_state.get("_future")
    if future is None or not future.done():
        return

    reply, session_id = future.result()
    if session_id:
        st.session_state["session_id"] = session_id
    st.session_state["messages"][st.session_state["_pending_idx"]]["content"] = reply
    st.session_state["_future"] = None
    st.session_state["_pending_idx"] = None

    inbox = st.session_state.get("_inbox")
    if inbox:
        launch_agent(inbox.pop(0))

    st.rerun(scope="app")


# -------------------------------
# Sidebar: health + document panel
# -------------------------------
sidebar = st.sidebar
sidebar.title("🍽️ Restaurant AI Demo")

healthy = backend_health()
if healthy:
    sidebar.markdown("🟢 **Backend connected** — `BACKEND_URL` = " + f"`{BACKEND_URL}`")
else:
    sidebar.markdown(f"🔴 **Backend offline** — is `{BACKEND_URL}` reachable?")
sidebar.divider()

sidebar.header("📄 Restaurant info document")
sidebar.caption("The source the assistant fetches for FAQ answers.")

pdf_paths = sorted(
    p for p in ROOT.rglob("*.pdf")
    if not (IGNORED_DIRS & set(p.relative_to(ROOT).parts))
)

if not pdf_paths:
    sidebar.info("No PDF found. Drop your restaurant info PDF in the project root, then refresh this page.")
else:
    labels = {str(p.relative_to(ROOT)): p for p in pdf_paths}
    label = sidebar.radio(
        "Document",
        list(labels.keys()),
        label_visibility="collapsed",
    )
    pdf_path = labels[label]
    size_kb = pdf_path.stat().st_size / 1024
    sidebar.caption(f"**{label}** — {size_kb:.0f} KB")

    if sidebar.button("⬇️ Download / open PDF"):
        sidebar.download_button(
            label="Save it",
            data=pdf_path.read_bytes(),
            file_name=pdf_path.name,
            mime="application/pdf",
        )
        st.toast(f"Downloading {pdf_path.name}")

    if pdf_path.stat().st_size <= MAX_EMBED_BYTES:
        with sidebar.expander("👁 Preview document", expanded=False):
            data_uri = "data:application/pdf;base64," + base64.b64encode(
                pdf_path.read_bytes()
            ).decode("ascii")
            st.components.v1.iframe(
                data_uri,
                height=480,
                scrolling=True,
            )
    else:
        sidebar.caption("File is too large to preview inline — use the download button.")

sidebar.divider()
sidebar.caption(f"LangGraph session: `{st.session_state['session_id'] or '—'}`")
sidebar.caption(f"Floor map polls every {POLL_SECONDS:.0f}s" if POLL_SECONDS > 0 else "Floor map polls on demand")

# -------------------------------
# Main area: chat + floor map
# -------------------------------
col_chat, col_map = st.columns([1.15, 1])

# --- Chat column
with col_chat:
    st.subheader("💬 Chat")
    # Messages live in a fixed-height scrollable container (CHAT_HEIGHT);
    # new chat messages auto-scroll into view. The input sits right below it.
    # Assistant messages may contain HTML (animated Thinking… bubble), so they
    # render with unsafe_allow_html; user messages render plain markdown.
    with st.container(key="chat_history", height=CHAT_HEIGHT):
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    st.markdown(msg["content"], unsafe_allow_html=True)
                else:
                    st.markdown(msg["content"])

    prompt = st.chat_input("Ask me ...", disabled=st.session_state.get("_future") is not None)
    if prompt:
        st.session_state["messages"].append({"role": "user", "content": prompt})
        if st.session_state.get("_future"):  # one already in flight → queue it
            st.session_state.setdefault("_inbox", []).append(prompt)
        else:
            launch_agent(prompt)
        st.rerun()

# Promotes in-box Thinking… bubbles to real replies when the worker finishes
poll_reply()


# --- Floor map column (auto-refreshes when the DB actually changes)
@st.fragment(run_every=(POLL_SECONDS if POLL_SECONDS > 0 else None))
def floor_map():
    top_bar = st.columns([3, 1])
    top_bar[0].subheader("🪑 Table availability")
    if top_bar[1].button("🔄 Refresh"):
        st.session_state["_map_version"] = None  # force a full fetch

    # Map content is its own fixed-height scrollable container (MAP_HEIGHT)
    with st.container(key="floor_map", height=MAP_HEIGHT):
        try:
            fingerprint = fetch_version()
            if fingerprint != st.session_state.get("_map_version") or "_tables" not in st.session_state:
                st.session_state["_tables"] = fetch_tables()
                st.session_state["_map_version"] = fingerprint
        except requests.RequestException as e:
            if "_tables" not in st.session_state:
                st.error(f"Cannot reach backend at `{BACKEND_URL}`: {e.__class__.__name__}")
                return
            st.caption(f"⚠️ Showing the last known snapshot (could not reach backend: {e.__class__.__name__})")

        tables = sorted(
            st.session_state.get("_tables", []),
            key=lambda t: t.get("table_number", 0),
        )
        if not tables:
            st.info("No tables in the database yet.")
            return

        cards = []
        for t in tables:
            reserved = bool(t.get("is_reserved"))
            reserved_date = t.get("reserved_date") or ""
            state = f"⛔ Reserved · {reserved_date}" if reserved else "✅ Available"
            cards.append(
                f"<div class='tcard {'reserved' if reserved else 'free'}'>"
                f"<div class='tname'>Table {t['table_number']}</div>"
                f"<div class='tcap'>👥 {t['capacity']} seats</div>"
                f"<div class='tstate'>{state}</div>"
                "</div>"
            )

        updated = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"<div class='tgrid'>{''.join(cards)}</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='tlegend'>🟩 Available &nbsp;·&nbsp; 🟥 Reserved &nbsp;·&nbsp; "
            f"<small>updated {updated}</small></div>",
            unsafe_allow_html=True,
        )


with col_map:
    floor_map()
