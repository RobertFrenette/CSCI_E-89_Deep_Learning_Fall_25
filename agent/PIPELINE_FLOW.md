# AI Agent Insure - Agent Assist Chatbot

## Hybrid RAG Application Pipeline Flow

## 🚀 **Startup Phase**

### 0. **Prerequisites**

```
⚠️  REQUIRED BEFORE RUNNING THE APP:

1. Ollama must be running:
   ollama serve

2. Databases must be created externally (one-time setup):
  cd ../insured-db
  python create_and_seed_insureds_db.py

   cd ../vector-store
   python create_chroma_vectorstore.py

The application requires Ollama for:
  - LLM inference (llama3.2:3b)
  - Embeddings were created with nomic-embed-text (already in vector store)
```

### 1. **Initialization** (`app.py` - `main()`)

```
User runs: python app.py
↓
setup_logging() initializes logging system
  - Creates logs/ directory if needed
  - Sets up console and/or file handlers
  - Configures log level from config.LOG_LEVEL
  - Creates app.log file if config.LOG_TO_FILE is True
↓
Creates RAGChatbotApp instance
↓
Calls app.run(run_test=True)
```

### 2. **Audio Initialization** (`initialize_audio()`)

```
Loads OpenAI Whisper model
↓
whisper.load_model("base")  # ~140MB
↓
Stores in self.whisper_model
```

### 4. **SQL Database Connection** (`initialize_sql()`)

```
Creates SQLProcessor instance with thread-local storage
↓
Connects to pre-created ../insured-db/insureds.db
  - Database was created externally by create_and_seed_insureds_db.py
  - Contains 100 insureds, 208 policies, 46 claims (ready to query)
  - Uses thread-safe connection handling
  - Connection stored in threading.local() for each thread
  - Sets row_factory to sqlite3.Row for dict-like access
↓
Queries database statistics:
  - Count insureds, policies, claims
  - Calculate average risk score
↓
Logs stats (insureds_count, policies_count, claims_history_count)
↓
Stores in self.sql_processor
↓
If database not found:
  - Logs error with helpful message
  - Suggests running: python ../insured-db/create_and_seed_insureds_db.py
  - Sets sql_processor = None
```

### 5. **RAG System Initialization** (`initialize_rag()`)

```
Creates RAGProcessor instance
↓
Calls processor.load_and_setup():

  A. Load Existing Vector Store (load_existing_vectorstore)
    - Checks if ../vector-store/chroma_db/ directory exists
     - Vector store was created externally by:
       cd ../vector-store && python create_chroma_vectorstore.py
     - Contains pre-generated embeddings of all PDFs from ../knowledge-base/
     - Enhanced with metadata (document_type, chunk_index, page_count)
     - Loads ChromaDB with OllamaEmbeddings (nomic-embed-text)
     - Prints: "✅ Loaded existing vector store with X vectors"
     - Startup is FAST (seconds vs minutes) - no PDF processing needed

  B. Setup RAG Chain (setup_rag_chain)
     - Initializes ChatOllama LLM (llama3.2:3b, temp=0.1, timeout=60s)
     - Creates ConversationSummaryMemory (max 2000 tokens)
       - Uses same LLM for summarization
       - Prevents unbounded memory growth
     - Custom prompt template optimized to minimize hallucinations
       - Strict instruction to use ONLY provided context
       - Explicit "I don't have that information" for missing context
     - Builds ConversationalRetrievalChain
       - Retriever with search_kwargs={"k": 4} (optimized for accuracy)
       - search_type="similarity" for better relevance
       - return_source_documents=True
     - Connects LLM + retriever + memory + custom prompt
     - Logs: "RAG chain initialized with optimized settings: k=4, custom prompt template"
↓
Stores qa_chain, memory, vectorstore
↓
Logs: "RAG system initialized with X vectors"
↓
If vector store not found:
  - Logs error with helpful message
  - Suggests running: python ../vector-store/create_chroma_vectorstore.py
  - Raises RuntimeError with instructions
  - App exits (cannot run without vector store)

NOTE: Original process_all() method that created vectors at runtime
is deprecated. The new workflow separates data preparation from
application runtime for much faster startup.
```

### 6. **Test Query** (optional, run_test=True by default)

