# 🏗️ Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     1C PORTAL RAG CHATBOT                        │
│                    Complete System Architecture                  │
└─────────────────────────────────────────────────────────────────┘


╔═══════════════════════════════════════════════════════════════════╗
║                      OFFLINE PHASE (One-Time)                      ║
╚═══════════════════════════════════════════════════════════════════╝

    📄 PDF Document
    (1C_Portal_Support_Guide_v3.2.pdf)
            │
            ▼
    ┌───────────────────┐
    │   PyPDF2 Parser   │ ───► Extract text page by page
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │  Text Chunking    │ ───► Split into 500-char pieces
    │  (500 chars with  │      with 100-char overlap
    │   100 overlap)    │
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │ OpenAI Embedding  │ ───► text-embedding-ada-002
    │   API Call        │      Converts to 1536D vectors
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │  FAISS Index      │ ───► Store vectors for fast search
    │  (IndexFlatIP)    │      Inner Product similarity
    └───────────────────┘
            │
            ▼
    💾 Save to Disk
    ├─ vectors.index (FAISS binary)
    └─ chunks.pkl (Text + metadata)


╔═══════════════════════════════════════════════════════════════════╗
║                    ONLINE PHASE (Every Query)                      ║
╚═══════════════════════════════════════════════════════════════════╝

    👤 User Question
    "How do I fill timesheet?"
            │
            ▼
    ┌───────────────────┐
    │ Query Embedding   │ ───► Convert to 1536D vector
    │   (OpenAI API)    │      Same model as documents
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │ Vector Search     │ ───► FAISS similarity search
    │  (Top-K = 5)      │      Find 5 most similar chunks
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │ Retrieve Chunks   │ ───► Get text from matched vectors
    │ + Page Numbers    │      Include source metadata
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │  Build Context    │ ───► Combine chunks into prompt
    │  (RAG Prompt)     │      System + Context + Query
    └───────────────────┘
            │
            ▼
    ┌───────────────────┐
    │   GPT-3.5 Turbo   │ ───► Generate answer using context
    │  Answer Generation│      Cites page numbers
    └───────────────────┘
            │
            ▼
    🤖 Answer + Sources
    "To fill timesheet: 1. Navigate to... (Page 8, 9)"
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    DATA TRANSFORMATION                        │
└──────────────────────────────────────────────────────────────┘

INPUT (PDF)
│
├─ Page 1: "Timesheet Management..."  (2,500 chars)
├─ Page 2: "Leave Application..."     (2,800 chars)  
└─ Page 3: "Expense Claims..."        (2,300 chars)
         │
         ▼ CHUNKING
         │
├─ Chunk 1: "Timesheet Management. To submit..." [500 chars]
├─ Chunk 2: "...submit timesheet, navigate..."  [500 chars]
├─ Chunk 3: "...navigate to portal home..."     [500 chars]
└─ ...
         │
         ▼ EMBEDDING (OpenAI)
         │
├─ Vector 1: [0.023, -0.145, 0.892, ..., 0.334] (1536 dims)
├─ Vector 2: [0.156, -0.023, 0.445, ..., 0.891] (1536 dims)
├─ Vector 3: [0.234, 0.567, -0.123, ..., 0.678] (1536 dims)
└─ ...
         │
         ▼ FAISS INDEX
         │
    [Searchable Vector Database]
         │
         ▼ QUERY TIME
         │
User Query: "timesheet submission"
         │
Query Vector: [0.045, -0.123, 0.778, ..., 0.456]
         │
         ▼ SIMILARITY SEARCH
         │
Cosine Similarity Calculation:
- Chunk 1: 0.89 ✓ (High match!)
- Chunk 2: 0.85 ✓
- Chunk 5: 0.12 ✗ (Low match)
         │
         ▼ TOP-K SELECTION
         │
Top 5 Most Relevant Chunks
         │
         ▼ GPT GENERATION
         │
