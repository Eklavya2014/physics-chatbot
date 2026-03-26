import streamlit as st
import os
import json
import datetime
from pathlib import Path

st.set_page_config(page_title="⚛️ Physics Chatbot", page_icon="⚛️", layout="centered")

# ── iCloud path setup ──────────────────────────────────────────
ICLOUD_PATH = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "PhysicsChatbot"
ICLOUD_PATH.mkdir(parents=True, exist_ok=True)

CONVERSATIONS_FILE = ICLOUD_PATH / "conversations.json"
LEARNED_FILE       = ICLOUD_PATH / "learned.json"

# ── iCloud helpers ─────────────────────────────────────────────
def load_json(path):
    try:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        st.warning(f"⚠️ Could not save to iCloud: {e}")
        return False

def save_conversation(messages):
    """Append completed conversation to iCloud history file."""
    if not messages:
        return
    all_convos = load_json(CONVERSATIONS_FILE)
    all_convos.append({
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": messages
    })
    save_json(CONVERSATIONS_FILE, all_convos)

def load_learned():
    return load_json(LEARNED_FILE)

def save_learned(data):
    save_json(LEARNED_FILE, data)

def add_to_learned(question, answer):
    data = load_learned()
    # Avoid duplicates
    for entry in data:
        if entry["question"].strip().lower() == question.strip().lower():
            entry["answer"] = answer  # update if already exists
            save_learned(data)
            return
    data.append({"question": question, "answer": answer})
    save_learned(data)

# ── Page title ─────────────────────────────────────────────────
st.title("⚛️ Class 10–College Physics Chatbot")
st.caption(f"💾 Saving to iCloud: `{ICLOUD_PATH}`")

# ── Check requirements ─────────────────────────────────────────
if not os.path.exists("./physics_index"):
    st.error("❌ physics_index not found! Run `python3 build_index.py` first.")
    st.stop()

# ── Load backend (cached) ──────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_backend():
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.docstore.document import Document
    import ollama as ol

    emb = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    vs = FAISS.load_local(
        "physics_index", emb,
        allow_dangerous_deserialization=True
    )
    return vs, Document, ol

# ── Session state ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_feedback" not in st.session_state:
    st.session_state.pending_feedback = None
if "backend_ready" not in st.session_state:
    st.session_state.backend_ready = False
if "show_history" not in st.session_state:
    st.session_state.show_history = False

# ── Load backend with progress bar ────────────────────────────
if not st.session_state.backend_ready:
    st.info("⏳ Loading knowledge base... (first time takes ~30 seconds)")
    bar = st.progress(0, text="Starting...")
    try:
        bar.progress(10, text="Loading embeddings model...")
        from langchain_community.embeddings import HuggingFaceEmbeddings
        emb = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )
        bar.progress(50, text="Loading physics knowledge base...")
        from langchain_community.vectorstores import FAISS
        from langchain_community.docstore.document import Document
        vs = FAISS.load_local(
            "physics_index", emb,
            allow_dangerous_deserialization=True
        )

        # Inject all previously learned Q&As from iCloud into live vectorstore
        learned = load_learned()
        if learned:
            docs = [Document(
                page_content=f"Q: {e['question']}\nA: {e['answer']}",
                metadata={"source": "icloud_learned"}
            ) for e in learned]
            vs.add_documents(docs)

        bar.progress(80, text="Connecting to Ollama...")
        import ollama
        ollama.chat(model="phi3:mini", messages=[{"role": "user", "content": "hi"}])
        bar.progress(100, text="Ready!")

        st.session_state.vs = vs
        st.session_state.Document = Document
        st.session_state.ollama = ollama
        st.session_state.backend_ready = True
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.stop()

