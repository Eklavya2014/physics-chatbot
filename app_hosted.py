import streamlit as st
import os
import datetime
import re
import urllib.parse
import streamlit.components.v1

st.set_page_config(
    page_title="PhysIQ — Science & English Tutor",
    page_icon="⚛️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ── Env vars ───────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
HF_TOKEN     = os.getenv("HF_TOKEN")

if not all([SUPABASE_URL, SUPABASE_KEY, HF_TOKEN]):
    st.error("❌ Missing environment variables. Check your .env file.")
    st.stop()

from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_authed_client():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    token = st.session_state.get("access_token")
    if token:
        client.auth.set_session(token, token)
    return client

# ── Session state ──────────────────────────────────────────────
defaults = {
    "user": None, "access_token": None, "messages": [],
    "pending_feedback": None, "backend_ready": False,
    "dark_mode": True, "show_landing": True,
    "simplify_target": None, "solver_result": None, "creative_mode": False, "coding_mode": False, "web_search_mode": False, "show_animator": False, "pdf_text": None, "pdf_name": None, "voice_mode": False, "voice_reply": None, "selected_voice": 0, "show_profile": False, "user_profile": None, "animation_data": None, "quiz_state": None, "quiz_active": False, "voice_transcript": "", "_voice_question": None, "voice_clear_pending": False,
    "visit_count": 0, "session_restored": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Theme CSS ──────────────────────────────────────────────────
def inject_theme():
    dark = st.session_state.dark_mode
    bg        = "#0d1117" if dark else "#f8f9fa"
    card_bg   = "#161b22" if dark else "#ffffff"
    text      = "#e6edf3" if dark else "#1a1a2e"
    subtext   = "#8b949e" if dark else "#6c757d"
    accent    = "#58a6ff" if dark else "#0066cc"
    border    = "#30363d" if dark else "#dee2e6"
    hero_grad = "linear-gradient(135deg,#0d1117 0%,#161b22 50%,#0d1117 100%)" if dark \
                else "linear-gradient(135deg,#e8f4f8 0%,#dbeafe 50%,#e8f4f8 100%)"
    btn_bg    = "#21262d" if dark else "#e9ecef"
    inp_bg    = "#0d1117" if dark else "#ffffff"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        background-color: {bg} !important;
        color: {text} !important;
    }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding-top: 1.5rem; max-width: 800px; }}

    /* ── Hero section ── */
    .hero {{
        background: {hero_grad};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 48px 32px;
        text-align: center;
        margin-bottom: 28px;
    }}
    .hero-title {{
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #58a6ff, #79c0ff, #a5d6ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 8px 0;
        line-height: 1.1;
    }}
    .hero-sub {{
        font-size: 1.15rem;
        color: {subtext};
        margin-bottom: 28px;
    }}
    .feature-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 14px;
        margin: 24px 0;
    }}
    .feature-card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 18px;
        text-align: left;
    }}
    .feature-icon {{ font-size: 1.6rem; margin-bottom: 8px; }}
    .feature-title {{ font-weight: 600; color: {text}; margin-bottom: 4px; }}
    .feature-desc {{ font-size: 0.85rem; color: {subtext}; }}

    /* ── Chat ── */
    .stChatMessage {{ background: {card_bg} !important; border: 1px solid {border} !important; border-radius: 12px !important; }}

    /* ── Solver box ── */
    .solver-box {{
        background: {card_bg};
        border: 1px solid {accent};
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
    }}
    .solver-title {{ color: {accent}; font-weight: 600; font-size: 1rem; margin-bottom: 8px; }}

    /* ── Buttons ── */
    .stButton > button {{
        border-radius: 8px;
        border: 1px solid {border};
        background: {btn_bg};
        color: {text};
        font-family: 'Inter', sans-serif;
        transition: all 0.2s;
    }}
    .stButton > button:hover {{
        border-color: {accent};
        color: {accent};
    }}

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: {inp_bg} !important;
        border: 1px solid {border} !important;
        color: {text} !important;
        border-radius: 8px !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab"] {{
        color: {subtext} !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {accent} !important;
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: {card_bg} !important;
        border-right: 1px solid {border} !important;
    }}

    /* ── Confidence badge ── */
    .conf-high   {{ color: #3fb950; font-weight: 600; }}
    .conf-med    {{ color: #d29922; font-weight: 600; }}
    .conf-low    {{ color: #f85149; font-weight: 600; }}

    /* ── Divider ── */
    hr {{ border-color: {border} !important; }}

    /* ── Section headers ── */
    .section-label {{
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: {subtext};
        margin-bottom: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

inject_theme()

# ══════════════════════════════════════════════════════════════
#  LANDING PAGE
# ══════════════════════════════════════════════════════════════
def show_landing():
    # Inject localStorage session restore on first load
    if not st.session_state.get("session_restored"):
        inject_session_persistence()
        st.session_state.session_restored = True
        # Check URL params for restored session
        try:
            params = st.query_params
            at = params.get("restore_at","")
            rt = params.get("restore_rt","")
            em = params.get("restore_em","")
            vc = int(params.get("restore_vc",0))
            if at and at != "":
                if restore_session_from_js(at, rt, em, "", "", vc):
                    try:
                        del st.query_params["restore_at"]
                        del st.query_params["restore_rt"]
                        del st.query_params["restore_em"]
                        del st.query_params["restore_vc"]
                    except: pass
                    st.rerun()
        except: pass

    # Theme toggle top-right
    col_sp, col_btn = st.columns([5,1])
    with col_btn:
        if st.button("🌙" if st.session_state.dark_mode else "☀️", help="Toggle dark/light mode"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    st.markdown("""
    <div class="hero">
        <div class="hero-title">⚛️ PhysIQ</div>
        <div class="hero-sub">Your AI Science Tutor — Physics & Chemistry<br>
        Class 10 · Class 11 · Class 12 · College Level</div>
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <div class="feature-title">Smart Answers</div>
                <div class="feature-desc">Powered by advanced AI with deep knowledge base</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔢</div>
                <div class="feature-title">Step-by-Step Solver</div>
                <div class="feature-desc">Solve any numerical problem with full working shown</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🗣️</div>
                <div class="feature-title">Explain Simply</div>
                <div class="feature-desc">Any concept re-explained in simple everyday language</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">✍️</div>
                <div class="feature-title">Creative Writing</div>
                <div class="feature-desc">Essays, debates, letters, diary entries, stories &amp; more</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Confidence Score</div>
                <div class="feature-desc">Know how confident the AI is in every answer</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">✍️</div>
                <div class="feature-title">English Writing</div>
                <div class="feature-desc">Essays, debates, letters, stories, poetry and more</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎨</div>
                <div class="feature-title">Creative Mode</div>
                <div class="feature-desc">Vivid, original creative writing with literary flair</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    tab_login, tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])

    with tab_login:
        st.markdown('<div class="section-label">Sign in to your account</div>', unsafe_allow_html=True)
        email    = st.text_input("Email address", key="login_email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sign In →", use_container_width=True):
                if not email or not password:
                    st.error("Please enter email and password.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user         = res.user
                        st.session_state.access_token = res.session.access_token
                        st.session_state.show_landing = False
                        st.toast("✅ Welcome back!")
                        # Save session to localStorage
                        save_session_to_js(res.user, res.session.access_token,
                            getattr(res.session,"refresh_token",""))
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")
        with c2:
            if st.button("Sign in with Google 🔵", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_oauth({
                        "provider": "google",
                        "options": {"redirect_to": os.getenv("REDIRECT_URL", "http://localhost:8501")}
                    })
                    st.markdown(f"[Click here to sign in with Google →]({res.url})")
                except Exception as e:
                    st.error(f"❌ {e}")

    with tab_signup:
        st.markdown('<div class="section-label">Create your free account</div>', unsafe_allow_html=True)
        name       = st.text_input("Full Name", key="signup_name", placeholder="Your name")
        email_s    = st.text_input("Email", key="signup_email", placeholder="you@example.com")
        password_s = st.text_input("Password (min 6 chars)", type="password", key="signup_password")
        password_c = st.text_input("Confirm Password", type="password", key="signup_confirm")

        if st.button("Create Free Account →", use_container_width=True):
            if not all([name, email_s, password_s, password_c]):
                st.error("Please fill in all fields.")
            elif password_s != password_c:
                st.error("Passwords do not match.")
            elif len(password_s) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    res = supabase.auth.sign_up({
                        "email": email_s, "password": password_s,
                        "options": {"data": {"full_name": name}}
                    })
                    if res.user:
                        st.success("✅ Account created! Check your email to confirm, then sign in.")
                except Exception as e:
                    st.error(f"❌ {e}")

# ══════════════════════════════════════════════════════════════
#  DB HELPERS
# ══════════════════════════════════════════════════════════════
def get_user_id(): return st.session_state.user.id

def save_message(role, content, confidence=None):
    try:
        get_authed_client().table("messages").insert({
            "user_id": get_user_id(), "role": role,
            "content": content, "confidence": confidence,
            "created_at": datetime.datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        st.warning(f"⚠️ Could not save: {e}")

def load_past_conversations():
    try:
        res = get_authed_client().table("messages").select("*")\
            .eq("user_id", get_user_id()).order("created_at").execute()
        return res.data or []
    except: return []

def save_learned(question, answer):
    try:
        get_authed_client().table("learned_answers").upsert({
            "user_id": get_user_id(), "question": question,
            "answer": answer, "created_at": datetime.datetime.utcnow().isoformat()
        }, on_conflict="user_id,question").execute()
    except Exception as e:
        st.warning(f"⚠️ Could not save: {e}")

def load_learned():
    try:
        res = get_authed_client().table("learned_answers").select("*")\
            .eq("user_id", get_user_id()).execute()
        return res.data or []
    except: return []

def delete_all_data():
    uid = get_user_id()
    try:
        get_authed_client().table("messages").delete().eq("user_id", uid).execute()
        get_authed_client().table("learned_answers").delete().eq("user_id", uid).execute()
    except Exception as e:
        st.error(f"❌ {e}")


# ══════════════════════════════════════════════════════════════
#  PERSISTENT LOGIN (localStorage-based, re-auth every 15 visits)
# ══════════════════════════════════════════════════════════════

VISITS_BEFORE_REAUTH = 15

def inject_session_persistence():
    """Inject JS to save/restore session from localStorage."""
    st.components.v1.html("""
<script>
(function(){
  // ── Restore saved session on load ──
  const saved = localStorage.getItem('physiq_session');
  if(saved){
    try{
      const d = JSON.parse(saved);
      // Send to Streamlit via query param hack
      if(d.access_token && d.refresh_token){
        window.parent.postMessage({
          type:'physiq_restore_session',
          access_token: d.access_token,
          refresh_token: d.refresh_token,
          user_email: d.user_email,
          user_id: d.user_id,
          user_name: d.user_name,
          visit_count: d.visit_count||0
        },'*');
      }
    }catch(e){}
  }

  // ── Listen for save-session from Streamlit ──
  window.addEventListener('message', function(e){
    if(e.data && e.data.type==='physiq_save_session'){
      const existing = JSON.parse(localStorage.getItem('physiq_session')||'{}');
      const vc = (existing.visit_count||0)+1;
      localStorage.setItem('physiq_session', JSON.stringify({
        access_token: e.data.access_token,
        refresh_token: e.data.refresh_token,
        user_email: e.data.user_email,
        user_id: e.data.user_id,
        user_name: e.data.user_name,
        visit_count: vc,
        saved_at: Date.now()
      }));
    }
    if(e.data && e.data.type==='physiq_clear_session'){
      localStorage.removeItem('physiq_session');
    }
    if(e.data && e.data.type==='physiq_restore_session'){
      // Already handled above on load
    }
  });
})();
</script>
""", height=0)

def restore_session_from_js(access_token, refresh_token, user_email, user_id, user_name, visit_count):
    """Try to restore session from saved token."""
    if st.session_state.get("user"):
        return True
    try:
        res = supabase.auth.set_session(access_token, refresh_token)
        if res and res.user:
            st.session_state.user = res.user
            st.session_state.access_token = access_token
            st.session_state.show_landing = False
            st.session_state.visit_count = visit_count
            return True
    except:
        pass
    return False

def save_session_to_js(user, access_token, refresh_token=""):
    """Tell JS to save session to localStorage."""
    name = ""
    try: name = user.user_metadata.get("full_name","")
    except: pass
    st.components.v1.html(f"""
<script>
window.parent.postMessage({{
  type:'physiq_save_session',
  access_token:{repr(access_token)},
  refresh_token:{repr(refresh_token or "")},
  user_email:{repr(user.email or "")},
  user_id:{repr(str(user.id))},
  user_name:{repr(name)},
}}, '*');
</script>
""", height=0)

def clear_session_from_js():
    """Tell JS to clear localStorage session."""
    st.components.v1.html("""
<script>window.parent.postMessage({type:'physiq_clear_session'},'*');</script>
""", height=0)


# ══════════════════════════════════════════════════════════════
#  BACKEND
# ══════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_backend():
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.docstore.document import Document
    emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
    vs  = FAISS.load_local("physics_index", emb, allow_dangerous_deserialization=True)
    return vs, Document

def call_hf(system_msg, user_msg, max_tokens=2000):
    """Core HuggingFace call — shared by all features."""
    from huggingface_hub import InferenceClient
    models = [
        "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "deepseek-ai/DeepSeek-V3",
    ]
    client = InferenceClient(base_url="https://router.huggingface.co/together/v1", api_key=HF_TOKEN)
    errors = []
    for model in models:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content":system_msg},{"role":"user","content":user_msg}],
                max_tokens=max_tokens, temperature=0.3,
            )
            answer = resp.choices[0].message.content.strip()
            if answer:
                return answer
        except Exception as e:
            errors.append(f"- {model}: {str(e)[:100]}")
    st.error("All AI models failed:\n" + "\n".join(errors))
    return None

def get_confidence(results):
    if not results: return "🔴 Very Low", "conf-low"
    score = results[0][1]
    if score < 0.3:   return "🟢 High confidence",   "conf-high"
    elif score < 0.6: return "🟡 Medium confidence",  "conf-med"
    elif score < 1.0: return "🟠 Low confidence",     "conf-low"
    else:             return "🔴 Very Low",            "conf-low"

# ── Feature 1: Normal Ask ─────────────────────────────────────
def ask_question(question, vs, history_text):
    results = vs.similarity_search_with_score(question, k=4)
    conf_label, conf_class = get_confidence(results)
    context = "\n\n".join([r[0].page_content for r in results]) if results else ""

    # Detect if question is about English/writing
    english_keywords = ["essay", "debate", "letter", "diary", "story", "poem", "speech",
                        "report", "paragraph", "grammar", "vocabulary", "creative", "write",
                        "writing", "narrative", "describe", "argument", "persuasive", "formal",
                        "informal", "comprehension", "figure of speech", "metaphor", "simile",
                        "alliteration", "rebuttal", "thesis", "introduction", "conclusion"]
    is_english = any(w in question.lower() for w in english_keywords)

    if is_english:
        system = """You are an expert English Language and Literature teacher and creative writing coach.
You help students with:
- Essay writing (argumentative, descriptive, narrative, expository)
- Debate writing and speech writing
- Formal and informal letter writing
- Diary entries, creative stories, and poetry
- Grammar, vocabulary, and language analysis
- Comprehension and literary analysis

Always follow proper writing conventions and rules. When asked to write something:
1. Follow the correct FORMAT and STRUCTURE for that type of writing
2. Use appropriate LANGUAGE and TONE
3. Apply relevant LITERARY DEVICES where suitable
4. Show CREATIVITY while maintaining correctness

If asked to write an essay/letter/story etc., actually WRITE it — do not just explain how to write it.
Be creative, use vivid language, strong vocabulary, and varied sentence structures."""
    else:
        is_creative = st.session_state.get("creative_mode", False)
    is_coding = st.session_state.get("coding_mode", False)
    # Personalisation from user profile
    profile_ctx = build_personalisation_context(st.session_state.get("user_profile"))
    if is_creative:
        system = ("""You are a brilliant, creative English writing expert with the literary sensibility of a published author and the precision of an English professor.
You write with vivid imagery, original metaphors, varied sentence rhythms, and emotional intelligence.
When asked to write essays, debates, letters, stories, poems, diary entries, speeches, or any creative writing:
- Follow the correct format and rules for that genre meticulously
- Use sophisticated, precise vocabulary
- Vary sentence structure (short punchy sentences mixed with longer flowing ones)
- Include figurative language (original similes, metaphors, personification)
- Create atmosphere, mood, and emotional resonance
- Show don't tell
- Always explain the rules/structure you used after your writing
If asked about grammar, literature, or comprehension — explain clearly with examples.""") + profile_ctx
    else:
        system = """You are PhysIQ — an expert AI tutor covering Physics, Chemistry, Mathematics, English, Biology, and General Science from Class 10 to College level.

CRITICAL RULE — UNDERSTAND INTENT FIRST:
Before answering, decide what the user ACTUALLY wants:
1. EXPLANATION: "What is Newton's law?" / "Explain photosynthesis" / "How does DNA work?" → Give a clear educational explanation with examples and formulas.
2. CALCULATION: "Calculate the force when..." / "Find the pH of..." → Solve step-by-step with working shown.
3. DEFINITION: "What is entropy?" / "Define oxidation" → Give a precise definition with context.
4. COMPARISON: "Difference between..." / "Compare X and Y" → Structured comparison.
5. CONCEPT QUESTION: "Why does ice float?" / "How do planes fly?" → Intuitive explanation first, then technical detail.
6. CONVERSATIONAL: "Hello", "Thanks", "That was helpful" → Respond naturally and warmly.

NEVER write computer code unless the user EXPLICITLY asks for code (e.g. "write a Python program", "code for me").
If someone asks "how does Python handle memory?" — explain the concept, do NOT write Python code.
If someone asks "what is a for loop?" — explain with a simple example, do NOT write a full program.

FORMAT YOUR ANSWERS WELL:
- Use clear headings for complex topics
- Use bullet points for lists
- Show formulas clearly: F = ma, E = mc²
- Give real-world examples
- Keep answers focused and not too long unless detail is needed
- Be encouraging and friendly

If you don't know something or are unsure, say so honestly."""

    user = f"""Conversation so far:
{history_text if history_text else "(First question)"}

Relevant Knowledge:
{context}

Question: {question}

Answer:"""

    answer = call_hf(system, user)
    return answer or "Could not generate a response.", conf_label, conf_class

# ── Feature 2: Step-by-Step Numerical Solver ─────────────────
def solve_numerical(problem, vs):
    results = vs.similarity_search_with_score(problem, k=3) if vs else []
    context = "\n\n".join([r[0].page_content for r in results]) if results else ""

    system = """You are an expert Physics and Chemistry problem solver.
Solve the given numerical problem with COMPLETE step-by-step working.
Use this exact format:

**Given:**
(list all given values with units)

**To Find:**
(what is asked)

**Formula Used:**
(write the relevant formula)

**Solution:**
Step 1: (first step with calculation)
Step 2: (next step)
... (continue until answer)

**Answer:**
(final answer with correct units, in a box if possible)

**Key Concept:**
(one sentence explaining the concept tested)"""

    user = f"""Relevant formulas and concepts:
{context}

Problem to solve:
{problem}"""

    return call_hf(system, user, max_tokens=1500)

# ── Feature 3: Explain Simply ─────────────────────────────────
def explain_simply(original_answer, question):
    system = """You are a friendly science teacher explaining to a 12-year-old student.
Take the technical answer and re-explain it using:
- Simple everyday language (no jargon)
- A real-life analogy or example
- Short sentences
- Maybe an emoji or two to make it fun
Keep it under 150 words but make sure the key idea is clear."""

    user = f"""Original question: {question}

Technical answer:
{original_answer}

Now explain this simply, like you're talking to a curious 12-year-old:"""

    return call_hf(system, user, max_tokens=400)


# ── Feature 4: Animated Teaching ─────────────────────────────
def generate_animation_script(question, answer):
    """Ask AI to generate a JSON animation script for the canvas animator."""
    system = """You are a scientific animation director for an advanced educational platform.
Given a question and answer, produce a rich JSON animation scene using multiple objects.

CRITICAL: Return ONLY valid JSON. No markdown, no explanation, just JSON.

The JSON format uses a SCENE GRAPH — an array of objects you can freely combine and position:

{
  "subtitle": "Short description",
  "info_text": "Educational explanation shown at bottom (under 120 words)",
  "time_scale": 1.0,
  "bg_gradient": "#color or null",
  "legend": [{"color": "#hex", "label": "name"}],
  "steps": [
    {"title": "Step 1", "info": "What is happening in step 1..."},
    {"title": "Step 2", "info": "What is happening in step 2..."}
  ],
  "step_duration": 5,
  "connections": [
    {"from": 0, "to": 2, "type": "arrow", "color": "#color", "label": "label"}
  ],
  "objects": [
    { object1 },
    { object2 },
    ...many more objects as needed...
  ]
}

POSITIONING RULES — VERY IMPORTANT — read carefully:
- x goes from -1 (far left) to +1 (far right). Center is x=0.
- y goes from -0.9 (bottom) to +0.9 (top). Center is y=0.
- SPREAD objects out! Never put two objects at exactly the same position.
- Minimum distance between any two objects: 0.18 units.
- For atoms/molecules: put the main object at center (0,0), labels BELOW at y=-0.4
- For diagrams with left+right sides: use x=-0.55 and x=+0.55
- For top+bottom rows: use y=+0.3 and y=-0.3
- Formula boxes always go at y=-0.42 (near bottom, above info panel)
- Title labels always go at y=+0.42 (near top)
- Legends go to the right side, x=+0.7

LAYOUT TEMPLATES (use these patterns):

ATOM LAYOUT (example for Carbon):
- Atom at center: {"type":"atom","x":0,"y":0.05,"r":0.2,...}
- Title above: {"type":"label","x":0,"y":0.44,"text":"Carbon (C) — Z=6",...}
- Formula below: {"type":"formula_box","x":-0.3,"y":-0.43,"formula":"Shells: 2,4",...}
- Energy level (right): {"type":"formula_box","x":0.4,"y":0,"formula":"Valency = 4",...}

LEFT-RIGHT LAYOUT (two things to compare):
- Left object: x=-0.45, y=0
- Right object: x=+0.45, y=0  
- Label left: x=-0.45, y=-0.22
- Label right: x=+0.45, y=-0.22
- Arrow between: from x=-0.2 to x=+0.2

TOP-BOTTOM LAYOUT (cause and effect):
- Top object: x=0, y=+0.3
- Arrow down: ty=0 (center)
- Bottom object: x=0, y=-0.15

MULTI-OBJECT LAYOUT (4-6 things):
- Top left: x=-0.45, y=+0.28
- Top right: x=+0.45, y=+0.28
- Middle left: x=-0.45, y=-0.08
- Middle right: x=+0.45, y=-0.08
- Formula box bottom: x=0, y=-0.43

CLARITY RULES:
1. Each object must have a "caption" or nearby label so user knows what it is
2. Never put a label on top of another object — offset labels by at least 0.12 units
3. Use formula_box for equations — place at bottom (y=-0.42)
4. Use "steps" array to guide the user through the animation step by step
5. Keep legends minimal — only include if there are 3+ different colored things
6. The info_text at the bottom should explain WHAT IS HAPPENING right now

Return ONLY the JSON object."""

    user = f"""Question: {question}

Answer given: {answer[:500]}

Generate the animation JSON for this concept:"""

    import json
    raw = call_hf(system, user, max_tokens=800)
    if not raw:
        return None
    # Extract JSON from response
    raw = raw.strip()
    start = raw.find('{')
    end   = raw.rfind('}') + 1
    if start == -1 or end == 0:
        return None
    try:
        data = json.loads(raw[start:end])
        # Ensure it has objects array (new format)
        if 'objects' not in data and 'type' in data:
            # Convert old format to new scene graph format
            data = convert_old_to_new(data)
        return data
    except Exception as e:
        return None

def convert_old_to_new(old):
    """Convert legacy animation format to new scene-graph format."""
    t = old.get('type','atom')
    objects = []
    subtitle = old.get('subtitle','Animation')
    info = old.get('info_text','')
    
    if t=='atom':
        objects.append({"type":"atom","x":0,"y":0.05,"r":0.2,
            "protons":old.get('protons',1),"neutrons":old.get('neutrons',0),
            "shells":old.get('shells',[[1]])})
        objects.append({"type":"label","x":0,"y":-0.4,"text":subtitle,"color":"#58a6ff","size":14})
    elif t=='wave':
        for i,w in enumerate(old.get('waves',[])):
            objects.append({"type":"wave","x":0,"y":w.get('y_offset',0)*0.3,
                "width":0.85,"amp":w.get('amplitude',60)/400,
                "wavelength":w.get('wavelength',150)/400,"speed":w.get('speed',0.03)*2000,
                "color":w.get('color','#44ffaa'),"label_top":w.get('label','')})
    else:
        objects.append({"type":"label","x":0,"y":0,"text":subtitle,"color":"#58a6ff","size":16})
        objects.append({"type":"formula_box","x":0,"y":-0.25,"formula":info[:40] if info else t,
            "color":"#4da6ff","width":0.5,"height":0.12})
    
    return {"subtitle":subtitle,"info_text":info,"objects":objects,
            "legend":old.get('legend',[]),"bg_gradient":None}

def show_animator_panel(animation_data):
    """Render the HTML5 Canvas animator in Streamlit."""
    import json
    with open("animator.html", "r") as f:
        html_content = f.read()
    # Inject data directly into the HTML
    inject_script = f"""
<script>
window.addEventListener('load', function() {{
  try {{
    const data = {json.dumps(animation_data)};
    scene = data;
    if(scene._particles) delete scene._particles;
    document.getElementById('loading').style.display='none';
    const subtitleEl = document.getElementById('subtitle');
    const infoEl = document.getElementById('info-text');
    if (subtitleEl) subtitleEl.textContent = scene.subtitle || scene.type || 'Animation';
    if (infoEl) infoEl.textContent = scene.info_text || '';
    if(scene.legend) updateLegend(scene.legend);
  }} catch(e) {{ console.error(e); }}
}}, 500);
</script>"""
    html_content = html_content.replace('</body>', inject_script + '</body>')
    st.components.v1.html(html_content, height=520, scrolling=False)



# ══════════════════════════════════════════════════════════════
#  QUIZ CONNECTOR
# ══════════════════════════════════════════════════════════════

QUIZ_TRIGGER_WORDS = [
    "quiz", "test me", "question me", "mcq", "multiple choice",
    "fill in the blank", "practice questions", "exam questions",
    "test my knowledge", "ask me questions", "give me a quiz",
    "quiz me", "make a quiz", "create a quiz", "generate a quiz"
]

def is_quiz_request(message):
    """Detect if user is asking for a quiz."""
    msg = message.lower()
    return any(word in msg for word in QUIZ_TRIGGER_WORDS)

def extract_quiz_topic(message):
    """Pull topic and type from user message."""
    msg = message.lower()
    q_type = "mixed"
    if "mcq" in msg or "multiple choice" in msg:
        q_type = "mcq"
    elif "fill" in msg or "blank" in msg:
        q_type = "fill"
    # Try to extract number
    import re
    nums = re.findall(r"\b(\d+)\b", msg)
    num_q = int(nums[0]) if nums else 5
    num_q = min(max(num_q, 3), 15)
    return q_type, num_q

def generate_quiz(topic, q_type, num_q):
    """Generate quiz questions using the AI."""
    import json
    if q_type == "mcq":
        type_instruction = f"Generate exactly {num_q} Multiple Choice Questions (MCQ)."
        schema_note = 'For MCQ: "type":"mcq", "options":["A)...","B)...","C)...","D)..."], "correct":"A"'
    elif q_type == "fill":
        type_instruction = f"Generate exactly {num_q} Fill in the Blank questions."
        schema_note = 'For fill: "type":"fill", "answer":"exact answer"'
    else:
        half = num_q // 2
        type_instruction = f"Generate {half} MCQ and {num_q - half} Fill in the Blank questions."
        schema_note = 'For MCQ: "type":"mcq", "options":["A)...","B)...","C)...","D)..."], "correct":"A". For fill: "type":"fill", "answer":"exact answer"'

    system = f"""You are an expert science and English quiz maker.
{type_instruction}
Return ONLY a valid JSON array. No explanation, no markdown, just the JSON.

Each question object must have:
- "q": the question text (for fill-in-blank, use _______ where the blank is)
- "type": "mcq" or "fill"
- "correct": the correct answer (letter for MCQ like "A", or the word/phrase for fill)
- "explanation": 2-3 sentence explanation of why this is the answer
- "difficulty": "easy", "medium", or "hard"
{schema_note}

Make questions varied in difficulty. Cover the topic thoroughly.
Example fill: {{"q":"Newton's second law states F = m × _______","type":"fill","correct":"a","explanation":"F=ma where a is acceleration. Force equals mass times acceleration.","difficulty":"easy"}}
Example MCQ: {{"q":"What is the SI unit of force?","type":"mcq","options":["A) Joule","B) Newton","C) Watt","D) Pascal"],"correct":"B","explanation":"The Newton (N) is the SI unit of force. 1 N = 1 kg⋅m/s².","difficulty":"easy"}}
"""

    user = f"Generate a quiz about: {topic}"
    raw = call_hf(system, user, max_tokens=2000)
    if not raw:
        return None
    raw = raw.strip()
    start = raw.find('[')
    end = raw.rfind(']') + 1
    if start == -1 or end == 0:
        # Try single object wrapped in array
        start = raw.find('{')
        if start == -1:
            return None
        raw = '[' + raw[start:] + ']'
        end = len(raw)
    try:
        questions = json.loads(raw[start:end])
        return questions[:num_q]
    except:
        return None

def save_quiz_mistakes(mistakes_data):
    """Save quiz mistakes to Supabase for the logged-in user."""
    if not st.session_state.get("user"):
        return
    try:
        import json
        existing = []
        try:
            res = get_authed_client().table("quiz_mistakes").select("*").eq("user_id", get_user_id()).execute()
            existing = res.data or []
        except:
            pass
        all_mistakes = existing + mistakes_data
        # Keep last 50 mistakes only
        all_mistakes = all_mistakes[-50:]
        # Delete old and insert fresh
        try:
            get_authed_client().table("quiz_mistakes").delete().eq("user_id", get_user_id()).execute()
        except:
            pass
        for m in all_mistakes:
            try:
                get_authed_client().table("quiz_mistakes").insert({
                    "user_id": get_user_id(),
                    "question": m.get("q",""),
                    "user_answer": m.get("user_answer",""),
                    "correct_answer": m.get("correct",""),
                    "explanation": m.get("explanation",""),
                    "topic": m.get("topic",""),
                    "created_at": datetime.datetime.utcnow().isoformat()
                }).execute()
            except:
                pass
    except Exception as e:
        st.warning(f"Could not save mistakes: {e}")

def load_quiz_mistakes():
    """Load past mistakes from Supabase."""
    if not st.session_state.get("user"):
        return []
    try:
        res = get_authed_client().table("quiz_mistakes").select("*").eq("user_id", get_user_id()).order("created_at", desc=True).limit(30).execute()
        return res.data or []
    except:
        return []

def generate_mistake_lesson(mistakes):
    """AI generates a personalised lesson based on mistakes."""
    if not mistakes:
        return None
    topics = list(set([m.get("topic","general") for m in mistakes[:10]]))
    wrong_qs = [f"Q: {m.get('question','?')} | Your answer: {m.get('user_answer','?')} | Correct: {m.get('correct_answer','?')}" for m in mistakes[:10]]
    system = """You are a patient, encouraging science and English tutor.
Based on the student's quiz mistakes, write a personalised lesson that:
1. Identifies the pattern of mistakes (which concepts are weak)
2. Clearly explains each weak concept with examples
3. Gives memory tips and mnemonics
4. Ends with 2-3 practice tips
Use friendly, encouraging language. Format with clear sections."""
    user = f"""Topics tested: {', '.join(topics)}

Student's mistakes:
{chr(10).join(wrong_qs)}

Write a personalised lesson to fix these mistakes:"""
    return call_hf(system, user, max_tokens=1500)

def show_celebration():
    """Show celebration animation for correct answer."""
    st.markdown("""
    <div id="celebration" style="text-align:center;padding:8px;animation:pop 0.5s ease-out;">
        <span style="font-size:2rem;">🎉</span>
        <span style="color:#3fb950;font-weight:700;font-size:1.1rem;"> Correct! Well done!</span>
        <span style="font-size:2rem;">⭐</span>
    </div>
    <style>
    @keyframes pop {
        0%{transform:scale(0.5);opacity:0}
        70%{transform:scale(1.15)}
        100%{transform:scale(1);opacity:1}
    }
    </style>
    """, unsafe_allow_html=True)

def show_quiz_ui():
    """Render the interactive quiz panel."""
    qs = st.session_state.quiz_state
    if not qs:
        return

    questions   = qs["questions"]
    current_idx = qs.get("current_idx", 0)
    score       = qs.get("score", 0)
    answers     = qs.get("answers", {})
    skipped     = qs.get("skipped", [])
    phase       = qs.get("phase", "quiz")  # quiz | review | results | lesson

    topic = qs.get("topic","Science")
    total = len(questions)

    st.markdown("---")

    # ── PHASE: QUIZ ───────────────────────────────────────────
    if phase == "quiz" and current_idx < total:
        q = questions[current_idx]
        prog = current_idx / total
        st.progress(prog, text=f"Question {current_idx+1} of {total} | ⭐ Score: {score}/{current_idx}")

        # Difficulty badge
        diff = q.get("difficulty","medium")
        diff_color = "#3fb950" if diff=="easy" else "#d29922" if diff=="medium" else "#f85149"
        st.markdown(f'<span style="background:{diff_color};color:#fff;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600">{diff.upper()}</span>', unsafe_allow_html=True)

        st.markdown(f"### Q{current_idx+1}. {q['q']}")

        q_key = f"quiz_q_{current_idx}"

        if q["type"] == "mcq":
            options = q.get("options", [])
            user_ans = st.radio("Choose your answer:", options, key=q_key, label_visibility="collapsed")
            col1, col2 = st.columns([1,4])
            with col1:
                if st.button("Submit →", key=f"submit_{current_idx}", use_container_width=True):
                    # Extract letter from option like "A) Newton"
                    chosen_letter = user_ans[0] if user_ans else ""
                    correct_letter = q.get("correct","A")
                    is_correct = chosen_letter.upper() == correct_letter.upper()
                    answers[current_idx] = {"q": q["q"], "user_answer": user_ans,
                                            "correct": q["correct"], "is_correct": is_correct,
                                            "explanation": q.get("explanation",""),
                                            "topic": topic}
                    if is_correct:
                        qs["score"] = score + 1
                    else:
                        skipped.append(current_idx)
                    qs["answers"] = answers
                    qs["skipped"] = skipped
                    qs["current_idx"] = current_idx + 1
                    qs["last_correct"] = is_correct
                    st.session_state.quiz_state = qs
                    st.rerun()

        else:  # fill in blank
            user_ans = st.text_input("Type your answer:", key=q_key, placeholder="Your answer here...")
            col1, col2 = st.columns([1,4])
            with col1:
                if st.button("Submit →", key=f"submit_{current_idx}", use_container_width=True):
                    correct = q.get("correct","")
                    is_correct = user_ans.strip().lower() == correct.strip().lower()
                    # Also allow partial match for longer answers
                    if not is_correct and len(correct) > 3:
                        is_correct = correct.strip().lower() in user_ans.strip().lower()
                    answers[current_idx] = {"q": q["q"], "user_answer": user_ans,
                                            "correct": correct, "is_correct": is_correct,
                                            "explanation": q.get("explanation",""),
                                            "topic": topic}
                    if is_correct:
                        qs["score"] = score + 1
                    else:
                        skipped.append(current_idx)
                    qs["answers"] = answers
                    qs["skipped"] = skipped
                    qs["current_idx"] = current_idx + 1
                    qs["last_correct"] = is_correct
                    st.session_state.quiz_state = qs
                    st.rerun()

        # Show result of last answer
        if current_idx > 0 and qs.get("last_correct") is not None:
            if qs["last_correct"]:
                show_celebration()
            else:
                st.error("❌ Incorrect — question saved for review at the end")
        if st.button("⏭️ Skip this question", key=f"skip_{current_idx}"):
            answers[current_idx] = {"q": q["q"], "user_answer": "(skipped)",
                                    "correct": q.get("correct",""), "is_correct": False,
                                    "explanation": q.get("explanation",""), "topic": topic}
            skipped.append(current_idx)
            qs["answers"] = answers
            qs["skipped"] = skipped
            qs["current_idx"] = current_idx + 1
            qs["last_correct"] = False
            st.session_state.quiz_state = qs
            st.rerun()

    # ── PHASE: REVIEW WRONG ANSWERS ──────────────────────────
    elif phase == "quiz" and current_idx >= total:
        qs["phase"] = "review"
        st.session_state.quiz_state = qs
        st.rerun()

    elif phase == "review":
        score = qs.get("score",0)
        pct = round(score / total * 100)
        st.markdown(f"## 🏁 Quiz Complete!")

        # Score display
        score_color = "#3fb950" if pct >= 70 else "#d29922" if pct >= 40 else "#f85149"
        st.markdown(f"""
        <div style="text-align:center;padding:20px;background:rgba(0,0,0,0.3);border-radius:12px;margin:12px 0">
            <div style="font-size:3.5rem;font-weight:700;color:{score_color}">{pct}%</div>
            <div style="color:#8b949e;font-size:1rem">You got {score} out of {total} correct</div>
            <div style="font-size:1.5rem;margin-top:8px">{"🌟 Excellent!" if pct>=80 else "👍 Good effort!" if pct>=50 else "📚 Keep practising!"}</div>
        </div>
        """, unsafe_allow_html=True)

        # Wrong answers section
        wrong = [a for a in answers.values() if not a.get("is_correct")]
        if wrong:
            st.markdown(f"### ❌ {len(wrong)} Questions to Review")
            for i, ans in enumerate(wrong, 1):
                with st.expander(f"❌ Q{i}: {ans['q'][:60]}..."):
                    st.markdown(f"**Your answer:** {ans.get('user_answer','(skipped)')}")
                    st.markdown(f"**✅ Correct answer:** {ans.get('correct','')}")
                    st.markdown(f"**📖 Explanation:** {ans.get('explanation','')}")

            # Save mistakes to Supabase
            save_quiz_mistakes(wrong)
            st.success(f"✅ {len(wrong)} mistakes saved to your account for personalised learning!")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🎓 Get Personalised Lesson", use_container_width=True):
                    qs["phase"] = "lesson"
                    st.session_state.quiz_state = qs
                    st.rerun()
            with col2:
                if st.button("🔄 Try Again", use_container_width=True):
                    st.session_state.quiz_active = False
                    st.session_state.quiz_state = None
                    st.rerun()
            with col3:
                if st.button("✕ Close Quiz", use_container_width=True):
                    st.session_state.quiz_active = False
                    st.session_state.quiz_state = None
                    st.rerun()
        else:
            st.balloons()
            st.success("🎉 Perfect score! You got everything right!")
            if st.button("✕ Close Quiz", use_container_width=True):
                st.session_state.quiz_active = False
                st.session_state.quiz_state = None
                st.rerun()

    # ── PHASE: PERSONALISED LESSON ────────────────────────────
    elif phase == "lesson":
        wrong = [a for a in answers.values() if not a.get("is_correct")]
        st.markdown("## 🎓 Your Personalised Lesson")
        st.caption("Based on your quiz mistakes, the AI has created a custom lesson just for you.")
        with st.spinner("📚 Generating your personalised lesson..."):
            lesson = generate_mistake_lesson(wrong)
        if lesson:
            st.markdown(lesson)
        else:
            st.warning("Could not generate lesson. Please try again.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Take Another Quiz", use_container_width=True):
                st.session_state.quiz_active = False
                st.session_state.quiz_state = None
                st.rerun()
        with col2:
            if st.button("✕ Close", use_container_width=True):
                st.session_state.quiz_active = False
                st.session_state.quiz_state = None
                st.rerun()



# ══════════════════════════════════════════════════════════════
#  CODING CONNECTOR
# ══════════════════════════════════════════════════════════════

CODING_LANGUAGES = {
    "python":"Python","java":"Java","c++":"C++","cpp":"C++",
    "c#":"C#","csharp":"C#","javascript":"JavaScript","js":"JavaScript",
    "typescript":"TypeScript","ts":"TypeScript","roblox":"Roblox Lua",
    "lua":"Lua","rust":"Rust","go":"Go","golang":"Go","swift":"Swift",
    "kotlin":"Kotlin","sql":"SQL","html":"HTML","css":"CSS",
    "react":"React/JSX","php":"PHP","ruby":"Ruby","bash":"Bash/Shell",
    "r":"R","matlab":"MATLAB","dart":"Dart","flutter":"Flutter",
}

# Phrases that STRONGLY indicate user wants code written
CODING_WRITE_TRIGGERS = [
    "write code", "write a program", "write a script", "write a function",
    "write a class", "write a game", "write an app", "write a bot",
    "create a program", "create a script", "create a game", "create an app",
    "build a program", "build a game", "build an app", "build a website",
    "make a program", "make a game", "make a script", "make an app",
    "code for me", "generate code", "can you code", "write me code",
    "implement a", "develop a", "program a", "give me the code",
    "show me the code", "write the code", "full code", "complete code",
]

# Words that just mention coding but user wants EXPLANATION, not code
CODING_EXPLAIN_TRIGGERS = [
    "what is", "explain", "how does", "difference between", "what are",
    "define", "tell me about", "describe", "why does", "how do",
    "what does", "meaning of", "concept of", "theory", "example of",
    "when to use", "pros and cons", "advantages", "disadvantages",
]

def is_coding_request(message):
    """Only return True when user CLEARLY wants code written, not just asking a question."""
    if st.session_state.get("coding_mode", False):
        return True
    msg = message.lower().strip()

    # Strong action words that mean "write me code"
    strong_actions = [
        "write code", "write a program", "write a script", "write a function",
        "write a class", "create a program", "create an app", "build a program",
        "build an app", "build a game", "code for me", "generate code",
        "implement a", "develop a", "program that", "write me code",
        "give me code", "make a program", "make a game", "can you code",
        "write the code", "create the code", "build the code",
        "make a script", "write a bot", "create a bot",
    ]
    # Library names that only appear in coding contexts
    strong_libraries = [
        "ursina", "pygame", "tkinter", "kivy", "flask app", "fastapi",
        "django app", "tensorflow model", "pytorch model", "react component",
        "express server", "spring boot", "roblox script", "arduino code",
    ]

    if any(a in msg for a in strong_actions):
        return True
    if any(lib in msg for lib in strong_libraries):
        return True

    # Language + explicit code word combo
    lang_keys = list(CODING_LANGUAGES.keys())
    has_lang = any(f" {lang} " in f" {msg} " for lang in lang_keys)
    has_code_word = any(w in msg for w in ["code", "program", "script", "function", "class", "syntax"])
    return has_lang and has_code_word


def detect_language(message):
    msg = message.lower()
    for key, lang in CODING_LANGUAGES.items():
        if key in msg:
            return lang
    return "Python"  # default

def generate_code(question, vs, language="Python"):
    results = vs.similarity_search_with_score(question, k=3) if vs else []
    context = "\n\n".join([r[0].page_content for r in results]) if results else ""

    system = f"""You are an elite {language} programmer with 15+ years of experience.
You write clean, efficient, well-commented, production-quality code.
RULES:
1. Write COMPLETE, WORKING code — never truncate or use placeholder comments like "# add code here"
2. Include ALL necessary imports at the top
3. Add clear comments explaining complex logic
4. Follow best practices and design patterns for {language}
5. If the user asks for a game/app, write the FULL implementation
6. You can write up to 2000 lines if needed — never cut short
7. After the code, write a brief explanation of how it works
8. If using a library (ursina, pygame, pandas etc), use it correctly with real API calls
9. Make the code actually runnable with zero modifications needed
10. For Roblox Lua, use proper Roblox API (Services, Instances, Events)

LIBRARIES YOU KNOW PERFECTLY:
Python: numpy, pandas, matplotlib, seaborn, scikit-learn, tensorflow, pytorch,
        flask, fastapi, django, sqlalchemy, pygame, ursina, opencv, requests,
        beautifulsoup4, pillow, pydantic, asyncio, aiohttp, celery, redis,
        plotly, dash, streamlit, gradio, transformers, langchain, openai
Java: Spring Boot, Hibernate, Maven, Gradle, JUnit, Mockito
C++: STL, Boost, OpenGL, SDL2, SFML, CMake
JavaScript: React, Vue, Angular, Express, Next.js, Node.js, TypeScript
Roblox Lua: All Roblox services, DataStore, TweenService, RemoteEvents
Rust: tokio, serde, actix-web, reqwest
Go: gin, echo, gorm, cobra

Write the code now:"""

    user = f"""Relevant documentation:
{context}

Task: {question}

Write complete, working {language} code:"""

    return call_hf(system, user, max_tokens=30000)



# ══════════════════════════════════════════════════════════════
#  PDF READER
# ══════════════════════════════════════════════════════════════

def extract_pdf_text(pdf_file):
    """Extract text from uploaded PDF file."""
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n{page_text}"
        return text.strip()
    except Exception as e:
        return None

def answer_from_pdf(pdf_text, question):
    """Use AI to answer a question based on PDF content."""
    # Trim PDF text to avoid token overflow
    trimmed = pdf_text[:4000] if len(pdf_text) > 4000 else pdf_text
    system = """You are an expert tutor. A student has uploaded a PDF document and asked a question about it.
Read the document carefully and answer the question accurately and clearly.
If the answer is not in the document, say so honestly.
Format your answer with clear sections if needed."""
    user = f"""PDF Content:
{trimmed}

Student's question: {question}

Answer based on the PDF:"""
    return call_hf(system, user, max_tokens=1500)

def summarise_pdf(pdf_text):
    """Generate a structured summary of a PDF."""
    trimmed = pdf_text[:5000] if len(pdf_text) > 5000 else pdf_text
    system = """You are an expert academic summariser.
Create a clear, structured summary of this document with:
- Main topic and purpose
- Key concepts covered  
- Important facts, formulas, or findings
- Conclusions or takeaways
Use bullet points and headers for clarity."""
    user = f"""Document to summarise:\n{trimmed}\n\nProvide a structured summary:"""
    return call_hf(system, user, max_tokens=1200)



# ══════════════════════════════════════════════════════════════
#  VOICE CONNECTOR
# ══════════════════════════════════════════════════════════════

def generate_voice_answer(question, full_answer):
    """Generate a short, spoken-friendly version of the answer."""
    system = """You are a friendly science tutor speaking out loud.
Convert this answer into a SHORT spoken response (under 60 words).
Rules:
- Speak naturally, like talking to a student face-to-face
- No markdown, no bullet points, no symbols like * or #
- No formulas with special characters — say them in words (e.g. "F equals m times a")
- Get straight to the point
- End with one short key fact
- Sound warm and encouraging"""
    user = f"""Question: {question}
Full answer: {full_answer[:800]}

Write a short spoken version (under 60 words):"""
    return call_hf(system, user, max_tokens=200)

@st.cache_resource(show_spinner=False)
def load_local_asr():
    """Load a lightweight local Whisper pipeline for transcription."""
    import torch
    from transformers import pipeline

    device = 0 if torch.cuda.is_available() else -1
    return pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-tiny.en",
        device=device,
    )

def normalize_voice_text(text):
    """Clean transcript text and decode stray URL-encoded mic payloads."""
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""

    if "%" in cleaned and re.search(r"%[0-9A-Fa-f]{2}", cleaned):
        decoded = urllib.parse.unquote_plus(cleaned).strip()
        if decoded:
            cleaned = decoded

    return " ".join(cleaned.split())

def consume_browser_voice_query():
    """Pick up browser speech input passed through the URL and feed it into chat."""
    try:
        raw_text = st.query_params.get("voice_text", "")
    except Exception:
        raw_text = ""

    question = normalize_voice_text(raw_text)

    for key in ("voice_text", "voice_nonce"):
        try:
            del st.query_params[key]
        except Exception:
            pass

    if question:
        st.session_state._voice_question = question
        st.session_state._is_voice_question = True
        st.rerun()

def transcribe_audio_hf(audio_bytes):
    """Transcribe recorded audio using a local Whisper pipeline."""
    import io
    import numpy as np
    from scipy.io import wavfile

    try:
        sample_rate, audio_array = wavfile.read(io.BytesIO(audio_bytes))
        if audio_array.ndim > 1:
            audio_array = audio_array.mean(axis=1)
        if np.issubdtype(audio_array.dtype, np.integer):
            max_val = np.iinfo(audio_array.dtype).max
            audio_array = audio_array.astype(np.float32) / max(max_val, 1)
        else:
            audio_array = audio_array.astype(np.float32)

        asr = load_local_asr()
        result = asr({"raw": audio_array, "sampling_rate": int(sample_rate)})
        text = result.get("text") if isinstance(result, dict) else None
        normalized = normalize_voice_text(text)
        if normalized:
            return normalized, None
        return None, "The audio was processed, but no speech was detected."
    except Exception as e:
        return None, f"Local transcription failed: {str(e)[:160]}"

def show_voice_ui():
    """Render a native Streamlit voice panel using microphone recording."""
    st.markdown("Record a short question, transcribe it, then send it into the chat.")

    if st.session_state.get("voice_clear_pending"):
        st.session_state.voice_transcript = ""
        st.session_state.voice_transcript_editor = ""
        st.session_state.voice_clear_pending = False

    audio = st.audio_input("🎙️ Record your question", key="voice_audio_input")
    if audio is None:
        st.caption("Tap record, speak clearly, and stop when you're done.")
        return

    st.audio(audio)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⚡ Ask in ~3 sec", use_container_width=True, key="voice_quick_ask_btn"):
            with st.spinner("🎧 Converting your speech to text..."):
                transcript, error = transcribe_audio_hf(audio.getvalue())
            if transcript:
                st.session_state.voice_transcript = transcript
                st.session_state.voice_transcript_editor = transcript
                st.session_state._voice_question = transcript
                st.session_state._is_voice_question = True
                st.session_state.voice_clear_pending = True
                st.rerun()
            else:
                st.error(f"❌ Could not transcribe this recording. {error or ''}".strip())
    with col2:
        if st.button("📝 Transcribe Only", use_container_width=True, key="voice_transcribe_btn"):
            with st.spinner("🎧 Converting your speech to text..."):
                transcript, error = transcribe_audio_hf(audio.getvalue())
            if transcript:
                st.session_state.voice_transcript = transcript
                st.session_state.voice_transcript_editor = transcript
                st.success("✅ Speech detected and transcribed.")
            else:
                st.error(f"❌ Could not transcribe this recording. {error or ''}".strip())
    with col3:
        if st.button("🧹 Clear Voice", use_container_width=True, key="voice_clear_btn"):
            st.session_state.voice_transcript = ""
            st.session_state.voice_transcript_editor = ""
            st.rerun()

    if "voice_transcript_editor" not in st.session_state:
        st.session_state.voice_transcript_editor = st.session_state.get("voice_transcript", "")

    transcript_value = st.text_area(
        "Transcript",
        placeholder="Your recorded question will appear here...",
        key="voice_transcript_editor",
        height=100,
    )
    st.session_state.voice_transcript = transcript_value

    if st.button("➤ Ask PhysIQ", use_container_width=True, key="voice_send_btn"):
        cleaned_transcript = normalize_voice_text(transcript_value)
        if cleaned_transcript:
            st.session_state._voice_question = cleaned_transcript
            st.session_state._is_voice_question = True
            st.session_state.voice_transcript = cleaned_transcript
            st.session_state.voice_clear_pending = True
            st.rerun()
        else:
            st.warning("Record something first, then transcribe it before sending.")

def inject_voice_chat_bridge(enabled):
    """Attach a browser mic button near the chat bar and speak replies aloud."""
    st.components.v1.html(f"""
<script>
(function() {{
  const enabled = {str(enabled).lower()};
  const SILENCE_MS = 2200;
  const parentWin = window.parent;
  const doc = parentWin.document;
  const bridge = parentWin.__physiqVoiceBridge = parentWin.__physiqVoiceBridge || {{}};

  function setButtonState(state, text, title) {{
    const btn = doc.getElementById("physiq-chat-mic-btn");
    if (!btn) return;
    btn.dataset.state = state;
    btn.textContent = text;
    btn.title = title;
    btn.style.background = state === "listening" ? "#d97706" : "#0ea5e9";
    btn.style.boxShadow = state === "listening"
      ? "0 0 0 6px rgba(217, 119, 6, 0.18)"
      : "0 10px 25px rgba(14, 165, 233, 0.26)";
  }}

  function speakText(text) {{
    const cleaned = String(text || "").replace(/[#*_`>-]/g, " ").replace(/\\s+/g, " ").trim();
    if (!cleaned || !("speechSynthesis" in parentWin)) return;
    parentWin.speechSynthesis.cancel();
    const utterance = new parentWin.SpeechSynthesisUtterance(cleaned);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;
    const voices = parentWin.speechSynthesis.getVoices();
    const preferred = voices.find(v => /en-IN|en-GB|en-US/i.test(v.lang || "")) || voices[0];
    if (preferred) utterance.voice = preferred;
    parentWin.speechSynthesis.speak(utterance);
  }}

  if (!bridge.ttsBound) {{
    bridge.ttsBound = true;
    bridge.speakText = speakText;
    parentWin.addEventListener("message", function(event) {{
      if (event.data && event.data.type === "physiq_tts" && event.data.text) {{
        speakText(event.data.text);
      }}
    }});
    if ("speechSynthesis" in parentWin) {{
      parentWin.speechSynthesis.onvoiceschanged = function() {{}};
      parentWin.speechSynthesis.getVoices();
    }}
  }}

  function clearSilenceTimer() {{
    if (bridge.silenceTimer) {{
      parentWin.clearTimeout(bridge.silenceTimer);
      bridge.silenceTimer = null;
    }}
  }}

  function sendTranscript(text) {{
    const finalText = String(text || "").replace(/\\s+/g, " ").trim();
    if (!finalText) {{
      setButtonState("idle", "🎙️", "Start voice input");
      return;
    }}
    clearSilenceTimer();
    setButtonState("sending", "⏳", "Sending your question...");
    const url = new URL(parentWin.location.href);
    url.searchParams.set("voice_text", finalText);
    url.searchParams.set("voice_nonce", String(Date.now()));
    parentWin.location.href = url.toString();
  }}

  function stopListening(sendNow) {{
    clearSilenceTimer();
    bridge.recognizing = false;
    bridge.stopRequested = true;
    if (bridge.recognition) {{
      try {{ bridge.recognition.stop(); }} catch (e) {{}}
    }}
    const finalText = [bridge.finalTranscript || "", bridge.interimTranscript || ""].join(" ").replace(/\\s+/g, " ").trim();
    bridge.finalTranscript = "";
    bridge.interimTranscript = "";
    if (sendNow && finalText) {{
      sendTranscript(finalText);
    }} else {{
      setButtonState("idle", "🎙️", "Start voice input");
    }}
  }}

  function resetSilenceTimer() {{
    clearSilenceTimer();
    bridge.silenceTimer = parentWin.setTimeout(function() {{
      stopListening(true);
    }}, SILENCE_MS);
  }}

  function recognitionCtor() {{
    return parentWin.SpeechRecognition || parentWin.webkitSpeechRecognition || window.SpeechRecognition || window.webkitSpeechRecognition;
  }}

  function startListening() {{
    const SpeechRecognition = recognitionCtor();
    if (!SpeechRecognition) {{
      setButtonState("error", "🚫", "Speech recognition is not supported in this browser");
      return;
    }}

    bridge.finalTranscript = "";
    bridge.interimTranscript = "";
    bridge.stopRequested = false;
    bridge.recognition = new SpeechRecognition();
    bridge.recognition.lang = "en-US";
    bridge.recognition.continuous = true;
    bridge.recognition.interimResults = true;
    bridge.recognition.maxAlternatives = 1;

    bridge.recognition.onstart = function() {{
      bridge.recognizing = true;
      setButtonState("listening", "🔴", "Listening... stop speaking for 2.2 seconds to send");
    }};

    bridge.recognition.onresult = function(event) {{
      let finals = bridge.finalTranscript || "";
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {{
        const result = event.results[i];
        const part = (result[0] && result[0].transcript) ? result[0].transcript : "";
        if (result.isFinal) {{
          finals += " " + part;
        }} else {{
          interim += " " + part;
        }}
      }}
      bridge.finalTranscript = finals.trim();
      bridge.interimTranscript = interim.trim();
      const heard = [bridge.finalTranscript, bridge.interimTranscript].join(" ").trim();
      setButtonState("listening", heard ? "🗣️" : "🔴", heard ? `Heard: ${{heard}}` : "Listening...");
      if (heard) resetSilenceTimer();
    }};

    bridge.recognition.onerror = function(event) {{
      bridge.recognizing = false;
      clearSilenceTimer();
      const msg = event && event.error ? String(event.error) : "voice error";
      setButtonState("error", "⚠️", `Microphone error: ${{msg}}`);
    }};

    bridge.recognition.onend = function() {{
      clearSilenceTimer();
      const heard = [bridge.finalTranscript || "", bridge.interimTranscript || ""].join(" ").trim();
      const shouldSend = !bridge.stopRequested && heard;
      bridge.recognizing = false;
      bridge.stopRequested = false;
      if (shouldSend) {{
        sendTranscript(heard);
      }} else {{
        setButtonState("idle", "🎙️", "Start voice input");
      }}
    }};

    try {{
      bridge.recognition.start();
    }} catch (error) {{
      bridge.recognizing = false;
      setButtonState("error", "⚠️", "Could not start microphone");
    }}
  }}

  function mountButton() {{
    const chatInput = doc.querySelector('[data-testid="stChatInput"]');
    const existing = doc.getElementById("physiq-chat-mic-btn");

    if (!enabled) {{
      if (existing) existing.remove();
      if (bridge.recognizing) stopListening(false);
      return;
    }}

    if (!chatInput) {{
      parentWin.setTimeout(mountButton, 400);
      return;
    }}

    const rect = chatInput.getBoundingClientRect();
    const bottom = Math.max(18, parentWin.innerHeight - rect.bottom + 14);
    const right = Math.max(84, parentWin.innerWidth - rect.right + 88);

    const btn = existing || doc.createElement("button");
    btn.id = "physiq-chat-mic-btn";
    btn.type = "button";
    btn.textContent = "🎙️";
    btn.title = "Start voice input";
    btn.onclick = function() {{
      if (bridge.recognizing) {{
        stopListening(true);
      }} else {{
        startListening();
      }}
    }};
    btn.style.position = "fixed";
    btn.style.right = `${{right}}px`;
    btn.style.bottom = `${{bottom}}px`;
    btn.style.width = "48px";
    btn.style.height = "48px";
    btn.style.borderRadius = "999px";
    btn.style.border = "none";
    btn.style.color = "#fff";
    btn.style.fontSize = "20px";
    btn.style.cursor = "pointer";
    btn.style.zIndex = "99999";
    btn.style.transition = "all 0.18s ease";
    btn.style.display = "flex";
    btn.style.alignItems = "center";
    btn.style.justifyContent = "center";
    btn.style.background = "#0ea5e9";
    btn.style.boxShadow = "0 10px 25px rgba(14, 165, 233, 0.26)";

    if (!existing) doc.body.appendChild(btn);
  }}

  mountButton();
  parentWin.setTimeout(mountButton, 900);
  parentWin.addEventListener("resize", mountButton);
}})();
</script>
""", height=0)




# ══════════════════════════════════════════════════════════════
#  IMAGE GENERATOR CONNECTOR
# ══════════════════════════════════════════════════════════════

IMAGE_TRIGGER_WORDS = [
    "generate an image", "create an image", "make an image",
    "draw", "generate a picture", "create a picture",
    "show me a picture", "show me an image", "visualise",
    "generate a photo", "create a photo", "make a photo",
    "render", "illustrate", "generate a diagram",
    "create a 3d", "make a 3d", "generate a 3d",
    "show me a 3d", "3d model of", "2d image of",
    "image of", "picture of", "photo of",
]

def is_image_request(message):
    msg = message.lower()
    return any(t in msg for t in IMAGE_TRIGGER_WORDS)

def build_image_prompt(user_request, context_answer=""):
    """Use AI to craft a perfect, detailed image generation prompt."""
    system = """You are a world-class AI image prompt engineer.
Given a user request, create the PERFECT image generation prompt for FLUX.1.
Your prompt must produce hyperrealistic, stunning, award-winning images.

Rules:
1. Start with the most important subject
2. Include: lighting, style, quality keywords, camera/perspective details
3. For 3D: add "hyperrealistic 3D render, octane render, physically based rendering, ray tracing, 8K, ultra detailed"
4. For scientific: add "scientific illustration, photorealistic, detailed, accurate, educational"
5. For diagrams: add "clean vector illustration, white background, professional, labeled"
6. ALWAYS end with: "sharp focus, high resolution, 8K UHD, masterpiece, best quality"
7. Keep prompt under 200 words
8. Return ONLY the prompt text, nothing else"""

    user = f"""User wants: {user_request}
Context (if any): {context_answer[:200] if context_answer else "none"}

Write the perfect image generation prompt:"""

    prompt = call_hf(system, user, max_tokens=250)
    return prompt.strip() if prompt else user_request

def generate_image_hf(prompt, width=1024, height=1024, model="flux"):
    """Generate image using Hugging Face text-to-image."""
    import base64
    import io
    from huggingface_hub import InferenceClient

    # Model options — FLUX.1-schnell is free and excellent
    models = {
        "flux":   "black-forest-labs/FLUX.1-schnell",
        "flux_dev": "black-forest-labs/FLUX.1-dev",
        "sdxl":   "stabilityai/stable-diffusion-xl-base-1.0",
        "sdxl_turbo": "stabilityai/sdxl-turbo",
    }
    model_order = [models.get(model, models["flux"]), models["sdxl"], models["sdxl_turbo"]]

    try:
        errors = []
        for model_id in model_order:
            try:
                client = InferenceClient(provider="hf-inference", api_key=HF_TOKEN, timeout=180)
                image = client.text_to_image(
                    prompt,
                    model=model_id,
                    width=width if "sdxl" not in model_id else min(width, 1024),
                    height=height if "sdxl" not in model_id else min(height, 1024),
                    num_inference_steps=4 if "FLUX.1-schnell" in model_id else 20,
                    guidance_scale=0.0 if "FLUX.1-schnell" in model_id else 7.5,
                )
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                return b64, None
            except Exception as model_error:
                errors.append(f"{model_id}: {str(model_error)[:140]}")
        return None, "Generation failed: " + " | ".join(errors[:3])
    except Exception as e:
        return None, f"Error: {str(e)[:100]}"

def detect_image_style(message):
    """Detect if user wants 2D, 3D, diagram, or photo."""
    msg = message.lower()
    if any(x in msg for x in ["3d","three d","three-d","render","hyperrealistic","photorealistic"]):
        return "3d", 1024, 1024
    elif any(x in msg for x in ["diagram","chart","schematic","blueprint","2d","flat","vector"]):
        return "diagram", 1024, 768
    elif any(x in msg for x in ["landscape","panorama","wide"]):
        return "landscape", 1280, 768
    elif any(x in msg for x in ["portrait","person","human","face"]):
        return "portrait", 768, 1024
    else:
        return "general", 1024, 1024

def enhance_prompt_for_style(prompt, style):
    """Add style-specific quality keywords."""
    style_suffixes = {
        "3d": ", hyperrealistic 3D render, octane render, physically based rendering, ray tracing, subsurface scattering, ultra detailed, photorealistic, 8K UHD, masterpiece, best quality, sharp focus, professional lighting, studio quality, highly detailed",
        "diagram": ", clean scientific illustration, precise, labeled, white background, professional diagram, vector style, educational, high resolution, sharp, clear",
        "landscape": ", epic landscape photography, golden hour lighting, ultra wide angle, 8K UHD, masterpiece, photorealistic, award winning photography, sharp focus, vivid colors",
        "portrait": ", portrait photography, professional lighting, bokeh background, 8K, photorealistic, ultra detailed skin texture, cinematic, high quality",
        "general": ", ultra detailed, photorealistic, 8K UHD, masterpiece, best quality, sharp focus, vivid colors, professional, award winning",
    }
    suffix = style_suffixes.get(style, style_suffixes["general"])
    # Avoid duplicate quality words
    if "8K" not in prompt and "masterpiece" not in prompt:
        return prompt + suffix
    return prompt

def show_generated_image(b64_image, prompt, style, user_question):
    """Display the generated image beautifully in Streamlit."""
    import base64
    try:
        img_data = base64.b64decode(b64_image)
    except Exception:
        st.error("❌ The generated image could not be decoded.")
        return

    st.image(img_data, use_container_width=True)

    # Action buttons below image
    col1, col2, col3 = st.columns(3)
    with col1:
        # Download button
        st.download_button(
            "⬇️ Download",
            data=img_data,
            file_name=f"physiq_{style}_{int(__import__('time').time())}.png",
            mime="image/png",
            use_container_width=True
        )
    with col2:
        if st.button("🎬 Animate This", key=f"anim_img_{hash(prompt)}", use_container_width=True):
            # Store image for animator
            st.session_state.animator_bg_image = b64_image
            st.session_state.animator_bg_prompt = prompt
            # Generate animation with image as background
            with st.spinner("🎬 Building animation..."):
                anim = generate_animation_script(user_question,
                    f"Create animation using this image as reference: {prompt[:100]}")
                if anim:
                    anim["bg_image_b64"] = b64_image
                    st.session_state.animation_data = anim
                    st.session_state.show_animator = True
                    st.rerun()
    with col3:
        if st.button("🔄 Regenerate", key=f"regen_{hash(prompt)}", use_container_width=True):
            st.session_state._regen_prompt = prompt
            st.session_state._regen_style = style
            st.session_state._regen_question = user_question
            st.rerun()

    # Show prompt used
    with st.expander("🔍 Prompt used"):
        st.code(prompt, language=None)

def handle_image_request(question, vs):
    """Full pipeline: detect → craft prompt → generate → display."""
    # Detect style and dimensions
    style, width, height = detect_image_style(question)

    # Get some context from knowledge base
    context = ""
    if vs:
        try:
            results = vs.similarity_search_with_score(question, k=2)
            context = results[0][0].page_content[:300] if results else ""
        except: pass

    # Build optimised prompt
    with st.spinner("🎨 Crafting the perfect prompt..."):
        raw_prompt = build_image_prompt(question, context)

    # Add quality enhancers
    final_prompt = enhance_prompt_for_style(raw_prompt, style)

    # Generate
    style_labels = {
        "3d": "⚡ Generating hyperrealistic 3D image with FLUX.1...",
        "diagram": "📐 Generating scientific diagram...",
        "landscape": "🌄 Generating landscape...",
        "portrait": "👤 Generating portrait...",
        "general": "🖼️ Generating image",
    }
    spinner_msg = style_labels.get(style, "🖼️ Generating image...")

    with st.spinner(spinner_msg):
        b64, error = generate_image_hf(final_prompt, width, height)

    if error:
        st.error(f"❌ {error}")
        st.info("💡 Tip: FLUX.1 model sometimes needs a moment to warm up. Try again in 30 seconds.")
        return None, final_prompt

    return b64, final_prompt


# ══════════════════════════════════════════════════════════════
#  USER PROFILE & PERSONALISATION SYSTEM
# ══════════════════════════════════════════════════════════════

def save_user_profile(profile_data):
    """Save analysed profile to Supabase."""
    try:
        import json
        get_authed_client().table("user_profiles").upsert({
            "user_id": get_user_id(),
            "profile_json": json.dumps(profile_data),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }, on_conflict="user_id").execute()
    except Exception as e:
        pass  # table may not exist yet, fail silently

def load_user_profile():
    """Load saved profile from Supabase."""
    try:
        import json
        res = get_authed_client().table("user_profiles").select("*").eq(
            "user_id", get_user_id()).execute()
        if res.data:
            return json.loads(res.data[0]["profile_json"])
    except:
        pass
    return None

def analyse_user_profile(messages, past_convos, quiz_mistakes):
    """Use AI to deeply analyse all user data and build a profile."""
    # Build a summary of all interactions
    recent_questions = [m["content"] for m in messages if m["role"]=="user"][-30:]
    past_questions = [p["content"] for p in past_convos if p.get("role")=="user"][-50:]
    all_questions = list(set(recent_questions + past_questions))

    mistake_topics = [m.get("topic","") for m in quiz_mistakes] if quiz_mistakes else []
    wrong_questions = [m.get("question","") for m in quiz_mistakes] if quiz_mistakes else []

    if len(all_questions) < 2:
        return None

    system = """You are an expert educational psychologist and learning analyst.
Analyse the student's conversation history, quiz mistakes, and question patterns.
Return ONLY a valid JSON object with this exact structure — no extra text:

{
  "weak_concepts": ["concept1", "concept2", "concept3"],
  "strong_concepts": ["concept1", "concept2", "concept3"],
  "favourite_topics": ["topic1", "topic2"],
  "learning_style": "Visual / Reading / Problem-solving / Conceptual",
  "preferred_detail_level": "Simple / Balanced / Detailed / Expert",
  "asking_pattern": "e.g. Asks short direct questions / Asks deep theoretical questions",
  "personality": "e.g. Curious and explorative / Goal-oriented / Creative",
  "how_to_reply": "e.g. Use analogies, keep it short, avoid jargon",
  "improvement_plan": ["tip1", "tip2", "tip3"],
  "strengths_summary": "One sentence about what they are best at",
  "weakness_summary": "One sentence about their main gap",
  "engagement_level": "High / Medium / Low",
  "topics_explored": ["topic1", "topic2", "topic3", "topic4", "topic5"],
  "recommended_next": ["topic1", "topic2", "topic3"]
}"""

    user = f"""Student's questions (most recent first):
{chr(10).join([f'- {q}' for q in all_questions[:40]])}

Quiz mistakes (topics where errors occurred):
{chr(10).join([f'- {t}: {q}' for t,q in zip(mistake_topics[:15], wrong_questions[:15])])}

Analyse this student deeply and return the JSON profile:"""

    import json
    raw = call_hf(system, user, max_tokens=800)
    if not raw:
        return None
    raw = raw.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1:
        return None
    try:
        return json.loads(raw[start:end])
    except:
        return None

def build_personalisation_context(profile):
    """Build a short context string to inject into every AI response."""
    if not profile:
        return ""
    style = profile.get("how_to_reply", "")
    level = profile.get("preferred_detail_level", "Balanced")
    personality = profile.get("personality", "")
    weak = profile.get("weak_concepts", [])
    strong = profile.get("strong_concepts", [])
    context = f"""\n\n[STUDENT PROFILE — adjust your response accordingly:
- Detail level: {level}
- How they like replies: {style}
- Personality: {personality}
- Strong in: {", ".join(strong[:3]) if strong else "general"}
- Needs help with: {", ".join(weak[:3]) if weak else "varies"}
Always match your tone and depth to this profile.]"""
    return context

def show_profile_page():
    """Render the full user profile dashboard."""
    profile = st.session_state.get("user_profile")
    user_name = st.session_state.user.user_metadata.get("full_name", "Student")
    dark = st.session_state.dark_mode
    bg2  = "#161b22" if dark else "#ffffff"
    acc  = "#58a6ff"
    grn  = "#3fb950"
    red  = "#f85149"
    yel  = "#d29922"

    st.markdown(f"## 👤 {user_name}'s Learning Profile")
    st.caption("Automatically generated from your conversations and quiz history")

    col_refresh, col_back = st.columns([1,4])
    with col_refresh:
        if st.button("🔄 Refresh Profile", use_container_width=True):
            with st.spinner("🧠 Analysing your learning history..."):
                msgs = st.session_state.get("messages",[])
                past = load_past_conversations()
                mistakes = load_quiz_mistakes()
                new_profile = analyse_user_profile(msgs, past, mistakes)
                if new_profile:
                    st.session_state.user_profile = new_profile
                    save_user_profile(new_profile)
                    st.success("✅ Profile updated!")
                    st.rerun()
                else:
                    st.warning("Not enough conversation data yet. Ask more questions first!")
    with col_back:
        if st.button("← Back to Chat", use_container_width=True):
            st.session_state.show_profile = False
            st.rerun()

    if not profile:
        # Try loading from Supabase
        saved = load_user_profile()
        if saved:
            st.session_state.user_profile = saved
            profile = saved
        else:
            st.info("📊 No profile yet! Ask some questions in the chat first, then click 🔄 Refresh Profile")
            st.markdown("""
            **The profile will show:**
            - 🔴 Topics where you need improvement
            - 🟢 Topics where you are strong
            - ❤️ Your favourite subjects
            - 🎯 How the AI should talk to you
            - 📈 A personalised improvement plan
            """)
            return

    # ── Score cards ───────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        (c1, "🏆 Strengths", len(profile.get("strong_concepts",[])), grn),
        (c2, "📚 Topics Done", len(profile.get("topics_explored",[])), acc),
        (c3, "⚠️ Weak Areas", len(profile.get("weak_concepts",[])), red),
        (c4, "🎯 Engagement", profile.get("engagement_level","?"), yel),
    ]
    for col, label, val, color in metrics:
        with col:
            st.markdown(f"""
            <div style="background:{bg2};border:1px solid {color}30;border-left:4px solid {color};
            border-radius:10px;padding:14px 16px;text-align:center;margin-bottom:8px">
                <div style="color:{color};font-size:0.8rem;font-weight:600;margin-bottom:4px">{label}</div>
                <div style="color:#e6edf3;font-size:1.6rem;font-weight:700">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Two column layout ─────────────────────────────────────
    left, right = st.columns(2)

    with left:
        # Strong concepts
        strong = profile.get("strong_concepts", [])
        if strong:
            st.markdown(f"### 🟢 You're Great At")
            for s in strong:
                st.markdown(f"""<div style="background:{bg2};border:1px solid {grn}40;border-radius:8px;
                padding:8px 14px;margin:4px 0;color:#e6edf3;font-size:13px">
                ✅ {s}</div>""", unsafe_allow_html=True)
        st.markdown("")

        # Favourite topics
        favs = profile.get("favourite_topics", [])
        if favs:
            st.markdown(f"### ❤️ Favourite Topics")
            for f2 in favs:
                st.markdown(f"""<div style="background:{bg2};border:1px solid {acc}40;border-radius:8px;
                padding:8px 14px;margin:4px 0;color:#e6edf3;font-size:13px">
                ❤️ {f2}</div>""", unsafe_allow_html=True)

    with right:
        # Weak concepts
        weak = profile.get("weak_concepts", [])
        if weak:
            st.markdown(f"### 🔴 Needs Improvement")
            for w in weak:
                st.markdown(f"""<div style="background:{bg2};border:1px solid {red}40;border-radius:8px;
                padding:8px 14px;margin:4px 0;color:#e6edf3;font-size:13px">
                ⚠️ {w}</div>""", unsafe_allow_html=True)
        st.markdown("")

        # Topics explored
        explored = profile.get("topics_explored", [])
        if explored:
            st.markdown(f"### 🗺️ Topics Explored")
            for t in explored[:6]:
                st.markdown(f"""<div style="background:{bg2};border:1px solid #30363d;border-radius:8px;
                padding:8px 14px;margin:4px 0;color:#8b949e;font-size:12px">
                📖 {t}</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Learning style card ───────────────────────────────────
    st.markdown("### 🧠 Your Learning DNA")
    dna1, dna2 = st.columns(2)
    with dna1:
        style_items = [
            ("Learning Style", profile.get("learning_style","?"), "🎓"),
            ("Detail Level", profile.get("preferred_detail_level","?"), "📏"),
            ("Asking Pattern", profile.get("asking_pattern","?"), "💬"),
            ("Personality", profile.get("personality","?"), "🌟"),
            ("Engagement", profile.get("engagement_level","?"), "⚡"),
        ]
        for label, val, icon in style_items:
            st.markdown(f"""<div style="background:{bg2};border:1px solid #30363d;border-radius:10px;
            padding:12px 16px;margin:6px 0;display:flex;align-items:center;gap:12px">
            <span style="font-size:1.3rem">{icon}</span>
            <div><div style="color:#8b949e;font-size:10px;font-weight:600;letter-spacing:1px">{label.upper()}</div>
            <div style="color:#e6edf3;font-size:13px;font-weight:500">{val}</div></div>
            </div>""", unsafe_allow_html=True)

    with dna2:
        # How AI talks to this user
        how = profile.get("how_to_reply","")
        if how:
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1f6feb20,#388bfd10);
            border:1px solid {acc}40;border-radius:12px;padding:16px;margin-bottom:10px">
            <div style="color:{acc};font-weight:700;margin-bottom:8px;font-size:13px">🤖 How PhysIQ Talks to You</div>
            <div style="color:#e6edf3;font-size:13px;line-height:1.6">{how}</div>
            </div>""", unsafe_allow_html=True)

        # Summaries
        s_sum = profile.get("strengths_summary","")
        w_sum = profile.get("weakness_summary","")
        if s_sum:
            st.markdown(f"""<div style="background:{bg2};border:1px solid {grn}40;border-radius:10px;
            padding:12px 16px;margin:6px 0">
            <div style="color:{grn};font-size:11px;font-weight:700;margin-bottom:4px">YOUR STRENGTH</div>
            <div style="color:#e6edf3;font-size:12px">{s_sum}</div>
            </div>""", unsafe_allow_html=True)
        if w_sum:
            st.markdown(f"""<div style="background:{bg2};border:1px solid {red}40;border-radius:10px;
            padding:12px 16px;margin:6px 0">
            <div style="color:{red};font-size:11px;font-weight:700;margin-bottom:4px">YOUR MAIN GAP</div>
            <div style="color:#e6edf3;font-size:12px">{w_sum}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Improvement plan ─────────────────────────────────────
    plan = profile.get("improvement_plan", [])
    rec  = profile.get("recommended_next", [])
    if plan:
        st.markdown("### 📈 Your Personalised Improvement Plan")
        for i, tip in enumerate(plan, 1):
            st.markdown(f"""<div style="background:{bg2};border:1px solid #30363d;border-left:4px solid {acc};
            border-radius:10px;padding:12px 16px;margin:6px 0;color:#e6edf3;font-size:13px">
            <span style="color:{acc};font-weight:700">Step {i}:</span> {tip}
            </div>""", unsafe_allow_html=True)

    if rec:
        st.markdown("### 🎯 What to Study Next")
        cols_rec = st.columns(min(len(rec), 3))
        for i, topic in enumerate(rec[:3]):
            with cols_rec[i]:
                if st.button(f"📖 {topic}", use_container_width=True, key=f"rec_{i}"):
                    st.session_state.show_profile = False
                    st.session_state.messages.append({
                        "role":"user","content":f"Teach me about {topic}"
                    })
                    st.rerun()

    st.markdown("---")
    st.caption("Profile is rebuilt whenever you click 🔄 Refresh Profile. The more you use PhysIQ, the more accurate it gets!")



# ══════════════════════════════════════════════════════════════
#  WEB SEARCH CONNECTOR
#  Free APIs only: Wikipedia, arXiv, OpenLibrary, DuckDuckGo
#  All free for commercial use, no API keys required
# ══════════════════════════════════════════════════════════════

import re as _re

WEB_SEARCH_TRIGGERS = [
    "search for","look up","find information","what is the latest",
    "current","recent","news about","search the web","look online",
    "find out","google","web search","search online","what happened",
    "today","2024","2025","latest research","recent study","new paper",
    "who is","where is","when did","how many","what country",
]

def needs_web_search(question, confidence_class):
    """Decide if web search would help."""
    msg = question.lower()
    low_conf = confidence_class in ["conf-low","conf-med"]
    has_trigger = any(t in msg for t in WEB_SEARCH_TRIGGERS)
    is_factual = any(x in msg for x in ["who","what","when","where","how many","which","list of"])
    return (low_conf and is_factual) or has_trigger

def search_wikipedia(query, sentences=4):
    """Search Wikipedia — completely free, no key needed."""
    try:
        import urllib.request, urllib.parse, json
        q = urllib.parse.quote(query)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}"
        req = urllib.request.Request(url, headers={"User-Agent":"PhysIQ/1.0 (educational)"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        if data.get("type") == "disambiguation":
            return None
        extract = data.get("extract","")
        # Return first N sentences
        sents = extract.split(". ")
        return ". ".join(sents[:sentences]) + ("." if len(sents)>sentences else "")
    except:
        return None

def search_arxiv(query, max_results=3):
    """Search arXiv for scientific papers — completely free."""
    try:
        import urllib.request, urllib.parse
        q = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={max_results}&sortBy=relevance"
        req = urllib.request.Request(url, headers={"User-Agent":"PhysIQ/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            xml = r.read().decode("utf-8")
        # Parse entries
        titles = _re.findall(r'<title>(.*?)</title>', xml)[1:]  # skip feed title
        summaries = _re.findall(r'<summary>(.*?)</summary>', xml, _re.DOTALL)
        results = []
        for i, (t, s) in enumerate(zip(titles[:max_results], summaries[:max_results])):
            t = t.strip().replace("\n"," ")
            s = s.strip().replace("\n"," ")[:200]
            results.append(f"📄 **{t}**: {s}...")
        return results if results else None
    except:
        return None

def search_duckduckgo(query):
    """DuckDuckGo Instant Answer API — free, no key, good for facts."""
    try:
        import urllib.request, urllib.parse, json
        q = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={q}&format=json&no_redirect=1&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={"User-Agent":"PhysIQ/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        abstract = data.get("AbstractText","").strip()
        answer = data.get("Answer","").strip()
        definition = data.get("Definition","").strip()
        related = [t.get("Text","") for t in data.get("RelatedTopics",[])[:2] if t.get("Text")]
        result = answer or abstract or definition
        if result:
            return result + (" | " + " | ".join(related) if related else "")
        return None
    except:
        return None

def search_openlibrary(query):
    """Open Library search — free, great for book/author queries."""
    try:
        import urllib.request, urllib.parse, json
        q = urllib.parse.quote(query)
        url = f"https://openlibrary.org/search.json?q={q}&limit=3&fields=title,author_name,first_publish_year,subject"
        req = urllib.request.Request(url, headers={"User-Agent":"PhysIQ/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        docs = data.get("docs",[])[:3]
        results = []
        for d in docs:
            t = d.get("title","?")
            a = ", ".join(d.get("author_name",["Unknown"])[:2])
            y = d.get("first_publish_year","")
            results.append(f"📚 *{t}* by {a} ({y})")
        return results if results else None
    except:
        return None

def web_search_all(query):
    """Run all free searches and compile results."""
    results = {}
    # Wikipedia (most reliable for facts)
    wiki = search_wikipedia(query)
    if wiki: results["Wikipedia"] = wiki
    # DuckDuckGo instant answers
    ddg = search_duckduckgo(query)
    if ddg: results["DuckDuckGo"] = ddg
    # arXiv for science topics
    sci_words = ["physics","chemistry","quantum","atom","molecule","theorem",
                 "research","paper","study","formula","equation","theory"]
    if any(w in query.lower() for w in sci_words):
        arxiv = search_arxiv(query)
        if arxiv: results["arXiv"] = arxiv
    # Open Library for books/authors
    book_words = ["book","author","novel","written by","publication","published"]
    if any(w in query.lower() for w in book_words):
        books = search_openlibrary(query)
        if books: results["Open Library"] = books
    return results

def format_web_results(results):
    """Format search results into readable text for AI context."""
    if not results:
        return ""
    lines = ["\n[WEB SEARCH RESULTS — use these to enrich your answer:]"]
    for source, data in results.items():
        lines.append(f"\n📡 {source}:")
        if isinstance(data, list):
            for item in data:
                lines.append(f"  • {item}")
        else:
            lines.append(f"  {data}")
    lines.append("[End of web results]\n")
    return "\n".join(lines)

def answer_with_web_search(question, vs, history_text):
    """Ask question WITH web search context added."""
    # Run web searches
    web_results = web_search_all(question)
    web_context = format_web_results(web_results)
    # Also get RAG context
    rag_context = ""
    if vs:
        try:
            results = vs.similarity_search_with_score(question, k=3)
            rag_context = "\n\n".join([r[0].page_content for r in results])
        except: pass
    system = """You are an expert tutor with access to live web search results.
Use BOTH your knowledge AND the web search results to give the most accurate, up-to-date answer.
Always mention if information comes from a web source.
Be accurate, clear and educational."""
    user = f"""Context from knowledge base:
{rag_context}

{web_context}

Conversation:
{history_text}

Question: {question}

Answer (use web results where relevant):"""
    answer = call_hf(system, user, max_tokens=1500)
    sources = list(web_results.keys()) if web_results else []
    return answer, sources


# ══════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════
def show_app():
    consume_browser_voice_query()
    user_name = st.session_state.user.user_metadata.get("full_name", st.session_state.user.email)

    # ── Load backend ───────────────────────────────────────────
    if not st.session_state.backend_ready:
        if not os.path.exists("./physics_index"):
            st.warning("⚠️ physics_index not found locally. The chatbot will work without RAG context.")
            # Create a dummy vectorstore so app doesn't crash
            st.session_state.vs = None
            st.session_state.Document = None
            st.session_state.backend_ready = True
            st.rerun()
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
            st.error(f"❌ {e}")
            st.stop()

    vs       = st.session_state.vs
    Document = st.session_state.Document

    if st.session_state.get("show_profile"):
        show_profile_page()
        return

    # ── SIDEBAR ────────────────────────────────────────────────
    with st.sidebar:
        # Theme toggle
        col_name, col_theme = st.columns([3,1])
        with col_name:
            st.markdown(f"**👋 {user_name}**")
            st.caption(st.session_state.user.email)
        with col_theme:
            if st.button("🌙" if st.session_state.dark_mode else "☀️", help="Toggle theme"):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()

        col_prof, col_out = st.columns(2)
        with col_prof:
            if st.button("👤 My Profile", use_container_width=True):
                st.session_state.show_profile = True
                # Auto-load saved profile
                if not st.session_state.user_profile:
                    saved = load_user_profile()
                    if saved:
                        st.session_state.user_profile = saved
                st.rerun()
        with col_out:
            pass
        if st.button("🚪 Sign Out", use_container_width=True):
            supabase.auth.sign_out()
            clear_session_from_js()
            for k in ["user","access_token","messages","pending_feedback","backend_ready","vs","Document"]:
                st.session_state[k] = None if k in ["user","access_token"] else \
                                      [] if k=="messages" else \
                                      False if k=="backend_ready" else None
            st.session_state.show_landing = True
            st.rerun()

        st.divider()

        # ── Numerical Solver Panel ─────────────────────────────
        # ── Creative Mode Toggle ───────────────────────────────
        st.markdown('<div class="section-label">🎛️ Mode Select</div>', unsafe_allow_html=True)
        voice_on = st.toggle("🎙️ Voice Mode", value=st.session_state.voice_mode,
            help="Speak your question, hear the answer")
        if voice_on != st.session_state.voice_mode:
            st.session_state.voice_mode = voice_on
            st.rerun()
        creative_on = st.toggle("✍️ Creative/English Mode", value=st.session_state.creative_mode,
            help="Essays, debates, letters, stories, poems")
        if creative_on != st.session_state.creative_mode:
            st.session_state.creative_mode = creative_on
            if creative_on: st.session_state.coding_mode = False
            st.rerun()

        coding_on = st.toggle("💻 Coding Mode", value=st.session_state.coding_mode,
            help="Python, Java, C++, C#, Roblox Lua, JS and more")
        if coding_on != st.session_state.coding_mode:
            st.session_state.coding_mode = coding_on
            if coding_on: st.session_state.creative_mode = False
            st.rerun()

        web_on = st.toggle("🌐 Web Search", value=st.session_state.get("web_search_mode",False),
            help="Auto-searches Wikipedia, arXiv, DuckDuckGo for extra info")
        if web_on != st.session_state.get("web_search_mode",False):
            st.session_state.web_search_mode = web_on
            st.rerun()

        if st.session_state.creative_mode:
            st.success("✍️ English/Creative Mode ON")
        elif st.session_state.coding_mode:
            st.success("💻 Coding Mode ON — Up to 2000 lines!")
        else:
            st.info("⚛️ Science Mode")
        if st.session_state.get("web_search_mode"):
            st.success("🌐 Web Search ON — Wikipedia, arXiv, DuckDuckGo active")

        st.divider()
        st.markdown('<div class="section-label">🔢 Numerical Solver</div>', unsafe_allow_html=True)
        st.caption("Paste any numerical problem for full step-by-step solution")
        num_problem = st.text_area("Problem:", placeholder="e.g. A ball is thrown with velocity 20 m/s at 30°. Find max height.", height=100, key="num_input", label_visibility="collapsed")
        if st.button("Solve Step-by-Step →", use_container_width=True):
            if num_problem.strip():
                with st.spinner("🔢 Solving..."):
                    result = solve_numerical(num_problem.strip(), vs)
                    st.session_state.solver_result = result
                    st.rerun()

        if st.session_state.solver_result:
            st.markdown('<div class="section-label">📋 Solution</div>', unsafe_allow_html=True)
            with st.expander("View Full Solution", expanded=True):
                st.markdown(st.session_state.solver_result)
            if st.button("Clear Solution"):
                st.session_state.solver_result = None
                st.rerun()

        st.divider()

        # ── Learned answers ────────────────────────────────────
        st.markdown('<div class="section-label">🧠 Learned Answers</div>', unsafe_allow_html=True)
        learned = load_learned()
        if not learned:
            st.caption("Nothing saved yet.")
        else:
            st.caption(f"✅ {len(learned)} answers saved")
            for e in learned[-3:]:
                with st.expander(f"{e['question'][:35]}..."):
                    st.write(e["answer"][:150])

        st.divider()

        # ── Past conversations ─────────────────────────────────
        st.markdown('<div class="section-label">💬 History</div>', unsafe_allow_html=True)
        past = load_past_conversations()
        if not past:
            st.caption("No history yet.")
        else:
            st.caption(f"💬 {len(past)} messages saved")
            user_msgs = [p for p in past if p["role"] == "user"]
            for p in user_msgs[-3:]:
                with st.expander(f"📅 {p['created_at'][:10]}: {p['content'][:30]}..."):
                    st.write(p["content"])

        st.divider()
        # ── PDF Reader ──────────────────────────────────────
        st.divider()
        st.markdown('<div class="section-label">📄 PDF Reader</div>', unsafe_allow_html=True)
        uploaded_pdf = st.file_uploader("Upload a PDF", type="pdf", key="pdf_upload",
            label_visibility="collapsed")
        if uploaded_pdf:
            if st.button("📖 Summarise PDF", use_container_width=True):
                with st.spinner("📖 Reading PDF..."):
                    pdf_text = extract_pdf_text(uploaded_pdf)
                if pdf_text:
                    summary = summarise_pdf(pdf_text)
                    if summary:
                        st.session_state.pdf_text = pdf_text
                        st.session_state.pdf_name = uploaded_pdf.name
                        reply = f"📄 **Summary of {uploaded_pdf.name}:**\n\n{summary}"
                        st.session_state.messages.append({"role":"assistant","content":reply})
                        st.rerun()
                else:
                    st.error("Could not read PDF. Make sure it contains text (not scanned images).")
            if st.session_state.get("pdf_text"):
                st.success(f"✅ {st.session_state.get('pdf_name','PDF')} loaded — ask questions about it!")

        # Past mistakes
        past_mistakes = load_quiz_mistakes()
        if past_mistakes:
            st.divider()
            st.markdown('<div class="section-label">📊 Quiz Mistakes</div>', unsafe_allow_html=True)
            st.caption(f"📝 {len(past_mistakes)} past mistakes recorded")
            if st.button("🎓 Get Lesson on Mistakes", use_container_width=True, key="lesson_btn"):
                with st.spinner("Generating lesson..."):
                    lesson = generate_mistake_lesson(past_mistakes)
                if lesson:
                    st.session_state.messages.append({"role":"assistant","content":"**📚 Personalised Lesson based on your quiz history:**\n\n"+lesson})
                    st.rerun()

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.pending_feedback = None
                st.session_state.simplify_target  = None
                st.rerun()
        with c2:
            if st.button("🗑️ Data", use_container_width=True):
                delete_all_data()
                st.toast("All data deleted.")
                st.rerun()

    # ── MAIN AREA ──────────────────────────────────────────────
    col_title, col_tog = st.columns([5,1])
    with col_title:
        st.markdown("## ⚛️ PhysIQ")
        st.caption("Physics · Chemistry · English Writing · Class 10 to College")
    with col_tog:
        st.write("")  # spacer

    inject_voice_chat_bridge(st.session_state.get("voice_mode", False))
    if st.session_state.get("voice_mode"):
        st.caption("Use the mic button beside the chat bar. After 2.2 seconds of silence, your question sends automatically and the reply is spoken aloud.")

    # ── Chat history ───────────────────────────────────────────
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            if msg.get("is_image") and msg.get("b64"):
                try:
                    import base64
                    img_bytes = base64.b64decode(msg["b64"])
                    st.image(img_bytes, use_container_width=True)
                except Exception:
                    st.warning("This saved image could not be displayed.")
            st.write(msg["content"])

            if msg["role"] == "assistant":
                # Confidence badge
                conf = msg.get("confidence","")
                cls  = msg.get("conf_class","conf-med")
                if conf:
                    st.markdown(f'<span class="{cls}">📊 {conf}</span>', unsafe_allow_html=True)

                # Explain Simply button (only on last assistant message)
                if i == len(st.session_state.messages) - 1:
                    b1, b2, b3 = st.columns([1, 1, 3])
                    with b1:
                        if st.button("🗣️ Explain Simply", key=f"simple_{i}"):
                            st.session_state.simplify_target = {
                                "answer": msg["content"],
                                "question": st.session_state.messages[i-1]["content"] if i > 0 else ""
                            }
                            st.session_state.show_animator = False
                            st.rerun()
                    with b2:
                        if st.button("🎬 Animated Teaching", key=f"anim_{i}"):
                            q = st.session_state.messages[i-1]["content"] if i > 0 else ""
                            with st.spinner("🎬 Generating animation..."):
                                anim = generate_animation_script(q, msg["content"])
                                if anim:
                                    st.session_state.animation_data = anim
                                    st.session_state.show_animator = True
                                    st.session_state.simplify_target = None
                                else:
                                    st.warning("Could not generate animation for this topic.")
                            st.rerun()

            # Show simple explanation if triggered for this message
            if msg["role"] == "assistant" and i == len(st.session_state.messages) - 1:
                if st.session_state.simplify_target:
                    st.divider()
                    with st.spinner("🗣️ Making it simpler..."):
                        simple = explain_simply(
                            st.session_state.simplify_target["answer"],
                            st.session_state.simplify_target["question"]
                        )
                    if simple:
                        st.markdown("**🗣️ Simple Explanation:**")
                        st.info(simple)
                    col_ok, col_cl = st.columns([1,4])
                    with col_ok:
                        if st.button("✅ Got it!", key="got_it"):
                            st.session_state.simplify_target = None
                            st.rerun()

    # ── Quiz Panel ─────────────────────────────────────────────
    if st.session_state.get("quiz_active") and st.session_state.get("quiz_state"):
        col_qt, col_qc = st.columns([5,1])
        with col_qt:
            st.markdown("**🎯 Quiz Connector**")
        with col_qc:
            if st.button("✕ Exit Quiz", key="exit_quiz"):
                st.session_state.quiz_active = False
                st.session_state.quiz_state = None
                st.rerun()
        show_quiz_ui()

    # ── Animated Teaching Panel ───────────────────────────────
    if st.session_state.get("show_animator") and st.session_state.get("animation_data"):
        st.divider()
        col_at, col_cl = st.columns([5,1])
        with col_at:
            atype = st.session_state.animation_data.get("type","").upper()
            st.markdown(f"**🎬 Animated Teaching — {atype} Animation**")
        with col_cl:
            if st.button("✕ Close", key="close_anim"):
                st.session_state.show_animator = False
                st.rerun()
        if not os.path.exists("animator.html"):
            st.error("❌ animator.html not found! Make sure it is in your physics-chatbot folder.")
        else:
            show_animator_panel(st.session_state.animation_data)

    # ── Feedback ───────────────────────────────────────────────
    if st.session_state.pending_feedback and not st.session_state.simplify_target:
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
                st.toast("✅ Saved to your knowledge base!")
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
                    st.toast("🧠 Correction saved!")
                    st.rerun()

    # ── Chat input ─────────────────────────────────────────────
    voice_q = st.session_state.pop("_voice_question", None)
    if voice_q:
        question = normalize_voice_text(voice_q)
    else:
        question = st.chat_input("Ask about Physics, Chemistry, or English Writing...")

    if question:
        st.session_state.simplify_target = None

        # ── Voice question flag ──────────────────────────────
        is_voice_q = st.session_state.get("_is_voice_question", False)
        if is_voice_q:
            st.session_state._is_voice_question = False

        # ── Auto-update profile every 20 messages ───────────
        if len(st.session_state.messages) % 20 == 0 and len(st.session_state.messages) > 0:
            import threading
            def bg_profile():
                try:
                    past = load_past_conversations()
                    mistakes = load_quiz_mistakes()
                    p = analyse_user_profile(st.session_state.messages, past, mistakes)
                    if p:
                        st.session_state.user_profile = p
                        save_user_profile(p)
                except: pass
            threading.Thread(target=bg_profile, daemon=True).start()

        # ── PDF question ─────────────────────────────────────
        if st.session_state.get("pdf_text"):
            pdf_keywords = ["in the pdf","from the pdf","the document","the pdf","page","according to","it says","uploaded"]
            if any(k in question.lower() for k in pdf_keywords):
                st.session_state.messages.append({"role":"user","content":question})
                save_message("user", question)
                with st.chat_message("user"):
                    st.write(question)
                with st.chat_message("assistant"):
                    with st.spinner("📄 Reading PDF to answer..."):
                        pdf_ans = answer_from_pdf(st.session_state.pdf_text, question)
                    if pdf_ans:
                        st.markdown(pdf_ans)
                        st.session_state.messages.append({"role":"assistant","content":pdf_ans,
                            "confidence":"📄 PDF Answer","conf_class":"conf-high"})
                        save_message("assistant", pdf_ans, "pdf")
                st.rerun()

        # ── Image generation request ─────────────────────────
        if is_image_request(question) or st.session_state.get("_regen_prompt"):
            regen = st.session_state.get("_regen_prompt")
            regen_style = st.session_state.get("_regen_style", "general")
            regen_q = st.session_state.get("_regen_question", question)
            if regen:
                st.session_state._regen_prompt = None
                st.session_state._regen_style = None
                st.session_state._regen_question = None
                # Re-generate with same prompt
                act_question = regen_q
                st.session_state.messages.append({"role":"user","content":f"[Regenerate] {regen_q}"})
                save_message("user", f"[Regenerate] {regen_q}")
                with st.chat_message("user"):
                    st.write(f"🔄 Regenerating: {regen_q}")
                with st.chat_message("assistant"):
                    style, w, h = detect_image_style(regen_q)
                    final_p = enhance_prompt_for_style(regen, style)
                    with st.spinner("🖼️ Regenerating image..."):
                        b64, err = generate_image_hf(final_p, w, h)
                    if b64:
                        show_generated_image(b64, final_p, style, regen_q)
                        reply = f"🎨 Regenerated! Style: **{style.upper()}** | Resolution: {w}×{h}px"
                        st.session_state.messages.append({"role":"assistant","content":reply,"is_image":True,"b64":b64})
                        save_message("assistant", reply)
                    else:
                        st.error(f"❌ {err}")
                st.rerun()
            else:
                st.session_state.messages.append({"role":"user","content":question})
                save_message("user", question)
                with st.chat_message("user"):
                    st.write(question)
                with st.chat_message("assistant"):
                    b64, final_prompt = handle_image_request(question, vs)
                    if b64:
                        show_generated_image(b64, final_prompt, detect_image_style(question)[0], question)
                        _, w, h = detect_image_style(question)
                        style = detect_image_style(question)[0]
                        reply = f"🎨 Generated! Style: **{style.upper()}** | Resolution: {w}×{h}px using FLUX.1"
                        st.session_state.messages.append({
                            "role":"assistant","content":reply,
                            "is_image":True,"b64":b64,"prompt":final_prompt
                        })
                        save_message("assistant", reply)
                st.rerun()

        # ── Detect quiz request ───────────────────────────────
        if is_quiz_request(question):
            st.session_state.messages.append({"role": "user", "content": question})
            save_message("user", question)
            with st.chat_message("user"):
                st.write(question)
            q_type, num_q = extract_quiz_topic(question)
            topic = question.lower()
            for word in QUIZ_TRIGGER_WORDS:
                topic = topic.replace(word,"").strip()
            topic = topic.strip(" on about:,") or "Physics and Chemistry"
            with st.chat_message("assistant"):
                with st.spinner(f"📝 Generating {num_q}-question quiz on {topic}..."):
                    questions = generate_quiz(topic, q_type, num_q)
                if questions:
                    reply = f"I have generated a {num_q}-question quiz on {topic}! The quiz is open below. Good luck!"
                    st.write(reply)
                    st.session_state.messages.append({"role":"assistant","content":reply})
                    save_message("assistant", reply)
                    st.session_state.quiz_state = {
                        "questions": questions, "current_idx": 0, "score": 0,
                        "answers": {}, "skipped": [], "phase": "quiz",
                        "topic": topic, "last_correct": None
                    }
                    st.session_state.quiz_active = True
                else:
                    st.error("Could not generate quiz. Please try again with a specific topic.")
            st.rerun()
        else:
            # ── Coding request ────────────────────────────────
            if is_coding_request(question):
                lang = detect_language(question)
                st.session_state.messages.append({"role": "user", "content": question})
                save_message("user", question)
                with st.chat_message("user"):
                    st.write(question)
                with st.chat_message("assistant"):
                    with st.spinner(f"💻 Writing {lang} code (up to 2000 lines)..."):
                        code_answer = generate_code(question, vs, lang)
                    if code_answer:
                        st.markdown(code_answer)
                        st.session_state.messages.append({
                            "role":"assistant","content":code_answer,
                            "confidence":"💻 Code","conf_class":"conf-high"
                        })
                        save_message("assistant", code_answer, "code")
                        st.session_state.pending_feedback = {"question":question,"answer":code_answer}
                st.rerun()
            else:
                # ── Normal question ─────────────────────────────
                st.session_state.messages.append({"role": "user", "content": question})
        save_message("user", question)

        with st.chat_message("user"):
            st.write(question)

        history_text = "\n".join([
            f"{'Student' if m['role']=='user' else 'Tutor'}: {m['content']}"
            for m in st.session_state.messages[-6:]
        ])

        with st.chat_message("assistant"):
            use_web = st.session_state.get("web_search_mode", False)
            with st.spinner("🔁 Thinking..." + (" + 🌐 searching web..." if use_web else "")):
                if use_web:
                    answer, sources = answer_with_web_search(question, vs, history_text)
                    conf_label = "🌐 Web + AI"
                    conf_class = "conf-high"
                    if not answer:
                        answer, conf_label, conf_class = ask_question(question, vs, history_text)
                        sources = []
                else:
                    answer, conf_label, conf_class = ask_question(question, vs, history_text)
                    sources = []
                    # Auto web search on low confidence
                    if conf_class == "conf-low" and needs_web_search(question, conf_class):
                        with st.spinner("🌐 Confidence low — checking web..."):
                            web_r = web_search_all(question)
                            if web_r:
                                web_ctx = format_web_results(web_r)
                                sources = list(web_r.keys())
                                # Re-ask with web context
                                sys2 = "You are an expert tutor. Use the web results to improve your answer."
                                usr2 = f"Web results:{web_ctx}\nQuestion:{question}\nImprove this answer:{answer}"
                                better = call_hf(sys2, usr2, max_tokens=1200)
                                if better: answer = better; conf_label = "🌐 Web-enhanced"
                st.write(answer)
                if sources:
                    st.caption(f"📡 Sources: {', '.join(sources)}")
                st.markdown(f'<span class="{conf_class}">📊 {conf_label}</span>', unsafe_allow_html=True)

                st.session_state.messages.append({
                    "role": "assistant", "content": answer,
                    "confidence": conf_label, "conf_class": conf_class
                })
                save_message("assistant", answer, conf_label)
                st.session_state.pending_feedback = {"question": question, "answer": answer}

                # TTS voice reply if voice mode on
                if st.session_state.get("voice_mode"):
                    with st.spinner("🔊 Preparing voice..."):
                        short = generate_voice_answer(question, answer)
                    if short:
                        st.components.v1.html(f"""<script>
setTimeout(()=>{{window.parent.postMessage({{type:'physiq_tts',text:{repr(short)}}}, '*');}},400);
</script>""", height=0)

        st.rerun()

# ══════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════
if st.session_state.user is None or st.session_state.show_landing:
    show_landing()
else:
    show_app()