```
Runs: "What is AI Agent Insure?"
↓
Calls processor.query(test_question)
↓
Displays:
  - Question
  - Answer
  - Retrieved chunks (with preview and metadata)
  - Sources
```

### 7. **Gradio Interface Launch** (`ui.py` - `create_interface()`)

```
Calls ui.create_interface(app_instance)
↓
Loads assets:
  - Logo: assets/shield.png (80x80)
  - Favicon: assets/favicon.png
↓
Builds UI with Gradio Blocks (theme="soft"):
  - Header with logo and title (config.APP_TITLE)
  - Description (config.APP_DESCRIPTION)
  - Text input box
  - Audio input (microphone/upload)
  - Submit button
  - Clear conversation button
  - Text output area
  - Audio output player
  - Example questions (from config.EXAMPLE_QUESTIONS)
↓
Event handlers wired to app instance:
  - submit_btn.click → app.process_query()
  - clear_btn.click → app.clear_conversation()
↓
Returns configured Gradio Blocks interface
↓
Launches on http://127.0.0.1:7861
  - share=False (no public link)
  - debug=True
  - favicon_path set
```

---

## 💬 **Query Processing Phase** (User Interaction)

### User submits a question (text or voice)

```
app.process_query(text_input, audio_input) is called
  ↓
Delegates to QueryService.process_query()
```

### 1. **Input Processing** (`processors/query_service.py` - `_handle_input()`)

```
IF audio_input exists:
  ↓
  transcribe_audio(audio_input, whisper_model)
  ↓
  Whisper converts speech → text
  ↓
  question = transcribed text
ELSE:
  ↓
  question = text_input
```

### 2. **Query Preprocessing** (`processors/rag_processor.py` - `preprocess_query()`)

```
Simplifies query for better retrieval (called during RAG processing):
  - Strips whitespace
  - Normalizes text
```

### 3. **Query Type Detection** (`routing/query_router.py` - `detect_query_type()`)

```
Intelligently detects SQL vs RAG routing using multi-factor analysis:

1. **Intelligent Routing (default):**
  - The agent app automatically detects SQL queries using keyword and intent analysis.
  - Prefixes ("DB:", "DATABASE:") are optional and only needed to force SQL routing for ambiguous queries.

2. SQL Indicators (client data queries):
   STRONG (weight: 3 points each):
   - Direct entities: "insured", "insureds", "policyholder", "customer"
   - Data specifics: "policy number", "claim number", "risk score"
   - Structured data: "premium", "deductible", "coverage limit"

   OPERATIONS (weight: 2 points each):
   - Counting: "how many", "count", "total", "average", "sum"
   - Listing: "list all", "show all", "find all", "get all"
   - Analytics: "statistics", "stats", "data about"

   QUALIFIERS (weight: 2 points each):
   - Context: "in the database", "from the database"
   - Relationships: "with coverage", "with policy", "with claim"

3. RAG Indicators (company/product information):
   COMPANY (weight: 3 points each):
   - Company name: "ai agent insure", "this company", "your company"
   - Company queries: "company offer", "company provide", "about ai agent"
   - Organizational: "mission", "vision", "values"

   PRODUCTS (weight: 2 points each):
   - Product info: "insurance product", "what products", "types of insurance"
   - Coverage types: "ai liability", "data breach", "model failure"
   - Product details: "coverage include", "coverage cover"

   PROCEDURES (weight: 2 points each):
   - Process: "how to file", "how to submit", "how to apply"
   - Steps: "what is the process", "steps to", "procedure for"
   - Documentation: "guide", "requirements for"

Decision Logic:
  IF sql_score > rag_score AND sql_score >= 2:
    → Route to SQL (client database)
  ELSE:
    → Route to RAG (company documents)

Examples:
  "What is AI Agent Insure?"
    → SQL: 0, RAG: 3 (company name) → RAG ✓

  "Show me high risk insureds"
    → SQL: 5 (show all=2, high risk=3), RAG: 0 → SQL ✓

  "How many policies?"
    → SQL: 2 (how many=2), RAG: 0 → SQL ✓

  "What insurance products do you offer?"
    → SQL: 0, RAG: 4 (insurance product=2, what products=2) → RAG ✓

  "Find all policyholders with claims"
    → SQL: 5 (find all=2, policyholders=3), RAG: 0 → SQL ✓

  "Show me database statistics"
    → SQL: Detected automatically (no prefix required) → SQL ✓

Benefits:
  - No prefix needed for most queries
  - Natural language understanding routes queries automatically
  - Prefixes still work as override for edge cases
  - Logs scoring for debugging (when LOG_LEVEL=DEBUG)
```

