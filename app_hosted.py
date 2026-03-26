import streamlit as st
import os
import json
import datetime
from pathlib import Path

st.set_page_config(
    page_title="⚛️ Physics Chatbot",
    page_icon="⚛️",
    layout="centered"
)

# ── Load environment variables ─────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
HF_TOKEN     = os.getenv("HF_TOKEN")
HF_MODEL     = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-V3")

# ── Validate env vars ──────────────────────────────────────────
if not all([SUPABASE_URL, SUPABASE_KEY, HF_TOKEN]):
    st.error("❌ Missing environment variables. Check your .env file.")
    st.stop()

# ── Supabase client ────────────────────────────────────────────
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_authed_client():
    """Return a Supabase client authenticated with the current user's token."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    token = st.session_state.get("access_token")
    if token:
        client.auth.set_session(token, token)
    return client

# ── Session state defaults ─────────────────────────────────────
for key, default in {
    "user": None,
    "access_token": None,
    "messages": [],
    "pending_feedback": None,
    "backend_ready": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ══════════════════════════════════════════════════════════════
#  AUTH SCREEN
# ══════════════════════════════════════════════════════════════
def show_auth():
    st.title("⚛️ Physics Chatbot")
    st.caption("Class 10 · Class 11 · Class 12 · College Physics")
    st.divider()

    tab_login, tab_signup = st.tabs(["🔑 Sign In", "📝 Sign Up"])

    with tab_login:
        st.subheader("Welcome back!")
        email    = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sign In", use_container_width=True):
                if not email or not password:
                    st.error("Please enter email and password.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({
                            "email": email, "password": password
                        })
                        st.session_state.user = res.user
                        st.session_state.access_token = res.session.access_token
                        st.toast(f"✅ Welcome back!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Login failed: {e}")
        with col2:
            if st.button("Sign in with Google 🔵", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_oauth({
                        "provider": "google",
                        "options": {"redirect_to": os.getenv("REDIRECT_URL", "http://localhost:8501")}
                    })
                    st.markdown(f"[Click here to sign in with Google]({res.url})")
                except Exception as e:
                    st.error(f"❌ Google sign-in error: {e}")

    with tab_signup:
        st.subheader("Create your free account")
        name       = st.text_input("Your Name", key="signup_name")
        email_s    = st.text_input("Email", key="signup_email")
        password_s = st.text_input("Password (min 6 chars)", type="password", key="signup_password")
        password_c = st.text_input("Confirm Password", type="password", key="signup_confirm")

        if st.button("Create Account", use_container_width=True):
            if not all([name, email_s, password_s, password_c]):
                st.error("Please fill in all fields.")
            elif password_s != password_c:
                st.error("Passwords do not match.")
            elif len(password_s) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    res = supabase.auth.sign_up({
                        "email": email_s,
                        "password": password_s,
                        "options": {"data": {"full_name": name}}
                    })
                    if res.user:
                        st.success("✅ Account created! Check your email to confirm, then sign in.")
                except Exception as e:
                    st.error(f"❌ Sign up failed: {e}")

# ══════════════════════════════════════════════════════════════
#  DATABASE HELPERS
# ══════════════════════════════════════════════════════════════
def get_user_id():
    return st.session_state.user.id

def save_message(role, content, confidence=None):
    try:
        get_authed_client().table("messages").insert({
            "user_id":    get_user_id(),
            "role":       role,
            "content":    content,
            "confidence": confidence,
            "created_at": datetime.datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        st.warning(f"⚠️ Could not save message: {e}")

def load_past_conversations():
    try:
        res = get_authed_client().table("messages").select("*").eq("user_id", get_user_id()).order("created_at").execute()
        return res.data or []
    except:
        return []

def save_learned(question, answer):
    try:
        get_authed_client().table("learned_answers").upsert({
            "user_id":    get_user_id(),
            "question":   question,
            "answer":     answer,
            "created_at": datetime.datetime.utcnow().isoformat()
        }, on_conflict="user_id,question").execute()
    except Exception as e:
        st.warning(f"⚠️ Could not save: {e}")

def load_learned():
    try:
        res = get_authed_client().table("learned_answers").select("*").eq("user_id", get_user_id()).execute()
        return res.data or []
    except:
        return []

def delete_all_data():
    uid = get_user_id()
    try:
        get_authed_client().table("messages").delete().eq("user_id", uid).execute()
        get_authed_client().table("learned_answers").delete().eq("user_id", uid).execute()
    except Exception as e:
        st.error(f"❌ Could not delete: {e}")

# ══════════════════════════════════════════════════════════════
#  BACKEND LOADER
# ══════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_backend():
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.docstore.document import Document
    emb = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    vs = FAISS.load_local(
        "physics_index", emb,
        allow_dangerous_deserialization=True
    )
    return vs, Document

# ── HuggingFace InferenceClient (new router) ──────────────────
def ask_hf(question, history_text, vs, Document):
    from huggingface_hub import InferenceClient

    # Get relevant docs + confidence
    results = vs.similarity_search_with_score(question, k=4)
    if not results:
        return "I couldn't find anything relevant in my knowledge base.", "🔴 Very Low"

    docs    = [r[0] for r in results]
    score   = results[0][1]
    context = "\n\n".join([d.page_content for d in docs])

    if score < 0.3:   conf = "🟢 High"
    elif score < 0.6: conf = "🟡 Medium"
    elif score < 1.0: conf = "🟠 Low"
    else:             conf = "🔴 Very Low"

    system_msg = """You are an expert Science tutor covering Physics, Chemistry and Biology from all classes and College level.