vs       = st.session_state.vs
Document = st.session_state.Document
ollama   = st.session_state.ollama

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.success("✅ Ready!")

    # ── iCloud status
    st.markdown("### ☁️ iCloud Storage")
    learned_data = load_learned()
    all_convos   = load_json(CONVERSATIONS_FILE)
    st.markdown(f"- 📚 **{len(learned_data)}** learned answers saved")
    st.markdown(f"- 💬 **{len(all_convos)}** past conversations saved")
    st.caption(f"`{ICLOUD_PATH}`")

    st.divider()

    # ── Past conversations
    st.markdown("### 💬 Past Conversations")
    if not all_convos:
        st.info("No past conversations yet.")
    else:
        for i, convo in enumerate(reversed(all_convos[-10:]), 1):
            label = f"[{convo['date']}] ({len(convo['messages'])} msgs)"
            with st.expander(label):
                for msg in convo["messages"]:
                    role = "🧑 You" if msg["role"] == "user" else "🤖 Bot"
                    st.markdown(f"**{role}:** {msg['content'][:200]}{'...' if len(msg['content'])>200 else ''}")

    st.divider()

    # ── Learned answers
    st.markdown("### 🧠 Learned Answers (Permanent)")
    if not learned_data:
        st.info("Nothing learned yet.")
    else:
        for i, e in enumerate(learned_data[-5:], 1):
            with st.expander(f"[{i}] {e['question'][:45]}..."):
                st.write(e["answer"][:300])

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat"):
            if st.session_state.messages:
                save_conversation(st.session_state.messages)
            st.session_state.messages = []
            st.session_state.pending_feedback = None
            st.rerun()
    with col2:
        if st.button("🗑️ Clear iCloud"):
            save_json(CONVERSATIONS_FILE, [])
            save_json(LEARNED_FILE, [])
            st.toast("iCloud data cleared!")
            st.rerun()

# ── Ask function ───────────────────────────────────────────────
def ask(question):
    results = vs.similarity_search_with_score(question, k=4)
    if not results:
        return "I couldn't find anything relevant.", "🔴 Very Low"

    docs  = [r[0] for r in results]
    score = results[0][1]
    context = "\n\n".join([d.page_content for d in docs])

    if score < 0.3:   conf = "🟢 High"
    elif score < 0.6: conf = "🟡 Medium"
    elif score < 1.0: conf = "🟠 Low"
    else:             conf = "🔴 Very Low"

    history = ""
    if st.session_state.messages:
        recent = st.session_state.messages[-6:]
        history = "\n".join([
            f"{'Student' if m['role']=='user' else 'Tutor'}: {m['content']}"
            for m in recent
        ])

    prompt = f"""You are an expert Physics tutor covering Class 10, Class 11, Class 12 and College level physics (CBSE and university curriculum).
Use the context and conversation history to answer clearly. Include formulas and step-by-step explanations where needed.
If unsure, say so honestly.

=== Conversation So Far ===
{history if history else "(First question)"}

=== Relevant Physics Knowledge ===
{context}

=== Question ===
{question}

=== Answer ==="""

    r1 = ollama.chat(model="phi3:mini", messages=[{"role": "user", "content": prompt}])
    draft = r1["message"]["content"].strip()

    r2 = ollama.chat(model="phi3:mini", messages=[{"role": "user", "content": f"""You are a strict Physics examiner.
Improve this answer if needed. If perfect, return unchanged.
Question: {question}
Draft: {draft}
Improved Answer:"""}])
    final = r2["message"]["content"].strip()

    return final, conf

# ── Render chat ────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and "confidence" in msg:
            st.caption(f"📊 Confidence: {msg['confidence']}")

# ── Feedback ───────────────────────────────────────────────────
if st.session_state.pending_feedback:
    pf = st.session_state.pending_feedback
    st.divider()
    st.markdown("**📝 Was this answer correct?**")
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("✅ Yes — save to iCloud"):
            # Add to vectorstore (session) AND save permanently to iCloud
            vs.add_documents([Document(
                page_content=f"Q: {pf['question']}\nA: {pf['answer']}",
                metadata={"source": "icloud_learned"}
            )])
            add_to_learned(pf["question"], pf["answer"])
            st.session_state.pending_feedback = None
            st.toast("✅ Saved to iCloud! Will be remembered next session.")
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
        correction = st.text_area("✏️ Type the correct answer:", height=100, key="correction_box")
        if st.button("💾 Save Correction to iCloud"):
            if correction.strip():
                vs.add_documents([Document(
                    page_content=f"Q: {pf['question']}\nA: {correction.strip()}",
                    metadata={"source": "icloud_learned"}
                )])
                add_to_learned(pf["question"], correction.strip())
                st.session_state.pending_feedback = None
                st.toast("🧠 Correction saved to iCloud permanently!")
                st.rerun()

# ── Chat input ─────────────────────────────────────────────────
question = st.chat_input("Ask a Physics question (Class 10 to College)...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("🔁 Thinking + self-reviewing..."):
            try:
                answer, conf = ask(question)
                st.write(answer)
                st.caption(f"📊 Confidence: {conf}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "confidence": conf
                })
                st.session_state.pending_feedback = {
                    "question": question,
                    "answer": answer
                }
                # Auto-save conversation to iCloud after every message
                save_conversation(st.session_state.messages)
            except Exception as e:
                st.error(f"❌ Error: {e}")
    st.rerun()