### 4. **Query Routing & Execution**

#### **Route A: SQL Query** (type = "sql", detected automatically or with optional prefix)

```
SQLQueryHandler.handle_query(cleaned_question)
↓
Pattern matching on cleaned question (supports 4 query types):

  1. Count Insureds:
     - Keywords: "insured", "how many", "count", "total"
     - NOT: "information", "info"
     → sql_processor.count_insureds()
     → Returns: "There are X insureds in the database."

  2. Count Claims:
     - Keywords: "claim", "how many", "count", "total", "filed"
     → sql_processor.count_claims()
     → Returns: "X claims have been filed."

  3. High Risk Policies:
     - Keywords: "high risk", "polic"
     → sql_processor.get_high_risk_policies(min_risk_score=90)
     → Returns formatted list of policies with risk score >= 90

  4. Insured Information:
     - Pattern: "Show me information for insured [ID]"
     - Extracts ID using regex: [A-Z0-9]{8}
     → sql_processor.get_insured_info(insured_id)
     → Returns comprehensive info: insured details, policies, claims

  Default (unsupported query):
     → Returns helpful message listing the 4 supported queries
↓
Format results for display
↓
Response: "📊 Database Query Results: ..."
↓
NO audio output (database results are text-only)
```

#### **Route B: RAG Query** (type = "rag", DEFAULT for all non-prefixed queries)

```
QueryService._process_rag_query(cleaned_question)
  ↓
rag_processor.get_answer_with_sources(cleaned_question)
↓
Preprocesses query: strips whitespace, normalizes text
↓
qa_chain({"question": cleaned_question})
↓
Process flow:
  1. Retriever searches ChromaDB for top K=4 similar chunks (optimized for accuracy)
  2. Validates retrieved chunks exist (answer validation)
  3. LLM receives: question + retrieved chunks + conversation history
  4. LLM generates answer using strict prompt template (temp=0.1 for factual accuracy)
     - Prompt instructs: "Answer based ONLY on provided context"
     - If answer not in context: "I don't have that information..."
  5. Returns answer + source documents with enhanced metadata
↓
Format answer with enriched metadata:
  - Answer text
  - Sources with document_type, chunk_index, page_count
  - Example: "📚 Sources: Company_Overview.pdf [Product, chunk 5/23, 12 pages]"
↓
Validates sources were retrieved (prevents hallucination)
↓
QueryService generates audio response (for RAG queries only):
  text_to_speech(answer) → generates WAV audio response
```

### 5. **Audio Response Generation** (`processors/audio_processor.py`)

```
text_to_speech(answer_text)
↓
macOS 'say' command → generates AIFF
↓
ffmpeg converts AIFF → WAV (44.1kHz, stereo)
↓
Returns WAV file path

Note: Audio generation only happens for RAG queries (SQL queries skip TTS)
```

### 6. **Response Display**

```
IF audio input:
  ↓
  Shows: "🎤 You asked: [transcribed question]
          [answer with sources]"
ELSE:
  ↓
  Shows: [answer with sources]

BOTH cases:
  ↓
  Audio player loaded with WAV file
```

---

## 🔄 **Conversation Memory Flow**

```
ConversationSummaryMemory automatically summarizes:
  - Previous questions and answers
  - Keeps recent exchanges verbatim
  - Summarizes older conversation (max 2000 tokens)

Each new query includes:
  - Current question
  - Summarized conversation history (compressed)
  - Retrieved relevant chunks

LLM can reference previous context:
  - "Tell me more about that" → knows what "that" is
  - "What about the other one?" → maintains context

Benefits:
  - Prevents unbounded memory growth
  - Maintains context without increasing token usage
  - Automatic compression of older conversations
```

---

## 🧹 **Clear Conversation**

