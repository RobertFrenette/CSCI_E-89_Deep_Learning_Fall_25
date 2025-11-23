# AI Agent Insure - System Architecture

**Complete architecture documentation for the Hybrid RAG Application**

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [End-to-End Initialization Flow](#end-to-end-initialization-flow)
4. [Agent Runtime Pipeline](#agent-runtime-pipeline)
5. [Evaluation Pipeline](#evaluation-pipeline)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [Component Details](#component-details)
8. [Technology Stack](#technology-stack)

---

## System Overview

AI Agent Insure Agent Assist is a **hybrid multimodal RAG (Retrieval-Augmented Generation) application** that combines:
- **Structured data queries** (SQLite database for insureds, policies, claims)
- **Unstructured document search** (ChromaDB vector store for PDF documents)
- **Intelligent query routing** (automatic detection of SQL vs RAG queries)
- **Multimodal I/O** (text and voice input, text and audio output)
- **Conversational memory** (summary-based context retention)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI AGENT INSURE                             │
│                     Hybrid RAG Application                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        INITIALIZATION PHASE                         │
│  (One-time setup: Cleanup → Environment → Data Preparation)         │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA PREPARATION                             │
│  ┌──────────────────────┐         ┌──────────────────────┐          │
│  │   Structured Data    │         │  Unstructured Data   │          │
│  │   (SQLite DB)        │         │   (Vector Store)     │          │
│  │                      │         │                      │          │
│  │ insured-db/          │         │ vector-store/        │          │
│  │ ├── CSV files        │         │ ├── PDF documents    │          │
│  │ └── create_*_db.py   │         │ └── create_*_vs.py   │          │
│  │     └──► insureds.db │         │     └──► chroma_db/  │          │
│  └──────────────────────┘         └──────────────────────┘          │
│           │                                   │                     │
│           └─────────────────┬─────────────────┘                     │
│                             ▼                                       │
│                    run_data_prep.py                                 │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       RUNTIME PHASE                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                        AGENT APPLICATION                     │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │   │
│  │  │   Audio    │  │     SQL    │  │     RAG    │              │   │
│  │  │ Processor  │  │  Processor │  │  Processor │              │   │
│  │  │            │  │            │  │            │              │   │
│  │  │ Whisper    │  │ SQLite     │  │ ChromaDB   │              │   │
│  │  │ macOS say  │  │ Thread-safe│  │ Ollama LLM │              │   │
│  │  └────────────┘  └────────────┘  └────────────┘              │   │
│  │        │              │                  │                   │   │
│  │        └──────────────┼──────────────────┘                   │   │
│  │                       ▼                                      │   │
│  │              Intelligent Query Router                        │   │
│  │              (Automatic SQL/RAG Detection)                   │   │
│  │                       │                                      │   │
│  │                       ▼                                      │   │
│  │                  Gradio UI (ui.py)                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EVALUATION PHASE                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   AGENT-EVAL MODULE                          │   │
│  │                                                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │   │
│  │  │  RAG Tests   │  │  SQL Tests   │  │   Metrics    │        │   │
│  │  │  (6 tests)   │  │  (4 tests)   │  │  Analysis    │        │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │   │
│  │         │                │                    │              │   │
│  │         └────────────────┼────────────────────┘              │   │
│  │                          ▼                                   │   │
│  │              Results JSON + Notebook Analysis                │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## End-to-End Initialization Flow

### Complete Initialization Sequence

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 1: CLEANUP                                  │
│                    (init.sh)                                        │
└─────────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Delete .venv │   │ Delete       │   │ Delete       │
│              │   │ __pycache__  │   │ Logs/DBs     │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│              STEP 2: ENVIRONMENT SETUP                              │
│              (init.sh)                                              │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────┐                       ┌──────────────┐
│ Create venv  │                       │ Install deps │
│ (uv venv)    │                       │ (uv pip)     │
└──────────────┘                       └──────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│              STEP 3: DATA PREPARATION                               │
│              (run_data_prep.py)                                     │
└─────────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│  PARALLEL DATA PREP (Step 1) │   │  PARALLEL DATA PREP (Step 2) │
│                              │   │                              │
│  SQL Database Creation       │   │  Vector Store Creation       │
│  ─────────────────────       │   │  ─────────────────────       │
│                              │   │                              │
│  insured-db/                 │   │  vector-store/               │
│  ├── CSV files               │   │  ├── PDF documents           │
│  │   ├── insureds.csv        │   │  │   └── knowledge-base/     │
│  │   ├── policies.csv        │   │  │       ├── company/        │
│  │   ├── coverage_*.csv      │   │  │       ├── products/       │
│  │   ├── ai_risk_*.csv       │   │  │       ├── guides/         │
│  │   └── claims_*.csv        │   │  │       ├── agent_support/  │
│  │                           │   │  │       └── personnel/      │
│  └── create_and_seed_*.py    │   │  └── create_chroma_*.py      │
│      │                       │   │      │                       │
│      ├── Parse CSVs          │   │      ├── Load PDFs           │
│      ├── Create schema       │   │      ├── Extract text        │
│      ├── Insert data         │   │      ├── Clean text          │
│      ├── Create indexes      │   │      ├── Chunk documents     │
│      └── Verify data         │   │      │   (1800/350 overlap)  │
│                              │   │      ├── Generate embeddings │
│                              │   │      │   (nomic-embed-text)  │
│                              │   │      ├── Enrich metadata     │
│                              │   │      │   (type, chunk_idx)   │
│                              │   │      └── Store in ChromaDB   │
│                              │   │                              │
│                              ▼   │                              ▼
│                    ┌─────────────┐│                    ┌─────────────┐
│                    │ insureds.db ││                    │ chroma_db/  │
│                    │             ││                    │             │
│                    │ 100 insureds││                    │ X vectors   │
│                    │ 208 policies││                    │ + metadata  │
│                    │ 46 claims   ││                    │             │
│                    └─────────────┘│                    └─────────────┘
│                                   │                              │
└───────────────────────────────────┴──────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│              STEP 4: VERIFICATION                                   │
│              (run_data_prep.py completes)                           │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Ready for     │
                    │ Agent Runtime │
                    └───────────────┘
```

### Detailed Initialization Flow

```
User runs: ./init.sh  (or: source init.sh to keep venv active after completion)
│
├─► CLEANUP PHASE
│   ├─► Remove .venv/ (if exists)
│   ├─► Remove all __pycache__/ directories
│   ├─► Clear agent/logs/ directory
│   ├─► Delete insured-db/insureds.db
│   └─► Delete vector-store/chroma_db/
│
├─► ENVIRONMENT SETUP
│   ├─► Check for uv command
│   ├─► Create virtual environment: uv venv --python python3.12
│   ├─► Activate virtual environment: source .venv/bin/activate
│   └─► Install dependencies: uv pip install -r requirements.txt
│
│   Note: If script was executed (./init.sh), venv activation is lost on exit.
│         If script was sourced (source init.sh), venv remains active.
│
└─► DATA PREPARATION (run_data_prep.py)
    │
    ├─► SQL DATABASE CREATION (insured-db/create_and_seed_insureds_db.py)
    │   │
    │   ├─► Validate CSV directory exists
    │   ├─► Delete existing insureds.db (if exists)
    │   │
    │   ├─► CREATE DATABASE SCHEMA
    │   │   ├─► Enable foreign keys (PRAGMA foreign_keys = ON)
    │   │   ├─► Create table: insureds (PRIMARY KEY: Insured_ID)
    │   │   ├─► Create table: policies (FK: Insured_ID)
    │   │   ├─► Create table: coverage_details (FK: Policy_Number)
    │   │   ├─► Create table: ai_risk_profile (FK: Policy_Number)
    │   │   ├─► Create table: claims_history (FK: Policy_Number, Insured_ID)
    │   │   └─► Create indexes for performance
    │   │
    │   └─► IMPORT DATA (in dependency order)
    │       ├─► Import insureds.csv → 100 records
    │       ├─► Import policies.csv → 208 records
    │       ├─► Import coverage_details.csv → 208 records
    │       ├─► Import ai_risk_profile.csv → 208 records
    │       └─► Import claims_history.csv → 46 records
    │
    └─► VECTOR STORE CREATION (vector-store/create_chroma_vectorstore.py)
        │
        ├─► Validate knowledge-base/ directory exists
        ├─► Delete existing chroma_db/ (if exists)
        │
        ├─► LOAD PDF DOCUMENTS
        │   ├─► Recursive scan of knowledge-base/
        │   ├─► Load PDFs using PyPDF
        │   ├─► Extract text page-by-page
        │   ├─► Clean text (normalize whitespace)
        │   └─► Extract document type and category from paths
        │
        ├─► CHUNK DOCUMENTS
        │   ├─► Use RecursiveCharacterTextSplitter
        │   ├─► Chunk size: 1800 chars (optimized)
        │   ├─► Chunk overlap: 350 chars (~20%)
        │   ├─► Filter small chunks (< 50 chars)
        │   ├─► Filter low-quality chunks (< 50% alphabetic)
        │   └─► Add document context prefixes to chunks
        │
        ├─► ENRICH METADATA
        │   ├─► source: PDF filename
        │   ├─► relative_path: Path from knowledge-base root
        │   ├─► document_type: product, company, guide, etc.
        │   ├─► document_category: Specific category
        │   ├─► chunk_index: Position in document
        │   ├─► total_chunks: Total chunks in document
        │   ├─► chunk_length: Size of chunk
        │   └─► page_count: Pages in source PDF
        │
        └─► GENERATE EMBEDDINGS & STORE
            ├─► Initialize OllamaEmbeddings (nomic-embed-text)
            ├─► Generate embeddings for all chunks
            ├─► Store in ChromaDB with metadata
            └─► Verify with test queries
```

---

## Agent Runtime Pipeline

### Complete Query Processing Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                                 │
│              (Gradio UI: http://127.0.0.1:7861)                     │
└─────────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────┐                       ┌──────────────┐
│  Text Input  │                       │ Audio Input  │
│              │                       │  (Microphone │
│              │                       │   or File)   │
└──────────────┘                       └──────────────┘
        │                                       │
        │                                       ▼
        │                              ┌──────────────┐
        │                              │  transcribe_ │
        │                              │  audio()     │
        │                              │  (Whisper)   │
        │                              └──────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            ▼
              ┌─────────────────────────┐
              │   process_query()       │
              │   (app.py)              │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  QueryService           │
              │  .process_query()       │
              │  (processors/query_     │
              │   service.py)           │
              │  Orchestrates pipeline  │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Query Preprocessing    │
              │  (processors/rag_       │
              │   processor.py - called │
              │   during RAG processing)│
              │  - Strip whitespace     │
              │  - Normalize text       │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  detect_query_type()    │
              │  (routing/query_        │
              │   router.py)            │
              │  Intelligent Routing    │
              └─────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌─────────────────────────┐        ┌─────────────────────────┐
│   SQL PATH              │        │   RAG PATH              │
│   (Structured Data)     │        │   (Unstructured Docs)   │
└─────────────────────────┘        └─────────────────────────┘
        │                                       │
        ▼                                       ▼
┌─────────────────────────┐        ┌──────────────────────────┐
│ SQLQueryHandler         │        │ get_answer_with_sources()│
│ .handle_query()         │        │ (processors/rag_         │
│                         │        │  processor.py)           │
│ Pattern Matching:       │        │                          │
│ • Count insureds        │        │ 1. Query Preprocessing   │
│ • Count claims          │        │ 2. Generate embeddings   │
│ • High risk policies    │        │ 3. Search ChromaDB       │
│ • Insured info by ID    │        │    (k=4, similarity)     │
│                         │        │ 4. Validate sources      │
│                         │        │ 5. LLM generation        │
│                         │        │    (strict prompt)       │
│                         │        │ 6. Format with metadata  │
└─────────────────────────┘        └──────────────────────────┘
        │                                       │
        ▼                                       ▼
┌─────────────────────────┐        ┌─────────────────────────┐
│ SQLProcessor Methods:   │        │ ConversationalRetrieval │
│ • count_insureds()      │        │ Chain                   │
│ • count_claims()        │        │                         │
│ • get_high_risk_*()     │        │ Components:             │
│ • get_insured_info()    │        │ • ChatOllama (llm)      │
│                         │        │ • Retriever (k=4)       │
│                         │        │ • ConversationSummary   │
│                         │        │   Memory                │
│                         │        │ • Custom Prompt Template│
└─────────────────────────┘        └─────────────────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            ▼
              ┌─────────────────────────┐
              │   Format Response       │
              │                         │
              │ SQL: Text-only          │
              │ RAG: Text + Sources     │
              │      + Enhanced Metadata│
              └─────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────┐                       ┌──────────────┐
│ SQL Response │                       │ RAG Response │
│              │                       │              │
│ (No audio)   │                       │ + Audio Gen  │
│              │                       │ (text_to_    │
│              │                       │  speech)     │
│              │                       │              │
│              │                       │ macOS say →  │
│              │                       │ ffmpeg → WAV │
└──────────────┘                       └──────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            ▼
              ┌─────────────────────────┐
              │   Display in UI         │
              │   (Gradio Interface)    │
              └─────────────────────────┘
```

### Agent Initialization Sequence

```
python agent/app.py
│
├─► INITIALIZE AUDIO (initialize_audio)
│   └─► Load Whisper model (base, ~140MB)
│
├─► INITIALIZE SQL (initialize_sql)
│   ├─► Create SQLProcessor instance
│   ├─► Connect to ../insured-db/insureds.db
│   ├─► Configure thread-local storage
│   ├─► Query statistics (counts)
│   └─► Display database stats
│
├─► INITIALIZE RAG (initialize_rag)
│   ├─► Create RAGProcessor instance
│   │
│   ├─► LOAD VECTOR STORE (load_existing_vectorstore)
│   │   ├─► Check ../vector-store/chroma_db/ exists
│   │   ├─► Initialize OllamaEmbeddings (nomic-embed-text)
│   │   ├─► Load ChromaDB with embeddings
│   │   └─► Verify vector count
│   │
│   └─► SETUP RAG CHAIN (setup_rag_chain)
│       ├─► Initialize ChatOllama (llama3.2:3b, temp=0.1, timeout=60s)
│       ├─► Create ConversationSummaryMemory (max 2000 tokens)
│       ├─► Create custom prompt template (strict, anti-hallucination)
│       ├─► Configure retriever (k=4, similarity search)
│       └─► Build ConversationalRetrievalChain
│
├─► INITIALIZE QUERY SERVICE
│   └─► Create QueryService instance
│       ├─► whisper_model (from initialize_audio)
│       ├─► sql_query_handler (from initialize_sql)
│       └─► rag_processor (from initialize_rag)
│
├─► TEST QUERY (optional)
│   └─► Query: "What is AI Agent Insure?"
│
└─► LAUNCH GRADIO UI (ui.py: create_interface)
    ├─► Build Gradio Blocks interface
    ├─► Wire event handlers
    └─► Launch server (http://127.0.0.1:7861)
```

---

## Evaluation Pipeline

### Agent-Eval Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EVALUATION INITIALIZATION                        │
│                    (agent-eval/test.py)                             │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Load Test Data         │
              │  (test_data.json)       │
              │                         │
              │  • 6 RAG tests          │
              │  • 4 SQL tests          │
              │  • Ground truth answers │
              │  • Expected keywords    │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Initialize Evaluator   │
              │  (RAGEvaluator)         │
              │                         │
              │  • Load RAGProcessor    │
              │    (from agent.processors │
              │     .rag_processor)     │
              │  • Setup RAG chain      │
              │  • Load vector store    │
              └─────────────────────────┘
                            │
                            ▼
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌─────────────────────────┐        ┌─────────────────────────┐
│   RAG TEST LOOP         │        │   SQL TEST LOOP         │
│   (6 tests)             │        │   (4 tests)             │
│                         │        │                         │
│  For each test:         │        │  For each test:         │
│  1. Execute full query  │        │  1. Execute query       │
│    (get_answer_with_    │        │  2. Execute SQL         │
│     sources)            │        │  3. Format results      │
│  2. Extract answer &    │        │  4. Compare to expected │
│     source documents    │        │     • Exact match       │
│  3. Evaluate quality    │        │     • Data correctness  │
│     • Context precision │        │                         │
│     • Answer relevance  │        │                         │
│  4. Record results      │        │  5. Record results      │
└─────────────────────────┘        └─────────────────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            ▼
              ┌─────────────────────────┐
              │  Calculate Metrics      │
              │                         │
              │  • Pass/Fail count      │
              │  • Success rate         │
              │  • Avg context precision│
              │  • Avg answer relevance │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Save Results           │
              │  (results/*.json)       │
              │                         │
              │  • Timestamp            │
              │  • Test results         │
              │  • Aggregate metrics    │
              │  • Error messages       │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Analysis Notebook      │
              │  (analysis.ipynb)       │
              │                         │
              │  • Load latest results  │
              │  • Visualizations       │
              │    - Pie charts         │
              │    - Bar charts         │
              │  • Failed test analysis │
              └─────────────────────────┘
```

---

## Data Flow Diagrams

### Data Preparation Flow

```
SOURCE DATA
│
├─► STRUCTURED DATA (CSV Files)
│   ├─► insured-db/insured_data/
│   │   ├─► insureds.csv (100 rows)
│   │   ├─► policies.csv (208 rows)
│   │   ├─► coverage_details.csv (208 rows)
│   │   ├─► ai_risk_profile.csv (208 rows)
│   │   └─► claims_history.csv (46 rows)
│   │
│   └─► PROCESSING
│       ├─► Parse CSV files
│       ├─► Validate foreign key relationships
│       ├─► Insert into SQLite database
│       ├─► Create indexes
│       └─► Verify integrity
│
│       ▼
│   insured-db/insureds.db
│   ├─► 5 tables with foreign keys
│   ├─► 770 total records
│   └─► Optimized indexes
│
└─► UNSTRUCTURED DATA (PDF Files)
    ├─► knowledge-base/
    │   ├─► company/ (2 PDFs)
    │   ├─► products/ (9 PDFs)
    │   ├─► guides/ (4 PDFs)
    │   ├─► agent_support/ (9 PDFs)
    │   └─► personnel/ (3 PDFs)
    │
    └─► PROCESSING
        ├─► Load PDFs (PyPDF)
        ├─► Extract text (page-by-page)
        ├─► Clean text (whitespace normalization)
        ├─► Chunk documents (1800/350 overlap)
        ├─► Filter low-quality chunks
        ├─► Enrich metadata (type, category, chunk_idx)
        ├─► Generate embeddings (nomic-embed-text)
        └─► Store in ChromaDB
        │
        ▼
    vector-store/chroma_db/
    ├─► Vector embeddings
    ├─► Enhanced metadata
    └─► Document context prefixes
```

### Query Processing Data Flow

```
USER QUERY
│
├─► INPUT PROCESSING
│   ├─► Text: Direct
│   └─► Audio: Whisper → Text
│
├─► QUERY PREPROCESSING
│   └─► Normalize, strip whitespace
│
├─► ROUTING DECISION
│   │
│   ├─► SQL PATH (if SQL keywords detected)
│   │   │
│   │   └─► SQL DATABASE
│   │       ├─► Pattern match to 4 query types
│   │       ├─► Execute SQL query
│   │       ├─► Format results
│   │       └─► Return text response
│   │
│   └─► RAG PATH (default)
│       │
│       ├─► VECTOR STORE RETRIEVAL
│       │   ├─► Generate query embedding
│       │   ├─► Search ChromaDB (k=4, similarity)
│       │   ├─► Retrieve top chunks
│       │   └─► Validate sources retrieved
│       │
│       ├─► LLM GENERATION
│       │   ├─► Combine: query + chunks + conversation history
│       │   ├─► Apply strict prompt template
│       │   ├─► Generate answer (temp=0.1)
│       │   └─► Validate answer quality
│       │
│       └─► RESPONSE FORMATTING
│           ├─► Format answer with sources
│           ├─► Include enhanced metadata
│           ├─► Generate audio (macOS say + ffmpeg)
│           └─► Return text + audio
│
└─► UI DISPLAY
    ├─► Show response text
    ├─► Display source documents
    └─► Play audio (RAG queries only)
```

---

## Component Details

### 1. Initialization Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `init.sh` | `/` | Complete project cleanup and setup |
| `run_data_prep.py` | `/` | Orchestrates both database creations |
| `create_and_seed_insureds_db.py` | `insured-db/` | Creates SQLite database from CSVs |
| `create_chroma_vectorstore.py` | `vector-store/` | Creates ChromaDB from PDFs |

### 2. Agent Application Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `app.py` | `agent/` | Main orchestrator, component initialization |
| `ui.py` | `agent/` | Gradio interface creation |
| `config.py` | `agent/` | Centralized configuration |
| `processors/query_service.py` | `agent/` | Query orchestration service |
| `processors/rag_processor.py` | `agent/` | RAG pipeline and retrieval |
| `processors/sql_processor.py` | `agent/` | SQL database operations |
| `processors/audio_processor.py` | `agent/` | Speech-to-text and text-to-speech |
| `routing/query_router.py` | `agent/` | Query type detection (SQL vs RAG) |
| `routing/sql_query_handler.py` | `agent/` | SQL query execution and formatting |
| `routing/constants.py` | `agent/` | Routing constants and indicators |
| `logger.py` | `agent/` | Logging configuration |

### 3. Evaluation Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `eval.py` | `agent-eval/` | Core evaluation functions |
| `test.py` | `agent-eval/` | Test execution script |
| `test_data.json` | `agent-eval/` | Test cases and ground truth |
| `analysis.ipynb` | `agent-eval/` | Results visualization |

### 4. Data Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `insureds.db` | `insured-db/` | SQLite database (structured data) |
| `chroma_db/` | `vector-store/` | ChromaDB vector store (unstructured data) |
| `knowledge-base/` | `/` | Source PDF documents |
| `insured_data/` | `insured-db/` | Source CSV files |

---

## Technology Stack

### Core Technologies

| Technology | Version/Purpose | Usage |
|------------|----------------|-------|
| **Python** | 3.12+ | Main language |
| **LangChain** | 0.3.13 | RAG framework |
| **ChromaDB** | Latest | Vector database |
| **SQLite** | 3.x | Structured data storage |
| **Gradio** | Latest | Web UI |
| **Ollama** | Latest | LLM and embeddings server |

### Models

| Model | Purpose | Location |
|-------|---------|----------|
| `llama3.2:3b` | LLM inference | Ollama |
| `nomic-embed-text` | Embeddings | Ollama |
| `whisper-base` | Speech-to-text | OpenAI Whisper |

### Dependencies

- **PDF Processing**: `pypdf`
- **Audio Processing**: `openai-whisper`, `ffmpeg` (macOS `say` command)
- **Database**: `sqlite3` (built-in), `chromadb`
- **ML/AI**: `langchain`, `langchain-community`, `ollama`
- **UI**: `gradio`
- **Utilities**: `uv` (virtual environment manager)

---

## Key Architectural Decisions

### 1. **External Data Preparation**
- **Rationale**: Faster startup, consistent embeddings, resource efficiency
- **Implementation**: Separate scripts create databases before app launch
- **Benefit**: Application starts in seconds vs minutes

### 2. **Intelligent Query Routing**
- **Rationale**: Natural language queries without explicit prefixes
- **Implementation**: Multi-factor keyword and intent analysis
- **Benefit**: Better user experience, automatic SQL/RAG detection

### 3. **Optimized Retrieval (k=4)**
- **Rationale**: Balance between speed and accuracy
- **Implementation**: Optimized chunk size (1800/350), retrieval k=4
- **Benefit**: Good accuracy with acceptable response times

### 4. **Environment-Based Configuration**
- **Rationale**: Easy deployment and environment-specific settings
- **Implementation**: `.env` file support with `python-dotenv` (rename `sample.env.txt` to `.env` in project root), all config values can be overridden
- **Benefit**: No code changes needed for different environments (dev/staging/prod)

### 5. **Enhanced Metadata**
- **Rationale**: Better source attribution and filtering
- **Implementation**: Document type, chunk index, page count
- **Benefit**: Improved transparency and debugging

### 6. **Strict Prompt Template**
- **Rationale**: Minimize hallucinations
- **Implementation**: "Answer based ONLY on provided context"
- **Benefit**: More factual, grounded responses

### 7. **Simplified SQL Queries**
- **Rationale**: Focus on most common operations
- **Implementation**: Four specific query types
- **Benefit**: Easier maintenance, predictable behavior

### 8. **Thread-Safe SQL**
- **Rationale**: Gradio uses multiple threads
- **Implementation**: `threading.local()` for connections
- **Benefit**: Concurrent query handling

### 9. **Modular UI**
- **Rationale**: Separation of concerns
- **Implementation**: `ui.py` separate from `app.py`
- **Benefit**: Better maintainability and testing

---

## Performance Characteristics

### Initialization Time
- **Full cleanup + setup**: ~2-5 minutes (depends on data size)
- **Data preparation only**: ~1-3 minutes
- **Agent startup**: ~5-10 seconds

### Query Response Time
- **SQL queries**: < 1 second
- **RAG queries**: ~3-10 seconds (depends on LLM and retrieval)
- **Audio generation**: ~1-2 seconds

### Resource Usage
- **Memory**: ~500MB-1GB (LLM models loaded)
- **Disk**: ~100MB (vector store) + ~1MB (SQL database)
- **CPU**: Moderate (LLM inference)

---

## System Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                    │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────┐                       ┌──────────────┐
│   Ollama     │                       │  Local Files │
│   Server     │                       │              │
│              │                       │  • PDFs      │
│  • llama3.2  │                       │  • CSVs      │
│  • nomic-    │                       │  • DBs       │
│    embed     │                       │              │
└──────────────┘                       └──────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            ▼
              ┌─────────────────────────┐
              │   Agent Application     │
              │   (Requires both)       │
              └─────────────────────────┘
```

---

## Security Considerations

1. **Local Processing**: All LLM and embedding processing runs locally
2. **No Cloud Dependencies**: No external API calls (except Ollama local server)
3. **File-Based Storage**: SQLite and ChromaDB are file-based (no network exposure)
4. **Thread Safety**: SQL connections use thread-local storage to prevent race conditions

---

## Future Enhancements

1. **SQL Query Expansion**: Add more query types based on user needs
2. **Evaluation Enhancement**: Add more SQL tests to agent-eval
3. **Performance Monitoring**: Add detailed performance metrics
4. **Caching**: Implement query result caching for common queries
5. **Multi-Model Support**: Allow switching between different LLM models
6. **Enhanced Filtering**: Implement document type filtering in retrieval

---

## Related Documentation

- **[agent/README.md](agent/README.md)** - Setup and usage guide
- **[agent/PIPELINE_FLOW.md](agent/PIPELINE_FLOW.md)** - Detailed pipeline flow
- **[vector-store/README.md](vector-store/README.md)** - Vector store documentation
- **[insured-db/README.md](insured-db/README.md)** - Database documentation
- **[agent-eval/README.md](agent-eval/README.md)** - Evaluation documentation

---

#### Credit: This markdown file was generated by 🤖 GitHub Copilot.
