# AI Agent Insure - Agent Assist Chatbot

## 🤖 Hybrid LLM RAG Agent - SQL + PDF Question Answering Chat

A standalone Python application for a multimodal RAG chatbot that answers questions from both structured database data and PDF documents using text or voice input.

## ✨ Features

- 📊 **SQL Database Queries** - Query structured insured data with four supported queries
- 📄 **PDF Processing** - Load and extract text from multiple PDFs
- 🔍 **Semantic Search** - Find relevant information using vector embeddings with enhanced metadata
- 🧩 **Intelligent Routing** - Automatic detection routes queries to SQL or RAG based on content
- 💬 **Conversational AI** - Multi-turn conversations with context memory (summary-based)
- 🎤 **Voice Input** - Ask questions using speech (Whisper)
- 🔊 **Audio Output** - Hear responses spoken aloud (macOS say command)
- 🤖 **100% Local** - All processing runs on your machine

## 🛠️ Tech Stack

- **Framework**: LangChain 0.3.13
- **Embeddings**: nomic-embed-text (Ollama)
- **Vector DB**: ChromaDB
- **SQL Database**: SQLite (insureds.db)
- **LLM**: llama3.2:3b (Ollama)
- **UI**: Gradio
- **Speech-to-Text**: OpenAI Whisper
- **Text-to-Speech**: macOS `say` command + ffmpeg

## 📋 Prerequisites