Answer clearly with step-by-step explanations and formulas where needed.
If unsure, say so honestly."""

    user_msg = f"""Conversation so far:
{history_text if history_text else "(First question)"}

Relevant Physics Knowledge:
{context}

Question: {question}"""

    # Models confirmed working on HF free tier new router
    models_to_try = [
        "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "deepseek-ai/DeepSeek-V3",
    ]

    errors = []
    for model in models_to_try:
        try:
            # Each model needs its own base_url with model name embedded
            client = InferenceClient(
                base_url="https://router.huggingface.co/together/v1",
                api_key=HF_TOKEN,
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": user_msg}
                ],
                max_tokens=2000,
                temperature=0.3,
            )
            answer = response.choices[0].message.content.strip()
            if answer:
                return answer, conf
            else:
                errors.append(f"- {model}: empty response")
        except Exception as e:
            errors.append(f"- {model}: {str(e)[:120]}")
            continue

    error_detail = "\n".join(errors)
    st.error(f"""All AI models failed:\n\n{error_detail}\n\nFixes:\n- 401: get a new token at huggingface.co/settings/tokens\n- 403: visit the model page on HuggingFace and click Agree""")
    return "Could not get a response. See the red error box above.", "🔴 Error"


# ══════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════
def show_app():
    user_name = st.session_state.user.user_metadata.get(
        "full_name", st.session_state.user.email
    )

    # ── Load backend ───────────────────────────────────────────
    if not st.session_state.backend_ready:
        if not os.path.exists("./physics_index"):
            st.error("❌ physics_index not found! Run `python3 build_index.py` first.")
            st.stop()

        st.info("⏳ Loading knowledge base... (~30 seconds first time)")
        bar = st.progress(0, text="Starting...")
        try:
            bar.progress(20, text="Loading embeddings...")
            vs, Document = load_backend()
            bar.progress(60, text="Loading your learned answers...")

            learned = load_learned()
            if learned:
                docs = [Document(
                    page_content=f"Q: {e['question']}\nA: {e['answer']}",
                    metadata={"source": "user_learned"}
                ) for e in learned]
                vs.add_documents(docs)

            bar.progress(100, text="Ready!")
            st.session_state.vs       = vs
            st.session_state.Document = Document
            st.session_state.backend_ready = True
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error loading: {e}")
            st.stop()

    vs       = st.session_state.vs
    Document = st.session_state.Document

    # ── Sidebar ────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"### 👋 Hi, {user_name}!")
        st.caption(st.session_state.user.email)

        if st.button("🚪 Sign Out"):
            supabase.auth.sign_out()
            for k in ["user","access_token","messages","pending_feedback","backend_ready","vs","Document"]:
                st.session_state[k] = None if k in ["user","access_token"] else \
                                      [] if k=="messages" else \
                                      False if k=="backend_ready" else None
            st.rerun()

        st.divider()
        st.markdown("### 🧠 Your Learned Answers")
        learned = load_learned()
        if not learned:
            st.info("Nothing learned yet.")
        else:
            st.success(f"✅ {len(learned)} answers saved")
            for e in learned[-5:]:
                with st.expander(f"{e['question'][:40]}..."):
                    st.write(e["answer"][:200])

        st.divider()
        st.markdown("### 💬 Past Conversations")
        past = load_past_conversations()
        if not past:
            st.info("No history yet.")
        else:
            st.success(f"💬 {len(past)} messages saved")
            user_msgs = [p for p in past if p["role"] == "user"]
            for p in user_msgs[-5:]:
                with st.expander(f"📅 {p['created_at'][:10]}: {p['content'][:35]}..."):
                    st.write(p["content"])

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.pending_feedback = None
                st.rerun()
        with col2:
            if st.button("🗑️ All Data", use_container_width=True):
                delete_all_data()
                st.toast("All your data deleted.")
                st.rerun()

    # ── Main area ──────────────────────────────────────────────
    st.title("⚛️ Physics Chatbot")
    st.caption("Class 10 · Class 11 · Class 12 · College Physics")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and msg.get("confidence"):
                st.caption(f"📊 Confidence: {msg['confidence']}")

    # ── Feedback ───────────────────────────────────────────────
    if st.session_state.pending_feedback:
        pf = st.session_state.pending_feedback
        st.divider()
        st.markdown("**📝 Was this answer correct?**")
        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("✅ Yes — Save it"):
                vs.add_documents([Document(
                    page_content=f"Q: {pf['question']}\nA: {pf['answer']}",
                    metadata={"source": "user_learned"}
                )])
                save_learned(pf["question"], pf["answer"])
                st.session_state.pending_feedback = None
                st.toast("✅ Saved! I'll remember this for your future sessions.")
                st.rerun()
        with c2:
            if st.button("❌ Correct it"):
                st.session_state.pending_feedback["correcting"] = True
                st.rerun()
        with c3:
            if st.button("⏭️ Skip"):
                st.session_state.pending_feedback = None
                st.rerun()

        if pf.get("correcting"):
            correction = st.text_area("✏️ Type the correct answer:", height=100)
            if st.button("💾 Save Correction"):
                if correction.strip():
                    vs.add_documents([Document(
                        page_content=f"Q: {pf['question']}\nA: {correction.strip()}",
                        metadata={"source": "user_learned"}
                    )])
                    save_learned(pf["question"], correction.strip())
                    st.session_state.pending_feedback = None
                    st.toast("🧠 Correction saved permanently!")
                    st.rerun()

    # ── Chat input ─────────────────────────────────────────────
    question = st.chat_input("Ask a Physics question...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        save_message("user", question)

        with st.chat_message("user"):
            st.write(question)

        history_text = "\n".join([
            f"{'Student' if m['role']=='user' else 'Tutor'}: {m['content']}"
            for m in st.session_state.messages[-6:]
        ])

        with st.chat_message("assistant"):
            with st.spinner("🔁 Thinking + self-reviewing..."):
                answer, conf = ask_hf(question, history_text, vs, Document)
                st.write(answer)
                st.caption(f"📊 Confidence: {conf}")
                st.session_state.messages.append({
                    "role": "assistant", "content": answer, "confidence": conf
                })
                save_message("assistant", answer, conf)
                st.session_state.pending_feedback = {
                    "question": question, "answer": answer
                }
        st.rerun()

# ── Router ─────────────────────────────────────────────────────
if st.session_state.user is None:
    show_auth()
else:
    show_app()