```
User clicks "Clear Conversation"
↓
clear_conversation() is called
↓
memory.clear()
↓
Resets conversation history
↓
Clears input/output fields
```

---

## 📊 **Data Flow Summary**

```
INPUT SOURCES:
├─ Text input box → question string
├─ Audio (mic/file) → Whisper → question string
└─ Example questions → question string

PROCESSING PATHS (orchestrated by QueryService):
├─ SQL Path (automatic detection or optional "DB:" prefix): 
│   question → detect_query_type() → SQLQueryHandler.handle_query() → 
│   pattern matching → 4 supported queries → SQLProcessor → results (text only)
│   Supported: count insureds, count claims, high risk policies, insured info by ID
├─ RAG Path (DEFAULT, automatic routing): 
│   question → detect_query_type() → QueryService._process_rag_query() →
│   RAGProcessor.get_answer_with_sources() → preprocessing → embeddings → 
│   ChromaDB (k=4) → LLM (strict prompt) → answer + sources (text + audio)
│   Optimized: k=4 chunks, custom prompt, source validation, enhanced metadata

OUTPUT FORMATS:
├─ SQL: Text-only results with formatted database query results
└─ RAG: Answer + enriched sources (document_type, chunk_index) + WAV audio file

STORAGE (Pre-created externally):
├─ SQLite DB: ../insured-db/insureds.db (structured data, 100 insureds, 208 policies, 46 claims)
│  Created by: cd ../insured-db && python create_and_seed_insureds_db.py
├─ ChromaDB: ../vector-store/chroma_db/ (vector embeddings with enhanced metadata)
│  Created by: cd ../vector-store && python create_chroma_vectorstore.py
│  Enhanced with: document_type, chunk_index, page_count, document_category
└─ Memory: Summarized conversation history (max 2000 tokens, runtime only)
```

---

## 🎯 **Key Design Principles**

1. **External Data Preparation**: SQL DB and vector store created separately for fast startup
2. **Intelligent Routing**: Automatic detection of SQL vs RAG queries (prefix optional for forced SQL)
3. **Hallucination Reduction**: Temperature 0.1, strict prompt template, source validation, answer verification
4. **Optimized Performance**: k=4 chunks, query preprocessing, timeout handling (60s), performance logging
5. **Enhanced Metadata**: Document type, chunk index, page count in sources for better attribution
6. **Simplified SQL**: Four specific supported queries focused on common operations
7. **Multimodal**: Accepts text or voice, outputs text and audio (RAG only, SQL text-only)
8. **Conversational**: Maintains context across multiple turns with summary memory
9. **Local First**: All processing on local machine (Ollama, Whisper, SQLite)
10. **Dual Intelligence**: Structured DB queries OR unstructured document search
11. **Thread-Safe**: SQL connections use thread-local storage for concurrent requests
12. **Separation of Concerns**: Data prep (insured-db/, vector-store/) separate from runtime (agent/)
13. **UI Modularity**: UI code separated into ui.py for better maintainability
14. **Service Layer**: QueryService orchestrates query processing pipeline
15. **Organized Processors**: Domain processors (RAG, SQL, Audio) grouped in processors/ module
16. **Routing Module**: Query routing logic separated into routing/ module

---

## 📝 **Logging System** (`logger.py`)

The application uses a centralized logging configuration:

```python
setup_logging() initializes:
  - Console handler (if LOG_TO_CONSOLE = True)
    - Outputs to stdout/stderr
    - Formatted with timestamps, module names, levels

  - File handler (if LOG_TO_FILE = True)
    - Creates logs/ directory automatically
    - Writes to logs/app.log
    - Rotates/appends to existing logs

  - Root logger configuration
    - Level set from config.LOG_LEVEL
    - Format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    - force=True overwrites any existing configuration

Logging usage throughout app:
  - logger.debug() - Detailed debugging info
  - logger.info() - General operational messages
  - logger.warning() - Warning messages (e.g., missing DB)
  - logger.error() - Error messages with exc_info=True for tracebacks
  - logger.critical() - Fatal errors

Each module gets its own logger:
  logger = logging.getLogger(__name__)
```

---

## 📁 **File Structure & Responsibilities**