- Python 3.12+ (includes SQLite3 library built-in)
- [uv - Universal Virtualenv Manager](https://pypi.org/project/uv/)
- [Ollama](https://ollama.com/)
- **[ffmpeg](https://www.ffmpeg.org/)**: `brew install ffmpeg` (macOS)
- **SQLite CLI** (optional, for database inspection): `brew install sqlite` (macOS)

## 🚀 Setup

### 1️⃣ Create Virtual Environment

**Recommended**: Create a single shared virtual environment at the project root (`/`).

```bash
uv venv --python python3.12
source .venv/bin/activate
```

**Why at project root?**

- Single environment for db scripts, vector-store scripts, app, and evaluation
- Simpler workflow - activate once, use everywhere
- All dependencies are compatible (no conflicts)

**Note**: The `uv` tool creates isolated Python environments quickly. If you don't have it installed:

```bash
pip install uv
```

### 2️⃣ Install Dependencies

**Important**: Install from the project root, not from `/agent/`.

```bash
# Make sure you're in / with .venv/ directory
source .venv/bin/activate  # If not already activated

# Install all project dependencies
uv pip install -r requirements.txt
```

**Note**: The root `requirements.txt` contains all dependencies needed for the main application, evaluation, and vector store scripts.

### 3️⃣ Setup Ollama Models

```bash
# Start Ollama server (if not already running)
ollama serve

# Pull required models
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 4️⃣ Create Databases (Required - Run Once)

Both databases must be created before running the app:

```bash
# From project root with shared environment activated
source .venv/bin/activate  # If not already activated

# Create SQL database (no dependencies needed)
cd insured-db
python create_and_seed_insureds_db.py

# Create vector store (requires Ollama running with nomic-embed-text)
cd ../vector-store
python create_chroma_vectorstore.py

# Return to agent directory to run the app
cd ../agent
```

- **SQL Database**: Creates `../insured-db/insureds.db` with sample insurance data (100 insureds, 208 policies, 46 claims)
- **Vector Store**: Creates `../vector-store/chroma_db/` with embeddings from all PDFs in `../knowledge-base/`

**Note**: The app loads these pre-created databases - it does not create them automatically. This approach provides:

- ✅ Faster startup (seconds vs minutes)
- ✅ Consistent embeddings across runs
- ✅ Resource efficiency (no regeneration on every launch)
- ✅ Better development workflow

See `../insured-db/README.md` and `../vector-store/README.md` for detailed documentation.

## ▶️ Running the Application

### 💻 Basic Usage

**Important**: Ollama must be running before starting the app!

1. **Start Ollama** (in a separate terminal):

```bash
ollama serve
```

2. **Run the application**:

```bash
# From project root
source .venv/bin/activate  # If not already activated
cd agent
python app.py
```

The application will:

1. Load Whisper model for speech-to-text
2. Connect to SQL database and display statistics (insured count, claims count)
3. Load pre-created vector store from `../vector-store/chroma_db/`
4. Setup RAG chain with conversation memory and optimized retrieval
5. Run a test query (optional)
6. Launch Gradio interface at http://127.0.0.1:7861

**Prerequisites**:

- Ollama must be running (`ollama serve`)
- Databases must be created (see Setup step 4)

**Troubleshooting**:

- If you get `ConnectionError: Failed to connect to Ollama`, make sure Ollama is running in another terminal
- If you get `Vector store not found`, run the database creation scripts first (see Setup step 4)

### ⚙️ Advanced Usage

You can import and customize the application:

```python
from agent.app import RAGChatbotApp

app = RAGChatbotApp()
app.run(
    run_test=True  # Run test query (default: True)
)
```

## 📁 Project Structure

```
agent/
├── app.py                    # Main application entry point
├── ui.py                     # Gradio UI interface (separated from app logic)
├── config.py                 # Configuration settings
├── logger.py                 # Logging configuration
├── processors/               # Domain processors and service layer
│   ├── __init__.py          # Processor exports
│   ├── query_service.py     # Query orchestration service
│   ├── rag_processor.py     # RAG processing and vector store management
│   ├── sql_processor.py     # SQL database operations
│   └── audio_processor.py   # Speech-to-text and text-to-speech
├── routing/                  # Query routing logic
│   ├── __init__.py          # Routing exports
│   ├── query_router.py      # Query type detection (SQL vs RAG)
│   ├── sql_query_handler.py # SQL query execution and formatting
│   └── constants.py         # Routing constants and indicators
├── assets/                   # UI assets
│   ├── favicon.png          # Browser favicon
│   └── shield.png           # Company logo
└── logs/                     # Application logs (auto-created)
    └── app.log              # Main log file
```

## ⚙️ Configuration

The application supports configuration via environment variables using a `.env` file in the project root. All settings can be overridden via environment variables with fallback to defaults in `config.py`.

**Environment Variables**: Before running the application, rename `sample.env.txt` in the project root to `.env` to customize settings without modifying code. See the `.env` file for available options.

**Manual Configuration**: Edit `config.py` to customize:

- **PDF_DIR**: Path to PDF documents (default: `../knowledge-base`)
- **CHROMA_DIR**: Vector database location (default: `../vector-store/chroma_db`)
- **SQL_DB_PATH**: Path to SQLite database (default: `../insured-db/insureds.db`)
- **EMBEDDING_MODEL**: Embedding model name (default: `nomic-embed-text`)
- **LLM_MODEL**: LLM model name (default: `llama3.2:3b`)
- **TEMPERATURE**: LLM temperature (default: `0.1` for factual responses)
- **CHUNK_SIZE**: Text chunk size (default: `1800` - optimized for context preservation)
- **CHUNK_OVERLAP**: Chunk overlap (default: `350` - ~20% overlap)
- **RETRIEVAL_K**: Number of chunks to retrieve (default: `4` - optimized for accuracy)
- **RETRIEVAL_SCORE_THRESHOLD**: Minimum similarity score (default: `None`)
- **WHISPER_MODEL**: Whisper model size (default: `base`)
- **SQL_QUERY_PREFIX**: Prefixes for SQL routing (default: `["db:", "database:"]`)
- **MAX_TOKEN_LIMIT**: Max tokens for conversation summary (default: `2000`)
- **LOG_LEVEL**: Logging level (default: `INFO`)
- **LOG_DIR**: Directory for log files (default: `logs/`)
- **LOG_FILE**: Log file path (default: `logs/app.log`)
- **SERVER_NAME**: Gradio server hostname (default: `127.0.0.1`)
- **SERVER_PORT**: Gradio server port (default: `7861`)

## 📚 Code Documentation

### 📝 `processors/sql_processor.py`

**SQLProcessor Class** - Thread-safe SQL database operations:

- `connect()` - Establish database connection (thread-local storage)
- `disconnect()` - Close database connection for current thread
- `count_insureds()` - Count total number of insureds
- `count_claims()` - Count total number of claims filed
- `get_high_risk_policies(min_risk_score=90)` - Get all high-risk policies with insured and policy information
- `get_insured_info(insured_id)` - Get comprehensive information for a specific insured (includes policies and claims)

**Thread Safety**: Uses `threading.local()` to store per-thread connections, ensuring safe concurrent access in multi-threaded environments like Gradio.

**Supported SQL Queries** (via `SQLQueryHandler.handle_query()` in `routing/sql_query_handler.py`):

1. "How many insureds are there in the database?"
2. "How many claims have been filed?"
3. "Show me all the high risk policies."
4. "Show me information for insured [ID]" (e.g., "Show me information for insured BQ4DCXWL")

### 📝 `processors/rag_processor.py`

**RAGProcessor Class** - Complete RAG pipeline with optimized retrieval:

- `load_and_setup()` - Load pre-created vector store and setup RAG chain (preferred method)
- `load_existing_vectorstore()` - Load ChromaDB from disk
- `setup_rag_chain()` - Initialize LLM and ConversationSummaryMemory with optimized settings
  - Custom prompt template optimized to minimize hallucinations
  - Strict instructions to use only provided context
  - Configurable retrieval count (default: 3)
- `preprocess_query()` - Simplify and clean queries for better retrieval
- `get_answer_with_sources()` - Query with formatted sources and enriched metadata
  - Returns document type, category, chunk index in source information
  - Validates that source documents were retrieved
- `query()` - Query with console output showing enhanced metadata

**Optimizations**:
- Query preprocessing for better retrieval relevance
- Enhanced metadata (document_type, chunk_index) in source attribution
- Strict prompt template to minimize hallucinations
- Performance logging and timing

**Recommended Workflow**: Use `../vector-store/create_chroma_vectorstore.py` script to create vector store externally, then use `load_and_setup()` method in the app.

### 📝 `processors/audio_processor.py`

- `transcribe_audio(audio_path, whisper_model)` - Speech to text using OpenAI Whisper
- `text_to_speech(text)` - Text to speech using macOS say command + ffmpeg conversion

### 📝 `logger.py`

- `setup_logging()` - Configurable log levels, formats, and output (console/file)

### 📝 `ui.py`

- `create_interface(app)` - Creates and configures the Gradio interface
  - Separates UI code from application logic
  - Takes app instance and wires up event handlers
  - Returns configured Gradio Blocks interface

### 🚀 `app.py`

**RAGChatbotApp Class** - Main application orchestrator:

- `__init__()` - Initialize application components
- `initialize_audio()` - Load Whisper model for speech-to-text
- `initialize_sql()` - Connect to SQL database and display statistics
- `initialize_rag()` - Setup RAG system with optimized retrieval
- `process_query()` - Delegate to QueryService for query processing
- `clear_conversation()` - Clear conversation memory
- `run()` - Start the complete application with optional test query

### 📝 `processors/query_service.py`

**QueryService Class** - Service layer that orchestrates query processing:

- `process_query()` - Complete query processing pipeline (input → routing → execution → response)
- Coordinates domain processors (RAG, SQL, Audio) to handle queries end-to-end

### 📝 `routing/query_router.py`

- `detect_query_type()` - Classify query as SQL or RAG using intelligent routing

### 📝 `routing/sql_query_handler.py`

**SQLQueryHandler Class** - SQL query execution and formatting:

- `handle_query()` - Execute database queries (supports 4 query types)

The system uses **intelligent automatic routing** with multi-factor analysis:

### Intelligent Routing (No Prefix Required)

The agent app uses automatic detection to route queries to SQL or RAG based on query content. Prefixing with "DB:" or "DATABASE:" is optional and only needed to force SQL routing for ambiguous queries.

**How it works:**

- Most queries are routed automatically using keyword and intent analysis
- SQL queries are detected by keywords: "insured", "claims", "policies", "count", "how many", "high risk", etc.
- RAG queries (company info, products, guides) are routed to the document vector store
- Prefixes ("DB:", "database:") can be used to force SQL routing if desired, but are not required

**SQL Query Support:**

The application supports four specific database queries:

1. **Count Insureds**: "How many insureds are there in the database?" or variations
2. **Count Claims**: "How many claims have been filed?" or variations
3. **High Risk Policies**: "Show me all the high risk policies" (risk score >= 90)
4. **Insured Information**: "Show me information for insured [ID]" (e.g., "BQ4DCXWL")
   - Returns comprehensive info including policies and claims for the insured

**Output Differences:**

- SQL queries: Text-only results (no audio)
- RAG queries: Text + audio response (spoken answer)

**Design Rationale:**
Intelligent routing enables natural language queries without requiring explicit prefixes, while still allowing forced SQL routing for edge cases. The simplified SQL queries focus on the most common database operations.

---

#### Credit: This markdown file was generated by 🤖 GitHub Copilot.
