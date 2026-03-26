import sys, os

print("=" * 60)
print("   ⚛️   Class 10 Physics Chatbot  (Smart Edition)")
print("=" * 60)

# ── Imports ────────────────────────────────────────────────────
print("\n🔄 Loading libraries...")
try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.docstore.document import Document
    import ollama
    print("   ✅ Libraries loaded.")
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    sys.exit()

# ── Check index ────────────────────────────────────────────────
if not os.path.exists("./physics_index"):
    print("\n❌ ERROR: Run 'python3 build_index.py' first!")
    sys.exit()

# ── Load knowledge base ────────────────────────────────────────
print("\n🔄 Loading physics knowledge base...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)
vectorstore = FAISS.load_local(
    "physics_index", embeddings,
    allow_dangerous_deserialization=True
)
print("   ✅ Knowledge base loaded.")

# ── Test Ollama ────────────────────────────────────────────────
print("\n🤖 Connecting to Ollama...")
try:
    ollama.chat(model="phi3:mini", messages=[{"role": "user", "content": "hi"}])
    print("   ✅ Ollama connected (phi3:mini ready).")
except Exception as e:
    print(f"\n❌ Ollama error: {e}")
    sys.exit()

# ── In-memory session store (deleted when you quit) ────────────
session_learned = []       # stores corrections made this session
conversation_history = []  # stores the chat so far this session

def inject_into_session(question, answer):
    """Add a Q&A into the live in-memory vectorstore (not saved to disk)."""
    doc = Document(
        page_content=f"Q: {question}\nA: {answer}",
        metadata={"source": "session"}
    )
    vectorstore.add_documents([doc])
    # NOTE: we do NOT call vectorstore.save_local() — so nothing is written to disk

# ── Confidence score ───────────────────────────────────────────
def get_confidence(question):
    results = vectorstore.similarity_search_with_score(question, k=4)
    if not results:
        return [], "🔴 Very Low — not in my knowledge base", 99.0
    docs = [r[0] for r in results]
    best_score = results[0][1]
    if best_score < 0.3:
        label = "🟢 High — I'm confident about this"
    elif best_score < 0.6:
        label = "🟡 Medium — fairly sure, double-check if important"
    elif best_score < 1.0:
        label = "🟠 Low — I'm not very sure about this"
    else:
        label = "🔴 Very Low — this may not be in my knowledge base"
    return docs, label, best_score

# ── Self-reflection ────────────────────────────────────────────
def reflect(question, draft):
    prompt = f"""You are a strict Class 10 CBSE Physics examiner reviewing a tutor's answer.
Rewrite the answer to be more accurate, clear and complete if needed.
If it is already perfect, return it unchanged.

Question: {question}
Draft Answer: {draft}

Improved Final Answer:"""
    r = ollama.chat(model="phi3:mini", messages=[{"role": "user", "content": prompt}])
    return r["message"]["content"].strip()

# ── Ask function ───────────────────────────────────────────────
def ask(question):
    docs, confidence_label, score = get_confidence(question)
    context = "\n\n".join([d.page_content for d in docs])

    # Include recent conversation so it remembers context
    history_text = ""
    if conversation_history:
        history_text = "\n".join([
            f"{'Student' if m['role'] == 'user' else 'Tutor'}: {m['content']}"
            for m in conversation_history[-6:]
        ])

    prompt = f"""You are an expert Class 10 CBSE Physics tutor.
Use the context and conversation history to answer the student's question.
Give a clear step-by-step answer with formulas where needed.
If unsure, say so honestly.

=== Conversation So Far ===
{history_text if history_text else "(First question of the session)"}

=== Relevant Physics Knowledge ===
{context}

=== Student's Question ===
{question}

=== Your Answer ==="""

    r = ollama.chat(model="phi3:mini", messages=[{"role": "user", "content": prompt}])
    draft = r["message"]["content"].strip()

    print("\n   🔁 Self-reviewing answer...")
    final = reflect(question, draft)

    conversation_history.append({"role": "user", "content": question})
    conversation_history.append({"role": "assistant", "content": final})

    return final, confidence_label

# ── Feedback handler ───────────────────────────────────────────
def handle_feedback(question, answer):
    print("\n📝 Was this answer correct?")
    print("   [y] Yes   [n] No, I'll correct it   [s] Skip")
    choice = input("   Choice (y/n/s): ").strip().lower()

    if choice == "y":
        # Inject into live memory so future answers benefit from it this session
        inject_into_session(question, answer)
        session_learned.append({"question": question, "answer": answer})
        print("   ✅ Got it! I've used this to improve my answers for the rest of this session.")
        print("   🗑️  (This will be forgotten when you quit — nothing saved to disk.)")

    elif choice == "n":
        print("\n   ✏️  Type the correct answer (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line == "" and lines:
                break
            elif line != "":
                lines.append(line)
        correct = "\n".join(lines).strip()
        if correct:
            inject_into_session(question, correct)
            session_learned.append({"question": question, "answer": correct})
            print("   ✅ Thanks! I've learned the correct answer for this session.")
            print("   🔁 I'll use it to give better answers to similar questions.")
            print("   🗑️  (This will be forgotten when you quit — nothing saved to disk.)")
    else:
        print("   (Skipped)")

# ── Help ───────────────────────────────────────────────────────
def show_help():
    print("\n📖 COMMANDS:")
    print("   'quit'    → Exit (all session learning is discarded)")
    print("   'history' → Show this session's conversation")
    print("   'learned' → Show what I've learned this session")
    print("   'clear'   → Clear conversation memory")
    print("   'help'    → Show this menu\n")

def show_history():
    if not conversation_history:
        print("\n📭 No conversation yet.\n")
        return
    print("\n" + "=" * 60)
    for msg in conversation_history:
        role = "🧑 You" if msg["role"] == "user" else "🤖 Bot"
        print(f"\n{role}: {msg['content'][:300]}{'...' if len(msg['content']) > 300 else ''}")
    print("=" * 60 + "\n")

def show_learned():
    if not session_learned:
        print("\n📭 Nothing learned yet this session.\n")
        return
    print(f"\n🧠 Learned {len(session_learned)} thing(s) this session (in memory only):\n")
    for i, e in enumerate(session_learned, 1):
        print(f"[{i}] Q: {e['question']}")
        print(f"     A: {e['answer'][:150]}{'...' if len(e['answer']) > 150 else ''}\n")

# ── Main loop ──────────────────────────────────────────────────
print("\n✅ Smart Physics Chatbot ready!")
print("   • Remembers our conversation this session")
print("   • Reviews and improves its own answers")
print("   • Learns from your corrections (in memory only)")
print("   • Tells you how confident it is")
print("   • Forgets everything when you quit (nothing saved to disk)")
show_help()
print("-" * 60)

while True:
    try:
        user_input = input("\n🧑 You: ").strip()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! (Session memory cleared)")
        break

    if not user_input:
        continue
    if user_input.lower() in ("quit", "exit"):
        print("\n👋 Goodbye! (Session memory cleared)")
        break
    elif user_input.lower() == "history":
        show_history()
        continue
    elif user_input.lower() == "learned":
        show_learned()
        continue
    elif user_input.lower() == "clear":
        conversation_history.clear()
        print("   🗑️  Conversation cleared.")
        continue
    elif user_input.lower() == "help":
        show_help()
        continue

    print("\n   🤖 Thinking + self-reviewing...")
    try:
        answer, confidence = ask(user_input)
        print(f"\n🤖 Bot:\n{answer}")
        print(f"\n📊 Confidence: {confidence}")
        print("-" * 60)
        handle_feedback(user_input, answer)
        print("-" * 60)
    except Exception as e:
        print(f"\n❌ Error: {e}")