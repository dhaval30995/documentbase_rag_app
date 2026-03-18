"""
Streamlit Frontend for RAG Chatbot.
Provides login, registration, PDF upload, chat interface, and session history.
"""

import requests
import streamlit as st

# ── Configuration ──────────────────────────────────────────────────────────
API_BASE_URL = "http://localhost:8000"

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        margin: 0.5rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #E3F2FD;
        border-left: 4px solid #1E88E5;
        color: #0D47A1;
        margin: 0.5rem 0;
    }
    .stChatMessage {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ──────────────────────────────────────────
def init_session_state() -> None:
    """Initialize all session state variables."""
    defaults = {
        "token": None,
        "user_id": None,
        "username": None,
        "current_session_id": None,
        "messages": [],
        "page": "login",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ── API Helper Functions ──────────────────────────────────────────────────
def get_auth_headers() -> dict:
    """Return authorization headers with JWT token."""
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_register(username: str, email: str, password: str) -> dict:
    """Call the /auth/register endpoint."""
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": username, "email": email, "password": password},
        timeout=30,
    )
    return response.json() if response.status_code in (200, 201) else {"error": response.json().get("detail", "Registration failed")}


def api_login(username: str, password: str) -> dict:
    """Call the /auth/login endpoint."""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    return response.json() if response.status_code == 200 else {"error": response.json().get("detail", "Login failed")}


def api_upload_pdf(file) -> dict:
    """Call the /documents/upload_pdf endpoint."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/documents/upload_pdf",
            headers=get_auth_headers(),
            files={"file": (file.name, file.getvalue(), "application/pdf")},
            timeout=600,
        )
        return response.json() if response.status_code in (200, 201) else {"error": response.json().get("detail", "Upload failed")}
    except requests.exceptions.RequestException as e:
        return {"error": f"Upload failed or timed out. Please try a smaller PDF. Error details: {str(e)}"}


def api_get_documents() -> list:
    """Call the /documents endpoint."""
    response = requests.get(
        f"{API_BASE_URL}/documents/",
        headers=get_auth_headers(),
        timeout=30,
    )
    return response.json().get("documents", []) if response.status_code == 200 else []


def api_chat(question: str, session_id: str = None):
    """Call the /chat endpoint and yield streaming text."""
    payload = {"question": question}
    if session_id:
        payload["session_id"] = session_id
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            headers=get_auth_headers(),
            json=payload,
            timeout=120,
            stream=True,
        )
        if response.status_code != 200:
            yield {"error": response.json().get("detail", "Chat failed")}
            return
            
        # Retrieve headers that contain session and sources
        new_session_id = response.headers.get("X-Session-ID")
        # Ensure the session state is updated immediately before the stream finishes
        if new_session_id:
            st.session_state.current_session_id = new_session_id
            
        sources_str = response.headers.get("X-Sources", "[]")
        import json
        try:
            sources = json.loads(sources_str)
        except Exception:
            sources = []

        # Yield chunks
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                yield chunk
                
        # After stream finishes, you could yield the sources as a final dictionary, 
        # but Streamlit's `st.write_stream` expects strings. So we handle sources separately
        # or append them as a string at the very end.
        
    except requests.exceptions.RequestException as e:
        yield f"❌ Connection Error: {str(e)}"


def api_get_sessions() -> list:
    """Call the /sessions endpoint."""
    response = requests.get(
        f"{API_BASE_URL}/sessions",
        headers=get_auth_headers(),
        timeout=30,
    )
    return response.json() if response.status_code == 200 else []


def api_get_messages(session_id: str) -> list:
    """Call the /sessions/messages/{session_id} endpoint."""
    response = requests.get(
        f"{API_BASE_URL}/sessions/messages/{session_id}",
        headers=get_auth_headers(),
        timeout=30,
    )
    return response.json() if response.status_code == 200 else []


# ── Authentication Pages ──────────────────────────────────────────────────
def show_login_page() -> None:
    """Display the login form."""
    st.markdown('<div class="main-header">🤖 RAG Chatbot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Chat with your PDF documents using AI</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 Login")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    with st.spinner("Logging in..."):
                        result = api_login(username, password)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state.token = result["access_token"]
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.session_state.page = "chat"
                        st.rerun()

        st.divider()
        if st.button("Don't have an account? Register", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()


def show_register_page() -> None:
    """Display the registration form."""
    st.markdown('<div class="main-header">🤖 RAG Chatbot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Create a new account</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("📝 Register")
        with st.form("register_form"):
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Choose a password")
            password_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            submitted = st.form_submit_button("Register", use_container_width=True)

            if submitted:
                if not all([username, email, password, password_confirm]):
                    st.error("Please fill in all fields")
                elif password != password_confirm:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    with st.spinner("Creating account..."):
                        result = api_register(username, email, password)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state.token = result["access_token"]
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.session_state.page = "chat"
                        st.rerun()

        st.divider()
        if st.button("Already have an account? Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────
def show_sidebar() -> None:
    """Display the sidebar with user info, PDF upload, and session history."""
    with st.sidebar:
        # User info
        st.markdown(f"### 👤 {st.session_state.username}")
        st.divider()

        # PDF Upload section
        st.subheader("📄 Upload PDF")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload a PDF document to chat with",
        )
        if uploaded_file:
            if st.button("📤 Process PDF", use_container_width=True):
                with st.spinner(f"Processing '{uploaded_file.name}'..."):
                    result = api_upload_pdf(uploaded_file)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(f"✅ {result['message']} ({result['chunks_created']} chunks)")

        st.caption("Available Documents:")
        docs = api_get_documents()
        if docs:
            with st.expander("📂 Your Uploaded PDFs", expanded=True):
                for doc in docs:
                    st.text(f"📄 {doc}")
        else:
            st.caption("No PDFs uploaded yet.")

        st.divider()

        # Session History
        st.subheader("💬 Chat History")
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.current_session_id = None
            st.session_state.messages = []
            st.rerun()

        # Load sessions
        sessions = api_get_sessions()
        if sessions:
            for session in sessions:
                session_title = session.get("title", "Untitled")
                if len(session_title) > 35:
                    session_title = session_title[:35] + "…"
                msg_count = session.get("message_count", 0)
                btn_label = f"💬 {session_title} ({msg_count})"
                if st.button(btn_label, key=f"session_{session['id']}", use_container_width=True):
                    load_session(session["id"])
        else:
            st.caption("No chat sessions yet")

        st.divider()

        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def load_session(session_id: str) -> None:
    """Load a previous chat session and its messages."""
    st.session_state.current_session_id = session_id
    messages = api_get_messages(session_id)
    st.session_state.messages = []
    for msg in messages:
        st.session_state.messages.append({"role": "user", "content": msg["user_message"]})
        st.session_state.messages.append({"role": "assistant", "content": msg["assistant_response"]})
    st.rerun()


# ── Main Chat Interface ──────────────────────────────────────────────────
def show_chat_page() -> None:
    """Display the main chat interface."""
    show_sidebar()

    # Header
    st.markdown('<div class="main-header">🤖 RAG Chatbot</div>', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown(
            '<div class="info-box">'
            "👋 Welcome! Upload a PDF in the sidebar, then ask questions about it here."
            "</div>",
            unsafe_allow_html=True,
        )

    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            # We use st.write_stream to render the generator
            generator = api_chat(
                question=prompt,
                session_id=st.session_state.current_session_id,
            )
            
            # Since api_chat updates st.session_state.current_session_id automatically
            # we just stream the text.
            response_text = st.write_stream(generator)
            
            # If the response generator caught an error, response_text might be a dictionary
            if isinstance(response_text, dict) and "error" in response_text:
                st.error(response_text["error"])
                response_text = f"❌ {response_text['error']}"

            # Save full response to local session history
            st.session_state.messages.append({"role": "assistant", "content": response_text})


# ── Main App Router ───────────────────────────────────────────────────────
def main() -> None:
    """Main application entry point — routes to the appropriate page."""
    if st.session_state.token:
        show_chat_page()
    elif st.session_state.page == "register":
        show_register_page()
    else:
        show_login_page()


if __name__ == "__main__":
    main()