Answer: "To submit timesheet, navigate to..."
```

---

## Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM COMPONENTS                         │
└─────────────────────────────────────────────────────────────┘


┌─────────────┐         ┌──────────────┐         ┌──────────┐
│   config.py │────────▶│pdf_to_vectors│────────▶│Vector DB │
│  (Settings) │         │     .py      │         │  Storage │
└─────────────┘         └──────────────┘         └──────────┘
                               │                       │
                               │ creates               │
                               ▼                       ▼
                        ┌──────────────┐       ┌─────────────┐
                        │ chunks.pkl   │       │vectors.index│
                        │ (Text data)  │       │(FAISS index)│
                        └──────────────┘       └─────────────┘
                               │                       │
                               └───────┬───────────────┘
                                       │ loaded by
                                       ▼
                              ┌─────────────────┐
                              │ ask_questions.py│
                              │  (Query Logic)  │
                              └─────────────────┘
                                       │
                                       │ used by
                                       ▼
                              ┌─────────────────┐
                              │  rag_chatbot.py │
                              │   (Main App)    │
                              └─────────────────┘
                                       │
                                       │ interacts with
                                       ▼
                                  ┌─────────┐
                                  │  User   │
                                  │ (You!)  │
                                  └─────────┘
```

---

## File Size & Storage

```
📊 STORAGE BREAKDOWN
═══════════════════════════════════════════

Input:
├─ PDF Document:        2.5 MB
└─ Total Pages:         20

After Processing:
├─ Text Chunks:         ~250 chunks
├─ chunks.pkl:          150 KB (text + metadata)
└─ vectors.index:       1.5 MB (FAISS index)

Total Vector DB Size:   ~1.65 MB

Memory Usage (Runtime):
├─ FAISS Index:         ~2 MB in RAM
├─ Text Chunks:         ~200 KB in RAM
└─ Python Process:      ~50 MB total
```

---

## Query Performance

```
⏱️  TIMING BREAKDOWN (Average Query)
═══════════════════════════════════════════

Step 1: Load Database          0.1s  ▓░░░░░░░░░
Step 2: Embed Query            0.5s  ▓▓▓▓▓░░░░░
Step 3: FAISS Search           0.001s ░░░░░░░░░░
Step 4: Retrieve Chunks        0.01s ░░░░░░░░░░
Step 5: GPT Generation         1.5s  ▓▓▓▓▓▓▓▓▓▓

Total Query Time:              ~2.1 seconds
                              ─────────────────
                              85% is OpenAI API
                              15% is local processing
```

---

## Similarity Search Example

```
🔍 HOW SIMILARITY SEARCH WORKS
═══════════════════════════════════════════

Query: "How to reset password?"
Query Vector: [0.23, -0.45, 0.78, ..., 0.12]

Document Chunks in Vector Space:

                    📄 "Password reset process..."
                    Score: 0.92 ✓ (Very Similar!)
                         │
                         │    📄 "Account security..."
                         │    Score: 0.75 ✓
    📄 "Timesheet..."    │         │
    Score: 0.23         ❓Query    │
                         │         │
                         │    📄 "Leave policy..."
                    📄 "Project..."   Score: 0.15
                    Score: 0.18


Cosine Similarity Formula:
similarity = dot(vec1, vec2) / (|vec1| * |vec2|)

Range: [-1, 1]
  1.0  = Identical
  0.0  = Unrelated
 -1.0  = Opposite

Threshold: 0.5 (only return chunks > 0.5)
```

---

## Code Execution Flow

