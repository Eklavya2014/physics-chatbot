import streamlit as st
import os
import datetime
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
    "simplify_target": None, "solver_result": None, "creative_mode": False, "show_animator": False, "animation_data": None, "quiz_state": None, "quiz_active": False,
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
    if is_creative:
        system = """You are a brilliant, creative English writing expert with the literary sensibility of a published author and the precision of an English professor.
You write with vivid imagery, original metaphors, varied sentence rhythms, and emotional intelligence.
When asked to write essays, debates, letters, stories, poems, diary entries, speeches, or any creative writing:
- Follow the correct format and rules for that genre meticulously
- Use sophisticated, precise vocabulary
- Vary sentence structure (short punchy sentences mixed with longer flowing ones)
- Include figurative language (original similes, metaphors, personification)
- Create atmosphere, mood, and emotional resonance
- Show don't tell
- Always explain the rules/structure you used after your writing
If asked about grammar, literature, or comprehension — explain clearly with examples."""
    else:
        system = """You are an expert tutor covering Physics, Chemistry, and English from Class 10 to College level.
For science: answer clearly with step-by-step explanations and formulas where needed.
For English: follow correct format rules, use sophisticated language, and explain your approach.
If unsure, say so honestly."""

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
    system = """You are a scientific animation director. Given a question and its answer,
produce a JSON animation script that visually explains the concept.

Return ONLY valid JSON, nothing else. Choose the best animation type:
- "atom": for atomic structure, valency, electron config, periodic table
- "molecule": for molecular structure, bonding, VSEPR, compounds
- "wave": for waves, sound, light waves, EM spectrum, SHM (wave form)
- "circuit": for electric circuits, Ohm's law, current flow
- "forces": for Newton's laws, vectors, force diagrams
- "thermodynamics": for gas laws, kinetic theory, temperature
- "projectile": for projectile motion, kinematics
- "light": for refraction, reflection, Snell's law, optics
- "electromagnetic": for electric fields, magnetic fields, charges
- "reaction": for chemical reactions, equations, reactants/products
- "pendulum": for pendulum, SHM, oscillations
- "spring": for spring-mass system, Hooke's law, SHM

JSON SCHEMAS by type:

ATOM: {"type":"atom","subtitle":"...","protons":N,"neutrons":N,"nucleus_radius":30,
"shells":[[e1,e2,...],[...]],"info_text":"...","legend":[{"color":"#hex","label":"..."}]}
shells is array of arrays, each inner array has number of electrons per shell.
Example for Carbon: "shells":[[2],[4]] means 2 in first shell, 4 in second.

MOLECULE: {"type":"molecule","subtitle":"...","atoms":[{"symbol":"O","x":0,"y":0,"color":"#hex","label":"...","radius":22}],
"bonds":[{"from":0,"to":1,"order":1}],"info_text":"..."}
x,y in range -1 to 1. order 1=single, 2=double, 3=triple.

WAVE: {"type":"wave","subtitle":"...","waves":[{"color":"#hex","amplitude":60,"wavelength":150,
"speed":0.03,"label":"Wave name","y_offset":0,"show_wavelength":true}],"info_text":"..."}

CIRCUIT: {"type":"circuit","subtitle":"...","nodes":[{"x":-0.8,"y":-0.5},{"x":0.8,"y":-0.5},{"x":0.8,"y":0.5},{"x":-0.8,"y":0.5}],
"wires":[{"from":0,"to":1,"speed":0.015}],"components":[{"type":"battery","x":-0.8,"y":0,"voltage":9,"label":"9V"},{"type":"resistor","x":0,"y":-0.5,"resistance":100}],"info_text":"..."}

FORCES: {"type":"forces","subtitle":"...","object":{"x":0.5,"y":0.5,"label":"Block","mass":"2kg"},
"forces":[{"label":"Weight","angle":90,"magnitude":100,"color":"#ff5555","value":"20N"},{"label":"Normal","angle":-90,"magnitude":100,"color":"#44ff88","value":"20N"}],"info_text":"..."}

THERMODYNAMICS: {"type":"thermodynamics","subtitle":"...","num_particles":30,"temperature":300,
"pressure":"P","volume":"V","moles":"n","label":"Gas at 300K","info_text":"..."}

PROJECTILE: {"type":"projectile","subtitle":"...","initial_velocity":25,"angle":45,"gravity":9.8,"info_text":"..."}

LIGHT: {"type":"light","subtitle":"...","n1":1.0,"n2":1.5,"incident_angle":45,"info_text":"..."}

ELECTROMAGNETIC: {"type":"electromagnetic","subtitle":"...","charge_pattern":"alternating",
"rows":3,"cols":5,"label":"Electric Field","info_text":"..."}

REACTION: {"type":"reaction","subtitle":"...","equation":"2H2 + O2 → 2H2O",
"reactants":[{"symbol":"H₂","formula":"2H₂","color":"#4da6ff"},{"symbol":"O₂","formula":"O₂","color":"#ff5555"}],
"products":[{"symbol":"H₂O","formula":"2H₂O","color":"#44ffaa"}],
"catalyst":"Pt catalyst","conditions":"High temp","info_text":"..."}

PENDULUM: {"type":"pendulum","subtitle":"...","length":200,"amplitude":30,"info_text":"..."}

SPRING: {"type":"spring","subtitle":"...","spring_constant":10,"mass":1,"amplitude":80,"info_text":"..."}

Pick the most appropriate type. Make the info_text educational and concise (under 100 words).
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
    # Find JSON object
    start = raw.find('{')
    end   = raw.rfind('}') + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(raw[start:end])
    except:
        return None

def show_animator_panel(animation_data):
    """Render the HTML5 Canvas animator in Streamlit."""
    import json, urllib.parse
    encoded = urllib.parse.quote(json.dumps(animation_data))
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
    document.getElementById('subtitle-text').textContent = scene.subtitle||scene.type||'Animation';
    document.getElementById('info-panel').textContent = scene.info_text||'';
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
#  MAIN APP
# ══════════════════════════════════════════════════════════════
def show_app():
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

        if st.button("🚪 Sign Out", use_container_width=True):
            supabase.auth.sign_out()
            for k in ["user","access_token","messages","pending_feedback","backend_ready","vs","Document"]:
                st.session_state[k] = None if k in ["user","access_token"] else \
                                      [] if k=="messages" else \
                                      False if k=="backend_ready" else None
            st.session_state.show_landing = True
            st.rerun()

        st.divider()

        # ── Numerical Solver Panel ─────────────────────────────
        # ── Creative Mode Toggle ───────────────────────────────
        st.markdown('<div class="section-label">✍️ Writing Mode</div>', unsafe_allow_html=True)
        creative_on = st.toggle(
            "🎨 Creative / English Mode",
            value=st.session_state.creative_mode,
            help="Turn ON for essays, debates, stories, poems, letters. Turn OFF for Physics & Chemistry."
        )
        if creative_on != st.session_state.creative_mode:
            st.session_state.creative_mode = creative_on
            st.rerun()
        if st.session_state.creative_mode:
            st.success("✍️ Creative Mode ON — Ask me to write essays, debates, letters, stories, poems!")
        else:
            st.info("⚛️ Science Mode — Ask Physics & Chemistry questions")

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

    # ── Chat history ───────────────────────────────────────────
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
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
    question = st.chat_input("Ask about Physics, Chemistry, or English Writing...")

    if question:
        st.session_state.simplify_target = None

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
            # ── Normal question ───────────────────────────────
            st.session_state.messages.append({"role": "user", "content": question})
        save_message("user", question)

        with st.chat_message("user"):
            st.write(question)

        history_text = "\n".join([
            f"{'Student' if m['role']=='user' else 'Tutor'}: {m['content']}"
            for m in st.session_state.messages[-6:]
        ])

        with st.chat_message("assistant"):
            with st.spinner("🔁 Thinking..."):
                answer, conf_label, conf_class = ask_question(question, vs, history_text)
                st.write(answer)
                st.markdown(f'<span class="{conf_class}">📊 {conf_label}</span>', unsafe_allow_html=True)

                st.session_state.messages.append({
                    "role": "assistant", "content": answer,
                    "confidence": conf_label, "conf_class": conf_class
                })
                save_message("assistant", answer, conf_label)
                st.session_state.pending_feedback = {"question": question, "answer": answer}

        st.rerun()

# ══════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════
if st.session_state.user is None or st.session_state.show_landing:
    show_landing()
else:
    show_app()