```
/
├── agent/
│   ├── app.py                    # Main orchestrator, component initialization
│   ├── ui.py                     # Gradio UI interface (separated from app logic)
│   ├── config.py                 # All configuration settings
│   ├── logger.py                 # Centralized logging setup
│   ├── processors/               # Domain processors and service layer
│   │   ├── __init__.py          # Processor exports
│   │   ├── query_service.py     # Query orchestration service
│   │   ├── rag_processor.py     # RAG pipeline (load vectorstore → retrieval with optimizations)
│   │   ├── sql_processor.py     # SQL database operations (4 supported queries)
│   │   └── audio_processor.py   # Whisper STT + macOS TTS
│   ├── routing/                  # Query routing logic
│   │   ├── __init__.py          # Routing exports
│   │   ├── query_router.py      # Query type detection (SQL vs RAG)
│   │   ├── sql_query_handler.py # SQL query execution and formatting
│   │   └── constants.py         # Routing constants and indicators
│   ├── assets/                   # UI assets (logo, favicon)
│   └── logs/                     # Application logs (auto-created)
│
├── insured-db/
│   ├── insureds.db              # SQLite database (100 insureds, 208 policies, 46 claims)
│   ├── insured_data/            # Source CSV files
│   └── create_and_seed_insureds_db.py  # Database creation script (run once)
│
├── vector-store/
│   ├── create_chroma_vectorstore.py    # ChromaDB vector store creation script (run once)
│   └── chroma_db/                      # Pre-created vector store (DO NOT DELETE)
│
└── knowledge-base/              # PDF documents (source for vector store)
    ├── agent_support/
    ├── company/
    ├── guides/
    ├── personnel/
    └── products/
```

---

## 🔧 **Configuration Details** (`config.py`)

The application loads configuration from environment variables via a `.env` file in the project root with fallback to these defaults. Before running the application, rename `sample.env.txt` in the project root to `.env` to customize settings:

```python
# Base directories (using pathlib)
BASE_DIR = Path(__file__).parent       # agent/ directory
PROJECT_ROOT = BASE_DIR.parent

# Paths (can be overridden via .env)
PDF_DIR = "../knowledge-base"          # PDF documents
CHROMA_DIR = "../vector-store/chroma_db"  # Vector database (external location)
SQL_DB_PATH = "../insured-db/insureds.db" # SQLite database

# RAG Settings (optimized for better retrieval quality)
CHUNK_SIZE = 1800                      # Optimized chunk size (matches vectorstore creation)
CHUNK_OVERLAP = 350                    # Optimized overlap (~20% overlap)
EMBEDDING_MODEL = "nomic-embed-text"   # Ollama embedding model
LLM_MODEL = "llama3.2:3b"             # Ollama LLM model
TEMPERATURE = 0.1                      # Low temp = minimal hallucinations, factual responses
RETRIEVAL_K = 4                        # Top 4 relevant chunks (optimized for accuracy)
RETRIEVAL_SCORE_THRESHOLD = None       # Score threshold (disabled - ChromaDB limitation)
RETRIEVAL_SEARCH_TYPE = "similarity"   # Similarity search for better relevance

# Audio settings
WHISPER_MODEL = "base"                 # Whisper model size (tiny, base, small, medium, large)

# Gradio settings
SERVER_NAME = "127.0.0.1"              # Local host
SERVER_PORT = 7861                     # Gradio port
SHARE = False                          # Public link disabled
DEBUG = True                           # Debug mode enabled

# Application metadata
APP_TITLE = "AI Agent Insure - Agent Assist"
APP_DESCRIPTION = "Ask questions about company documents and insured data using text or voice."

# SQL query prefix (optional - intelligent routing now detects SQL queries automatically)
SQL_QUERY_PREFIX = ["db:", "database:"]

# Example questions (demonstrates both intelligent routing and explicit prefix)
EXAMPLE_QUESTIONS = [
    "What is AI Agent Insure?",  # Automatic RAG routing (company info)
    "What products does this company offer?",  # Automatic RAG routing (product info)
    "How many insureds are in the database?",  # Automatic SQL routing (count operation)
    "Show me information for insured BQ4DCXWL.",  # Automatic SQL routing (client data)
]

# Logging settings
LOG_LEVEL = "INFO"                     # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = str(BASE_DIR / "logs")       # Directory for log files
LOG_FILE = str(BASE_DIR / "logs" / "app.log")  # Log file path
LOG_TO_FILE = True                     # Enable/disable file logging
LOG_TO_CONSOLE = True                  # Enable/disable console logging

# Memory settings
MEMORY_TYPE = "summary"                # Options: buffer, summary
MAX_TOKEN_LIMIT = 2000                 # Max tokens for conversation summary (prevents unbounded growth)
```