```python
# INDEXING FLOW (pdf_to_vectors.py)
# ═══════════════════════════════════

def main():
    pdf = open("data/document.pdf")           # 1. Load PDF
    ↓
    pages = extract_text(pdf)                 # 2. Extract text
    ↓
    chunks = create_chunks(pages)             # 3. Split into chunks
    ↓
    embeddings = get_embeddings(chunks)       # 4. Call OpenAI API
    ↓
    index = build_faiss_index(embeddings)     # 5. Create FAISS index
    ↓
    save(index, chunks)                       # 6. Save to disk


# QUERY FLOW (rag_chatbot.py)
# ═══════════════════════════════════

def query(question):
    index, chunks = load_database()           # 1. Load from disk
    ↓
    query_vec = embed_query(question)         # 2. Embed question
    ↓
    indices = index.search(query_vec, k=5)    # 3. Find top-5
    ↓
    context = get_chunks(indices)             # 4. Get text
    ↓
    prompt = build_prompt(question, context)  # 5. Build prompt
    ↓
    answer = call_gpt(prompt)                 # 6. Generate answer
    ↓
    return answer
```

---

## API Calls & Costs

```
💰 COST BREAKDOWN
═══════════════════════════════════════════

INDEXING (One-time):
┌────────────────────────────────────────┐
│ Text Chunks: 250                       │
│ Embedding Model: text-embedding-ada-002│
│ Cost: $0.0001 per 1K tokens           │
│                                        │
│ Calculation:                           │
│ 250 chunks × 100 tokens = 25K tokens  │
│ 25K tokens × $0.0001/1K = $0.0025     │
│                                        │
│ TOTAL INDEXING COST: ~$0.50 - $1.00   │
└────────────────────────────────────────┘

PER QUERY:
┌────────────────────────────────────────┐
│ 1. Query Embedding                     │
│    ~20 tokens × $0.0001/1K = $0.000002│
│                                        │
│ 2. GPT Generation                      │
│    Prompt: 2000 tokens                 │
│    Response: 500 tokens                │
│    Cost: $0.002/1K tokens              │
│    2500 × $0.002/1K = $0.005          │
│                                        │
│ TOTAL PER QUERY: ~$0.01 - $0.03       │
└────────────────────────────────────────┘

100 QUERIES: ~$1 - $3
1000 QUERIES: ~$10 - $30
```

---

## Technology Stack

```
🛠️  TECH STACK
═══════════════════════════════════════════

┌─────────────────┬──────────────────────┐
│   Layer         │   Technology         │
├─────────────────┼──────────────────────┤
│ Language        │ Python 3.8+          │
│ PDF Parser      │ PyPDF2               │
│ Embeddings      │ OpenAI Ada-002       │
│ Vector DB       │ FAISS                │
│ LLM             │ GPT-3.5-turbo        │
│ Arrays          │ NumPy                │
│ Serialization   │ Pickle               │
│ IDE             │ PyCharm              │
└─────────────────┴──────────────────────┘

ALTERNATIVES:
├─ Embeddings:  Sentence-BERT, Cohere
├─ Vector DB:   Pinecone, Weaviate, Milvus
├─ LLM:         Claude, Llama, Mistral
└─ PDF Parser:  PyMuPDF, pdfplumber
```

---

## Scalability Considerations

```
📈 SCALING THE SYSTEM
═══════════════════════════════════════════

Current Setup (Small Scale):
├─ Documents:     1 PDF (20 pages)
├─ Chunks:        ~250
├─ Index Type:    IndexFlatIP (exact search)
├─ Query Time:    ~2 seconds
└─ Suitable for:  <10K chunks

Medium Scale (10-100 PDFs):
├─ Documents:     10-100 PDFs
├─ Chunks:        ~10K
├─ Index Type:    IndexIVFFlat (approximate)
├─ Query Time:    ~500ms
└─ Changes:       Add clustering to FAISS

Large Scale (100+ PDFs):
├─ Documents:     100+ PDFs
├─ Chunks:        ~100K+
├─ Index Type:    IndexHNSW (graph-based)
├─ Query Time:    ~100ms
└─ Changes:       Use Pinecone/Weaviate

Enterprise Scale:
├─ Documents:     Thousands
├─ Chunks:        Millions
├─ Solution:      Distributed vector DB
├─ Technology:    Milvus, Weaviate cluster
└─ Query Time:    <50ms
```

---
