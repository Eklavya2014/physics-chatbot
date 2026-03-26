from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
 
print("=" * 50)
print("   Physics Chatbot - Knowledge Base Builder")
print("=" * 50)
 
# Check if physics_docs folder exists
if not os.path.exists("./physics_docs"):
    print("\n❌ ERROR: 'physics_docs' folder not found!")
    print("   Please create a folder named 'physics_docs' and add your .txt or .pdf files.")
    exit()
 
docs = []
 
# ── Load .txt files ──────────────────────────────────
txt_files = [f for f in os.listdir("./physics_docs") if f.endswith(".txt")]
if txt_files:
    print(f"\n📄 Found {len(txt_files)} .txt file(s): {txt_files}")
    txt_loader = DirectoryLoader(
        "./physics_docs/",
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    txt_docs = txt_loader.load()
    docs += txt_docs
    print(f"   ✅ Loaded {len(txt_docs)} .txt document(s).")
 
# ── Load .pdf files ──────────────────────────────────
pdf_files = [f for f in os.listdir("./physics_docs") if f.endswith(".pdf")]
if pdf_files:
    print(f"\n📄 Found {len(pdf_files)} .pdf file(s): {pdf_files}")
    for file in pdf_files:
        pdf_loader = PyPDFLoader(f"./physics_docs/{file}")
        pdf_docs = pdf_loader.load()
        docs += pdf_docs
        print(f"   ✅ Loaded '{file}' ({len(pdf_docs)} page(s)).")
 
# ── Check if any documents were loaded ───────────────
if not docs:
    print("\n❌ ERROR: No documents found in './physics_docs/'")
    print("   Please add .txt or .pdf physics files and try again.")
    exit()
 
print(f"\n📚 Total documents loaded: {len(docs)}")
 
# ── Split into chunks ────────────────────────────────
print("\n✂️  Splitting documents into chunks...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", " ", ""]
)
chunks = splitter.split_documents(docs)
print(f"   ✅ Created {len(chunks)} chunks.")
 
# ── Create embeddings ─────────────────────────────────
print("\n🧠 Creating embeddings (this may take a minute the first time)...")
print("   Downloading model 'all-MiniLM-L6-v2' if not already cached...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)
print("   ✅ Embedding model loaded.")
 
# ── Build FAISS index ─────────────────────────────────
print("\n🔍 Building FAISS vector index...")
vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local("physics_index")
print("   ✅ Index saved to './physics_index/'")
 
print("\n" + "=" * 50)
print("✅ Knowledge base built successfully!")
print("   Now run: python chatbot.py")
print("=" * 50)
 