---

## 🧪 **Example Query Flows**

### Example 1: Count Insureds Query (Automatic SQL Routing)

```
User: "How many insureds are there in the database?"
↓
detect_query_type() → "sql" (scores: SQL=5 for "insured"=3 + "how many"=2, RAG=0)
↓
SQLQueryHandler.handle_query("How many insureds are there in the database?") 
↓
Pattern match: "insured" + "how many" (not "information") → count_insureds()
↓
sql_processor.count_insureds() → executes: SELECT COUNT(*) FROM insureds
↓
Returns: "There are 100 insureds in the database."
↓
Display: "📊 Database Query Results:

          There are 100 insureds in the database."
↓
No audio output (SQL queries are text-only)
```

### Example 2: Pure RAG Query (Automatic Routing)

```
User: "What is AI liability insurance?"
↓
detect_query_type() → "rag" (scores: SQL=0, RAG=2 for "ai liability")
↓
get_answer_with_sources()
↓
Embeddings generated for question
↓
ChromaDB retrieves top 5 similar chunks from PDFs
↓
LLM generates answer using retrieved context + conversation history
↓
Display: "[Answer about AI liability insurance]
          📚 Sources: AI_Insurance_Guide.pdf"
↓
text_to_speech() generates WAV audio response
```

### Example 3: Company Query (Automatic RAG Routing)

```
User: "What is AI Agent Insure?"
↓
detect_query_type() → "rag" (scores: SQL=0, RAG=3 for "ai agent insure")
↓
get_answer_with_sources()
↓
ChromaDB retrieves top 5 chunks about AI Agent Insure
↓
LLM generates answer from company documents
↓
Display: "[Answer about AI Agent Insure from PDFs]
          📚 Sources: Company_Overview.pdf, About_Us.pdf"
↓
Audio response generated
```

### Example 4: High Risk Policies Query (Automatic SQL Routing)

```
User: "Show me all the high risk policies"
↓
detect_query_type() → "sql" (scores: SQL=5 for "show"=2 + "high risk"=3, RAG=0)
↓
SQLQueryHandler.handle_query("Show me all the high risk policies")
↓
Pattern match: "high risk" + "polic" → get_high_risk_policies(min_risk_score=90)
↓
sql_processor.get_high_risk_policies(90)
↓
Executes query joining insureds, policies, ai_risk_profile tables
↓
Filters policies with Risk_Score_Internal >= 90
↓
Returns formatted list of high-risk policies with insured and policy details
↓
Display: "📊 Database Query Results:

          [List of high-risk policies with insured names, policy numbers, risk scores]"
↓
No audio output (SQL queries are text-only)
```

### Example 4b: Insured Information Query (Automatic SQL Routing)

```
User: "Show me information for insured BQ4DCXWL"
↓
detect_query_type() → "sql" (scores: SQL=5 for "insured"=3 + "information"=2, RAG=0)
↓
SQLQueryHandler.handle_query("Show me information for insured BQ4DCXWL")
↓
Pattern match: "information" + "insured" + extracts ID using regex: BQ4DCXWL
↓
sql_processor.get_insured_info("BQ4DCXWL")
↓
Executes comprehensive query joining insureds, policies, coverage_details, ai_risk_profile, claims_history
↓
Returns formatted insured information:
  - Insured details (name, contact, company)
  - All policies with details
  - Claims history
↓
Display: "📊 Database Query Results:

          [Comprehensive insured information with policies and claims]"
↓
No audio output (SQL queries are text-only)
```

### Example 5: Voice Query with Count Claims

