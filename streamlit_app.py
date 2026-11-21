import os
import random
import time

import streamlit as st

st.set_page_config(page_title="AI Chat", page_icon="✺", layout="centered")

MODELS = {
    "Gemini 3.8 Flash": "gemini-3.8-flash",
    "Gemini 3.5 Flash-Lite": "gemini-3.5-flash-lite",
}
STARTERS = [
    ("✦ Explain", "Explain how GitHub pull requests work, simply."),
    ("✎ Write", "Write a short poem about a cozy terminal at midnight."),
    ("⌘ Code", "Show me a Python one-liner to count words in a file."),
    ("☼ Ideas", "Give me 5 fun weekend project ideas for a Streamlit app."),
]

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500&display=swap');
html, body, [class*="css"], .stMarkdown, p { font-family: 'Inter', sans-serif; }
h1, .hero { font-family: 'Fraunces', serif !important; }
.stApp {
  background:
    radial-gradient(900px 500px at 15% -10%, rgba(217,119,87,.22), transparent 60%),
    radial-gradient(700px 500px at 100% 10%, rgba(204,120,92,.12), transparent 55%),
    #1A1714;
}
#MainMenu, footer, header { visibility: hidden; }
.hero { text-align:center; margin: 2.5rem 0 .5rem; }
.hero .spark { font-size: 3rem; color:#D97757; display:inline-block;
  animation: spin 14s linear infinite; text-shadow: 0 0 30px rgba(217,119,87,.7); }
.hero h1 { font-size: 2.6rem; font-weight: 600; margin: .2rem 0; letter-spacing:-.02em; }
.hero p { color:#A89B8F; margin:0 0 1.5rem; }
@keyframes spin { to { transform: rotate(360deg); } }
[data-testid="stChatMessage"] {
  background: rgba(38,33,29,.7); border: 1px solid rgba(243,236,228,.07);
  border-radius: 18px; padding: 1rem 1.2rem; backdrop-filter: blur(8px);
  animation: rise .35s ease both;
}
@keyframes rise { from { opacity:0; transform: translateY(8px);} to {opacity:1; transform:none;} }
[data-testid="stChatInput"] { border-radius: 22px; border: 1px solid rgba(217,119,87,.4);
  box-shadow: 0 0 40px rgba(217,119,87,.12); }
.stButton > button { border-radius: 999px; border:1px solid rgba(217,119,87,.35);
  background: rgba(217,119,87,.08); color:#F3ECE4; transition: all .2s; }
.stButton > button:hover { background:#D97757; color:#1A1714; transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(217,119,87,.35); border-color:#D97757; }
section[data-testid="stSidebar"] { background:#15120F; border-right:1px solid rgba(243,236,228,.06); }
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### ✺ AI Chat")
    model_name = st.selectbox("Model", list(MODELS))
    system = st.text_area("System prompt", "You are a warm, concise assistant.", height=100)
    default_key = os.environ.get("GEMINI_API_KEY", "")
    try:
        default_key = default_key or st.secrets.get("GEMINI_API_KEY", "")
    except Exception:  # noqa: BLE001
        pass
    api_key = st.text_input(
        "Gemini API key",
        value=default_key,
        type="password",
        help="Leave empty for demo mode.",
    )
    if st.button("New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption("Demo mode is on" if not api_key else "Connected ✓")

st.session_state.setdefault("messages", [])
messages = st.session_state.messages

pending = st.session_state.pop("pending", None)
if not messages and not pending:
    st.markdown(
        '<div class="hero"><div class="spark">✺</div><h1>How can I help today?</h1>'
        "<p>Ask anything. Pick a starter or type below.</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, (label, prompt) in enumerate(STARTERS):
        if cols[i % 2].button(label, key=f"s{i}", use_container_width=True):
            st.session_state.pending = prompt
            st.rerun()

for m in messages:
    with st.chat_message(m["role"], avatar=":material/flare:" if m["role"] == "assistant" else None):
        st.markdown(m["content"])


def demo_stream(prompt):
    text = (
        f"*(demo mode — add an API key in the sidebar for real answers)*\n\n"
        f"You asked: **{prompt}**\n\nHere's where my real answer would stream in, "
        f"token by token, in this warm little corner of the terminal. "
        f"{random.choice(['✺', '✦', '☼'])}"
    )
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.03)


def real_stream(history):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in history
    ]
    stream = client.models.generate_content_stream(
        model=MODELS[model_name],
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=1500),
    )
    for chunk in stream:
        if chunk.text:
            yield chunk.text


prompt = st.chat_input("Message…") or pending
if prompt:
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar=":material/flare:"):
        try:
            gen = real_stream(messages) if api_key else demo_stream(prompt)
            reply = st.write_stream(gen)
        except Exception as e:  # noqa: BLE001
            reply = f"⚠️ {e}"
            st.error(reply)
    messages.append({"role": "assistant", "content": reply})