```
User: [speaks] "How many claims have been filed?"
↓
Whisper transcribes → "How many claims have been filed?"
↓
detect_query_type() → "sql" (scores: SQL=4 for "claim"=2 + "how many"=2, RAG=0)
↓
SQLQueryHandler.handle_query("How many claims have been filed?")
↓
Pattern match: "claim" + "how many"/"filed" → count_claims()
↓
sql_processor.count_claims() → executes: SELECT COUNT(*) FROM claims_history
↓
Display: "🎤 You asked: How many claims have been filed?

          📊 Database Query Results:
          
          46 claims have been filed."

No audio player (SQL queries skip TTS)

User: [types] "What types of coverage do you offer?"
↓
detect_query_type() → "rag" (scores: SQL=0, RAG=4 for "types"=2 + "coverage"=2)
↓
ConversationSummaryMemory provides previous context (summarized)
↓
LLM searches documents for coverage type information
↓
Generates detailed response using conversation history + retrieved chunks
↓
Audio response generated
```

### Example 6: Unsupported SQL Query

```
User: "DB: Find all policies expiring in 2025"
↓
detect_query_type() → "sql" (explicit "DB:" prefix detected, forced routing)
↓
Cleaned question: "Find all policies expiring in 2025"
↓
SQLQueryHandler.handle_query("Find all policies expiring in 2025")
↓
Pattern matching: No match for the 4 supported query types
↓
Returns helpful message:
↓
Display: "📊 Database Query Results:

          I can answer four types of database queries:

          1. "How many insureds are there in the database?"
          2. "How many claims have been filed?"
          3. "Show me all the high risk policies."
          4. "Show me information for insured [ID]"

          Please try one of these queries."
```

---

## 🚨 **Error Handling**

```
Logging System:
  - All errors logged with logger.error() and exc_info=True
  - All operations logged at appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Logs written to console and/or file based on config

Database Not Found:
  - initialize_sql() catches FileNotFoundError
  - Logs error message with instructions
  - Suggests: python ../insured-db/create_and_seed_insureds_db.py
  - Sets sql_processor = None
  - App continues with RAG-only functionality

Vector Store Not Found:
  - initialize_rag() checks if ../vector-store/chroma_db/ exists
  - Logs error message with instructions
  - Suggests: python ../vector-store/create_chroma_vectorstore.py
  - Raises RuntimeError (app cannot run without vector store)
  - User must create vector store before starting app

No PDFs Found (during vector store creation):
  - load_pdfs() finds 0 files in ../knowledge-base/
  - Logs warning during creation script
  - Creates empty vectorstore
  - App will start but won't retrieve relevant documents

Audio Transcription Fails:
  - Checks if audio_path exists
  - Checks file size (< 1000 bytes = too small)
  - transcribe_audio() returns empty string on error
  - process_query() shows error message to user ("❌ Could not transcribe audio...")
  - Doesn't crash app

Text-to-Speech Fails:
  - Catches subprocess.CalledProcessError
  - Logs error with stderr output
  - Returns None (no audio player shown)
  - User still receives text response

LLM Query Error:
  - Exception caught in process_query()
  - Logged with exc_info=True for full traceback
  - Returns formatted error message to user ("❌ Document search error: ...")

SQL Query Error:
  - Exception caught in SQLQueryHandler.handle_query()
  - Logged with exc_info=True
  - Returns formatted error message ("❌ Database query error: ...")
```

---

## 🎨 **User Interface Flow**

```
Gradio Web Interface (http://127.0.0.1:7861)
┌────────────────────────────────────────────────┐
│ 🤖 AI Agent Insure Chatbot                    │
├────────────────────────────────────────────────┤
│ Ask questions about insurance documents...    │
├──────────────────┬─────────────────────────────┤
│ Input            │ Response                    │
├──────────────────┤                             │
│ [Type question]  │ [Answer appears here]       │
│                  │                             │
│ [🎤 Record/      │ [🔊 Audio player]          │
│     Upload]      │                             │
│                  │                             │
│ [Submit]         │                             │
│ [Clear]          │                             │
├──────────────────┴─────────────────────────────┤
│ Example Questions:                             │
│ • What is AI Agent Insure?                     │
│ • What products does this company offer?       │
│ • DB: Find the high risk policies              │
└────────────────────────────────────────────────┘
```

---

#### Credit: This markdown file was generated by 🤖 GitHub Copilot.
