# AI Agent Insure — Agent Assist

## Hybrid RAG Application

Multi-modal RAG chatbot with SQL database integration for insurance document and policy data queries.

**📚 Vector Store Documentation**

## Overview

The **vector store** is a persistent ChromaDB database containing embeddings of all PDF documents from the `../knowledge-base/` directory. It enables semantic search and retrieval-augmented generation (RAG) for the AI Agent Insure chatbot application.

This vector store is **created externally** before the application launches, ensuring:

- ⚡ **Fast startup** - App launches in seconds vs minutes
- 🎯 **Consistency** - Same embeddings across all runs
- 💰 **Resource efficiency** - No regeneration on every launch
- 🔧 **Better development** - Iterate on app logic without reprocessing documents

---

## Vector Store Statistics

The vector store contains:

- **Source**: All PDF files from `../knowledge-base/` (recursive scan)
- **Chunking**: 1800-character chunks with 350-character overlap (~20% overlap for context continuity)
- **Minimum Chunk Size**: 50 characters (filters out low-quality chunks)
- **Embedding Model**: `nomic-embed-text` (via Ollama)
- **Storage**: ChromaDB (persistent) in `./chroma_db/`
- **Enhanced Metadata**: Document type, category, chunk index, page count, chunk length
- **Vector Count**: Varies based on document size (typically 100-500+ vectors)

---

## Creating/Rebuilding the Vector Store

### Script: `create_chroma_vectorstore.py`

**Purpose**: Creates a persistent ChromaDB vector store with document embeddings for RAG retrieval.

This script processes all PDF documents from the `../knowledge-base/` directory, splits them into chunks, generates embeddings using the specified model, and stores them in a persistent ChromaDB. The RAG application loads this pre-created vector store at startup.

**Usage**:

```bash
cd /vector-store
python create_chroma_vectorstore.py
```

**What it does**:

1. Scans `../knowledge-base/` directory for all PDF files (recursive)
2. Extracts text from each PDF document using PyPDF
3. Cleans and normalizes text (whitespace, encoding issues)
4. Extracts document type and category from file paths
5. Splits documents into chunks (1800 chars, 350 overlap) using RecursiveCharacterTextSplitter
6. Filters out low-quality chunks (too small or mostly punctuation)
7. Adds document context prefixes to chunks for better semantic matching
8. Creates enriched metadata (document_type, document_category, chunk_index, etc.)
9. Generates embeddings using `nomic-embed-text` model via Ollama
10. Stores vectors with metadata in persistent ChromaDB at `./chroma_db/`
11. Runs verification with test queries to ensure proper functioning
12. Displays statistics, document type breakdown, and sample results

- ChromaDB directory: `./chroma_db/` (size varies by document count)
- Vectors created: depends on number and size of PDFs
- Console output showing progress, statistics, and verification

**Requirements**:

- Python 3.x with dependencies (see `requirements.txt`)
- **Ollama** running with `nomic-embed-text` model pulled
- PDF files in `../knowledge-base/` directory

**Virtual Environment**:

**Recommended (shared environment)**: Use the shared environment and install dependencies from the project root:

```bash
source .venv/bin/activate  # Use shared environment
uv pip install -r requirements.txt
cd vector-store
python create_chroma_vectorstore.py
```

**Note**: All dependencies for the vector store and other project components are managed in the root `requirements.txt`.

**Ollama Setup**:

```bash
# Ensure Ollama is running and model is available
ollama serve
ollama pull nomic-embed-text
```

**Before running**:

```bash
# Ensure Ollama is running
ollama serve

# Ensure the embedding model is available
ollama pull nomic-embed-text

# Activate the shared virtual environment (if using project setup)
source .venv/bin/activate

# Navigate to vector-store directory
cd vector-store
```

---

## Setup Workflow

**Run this script once before starting the application** (or whenever documents change):

```bash
# From project root
cd /vector-store
python create_chroma_vectorstore.py
```

Then run the application:

```bash
cd ../agent
python app.py
```

---

## Maintenance

### When to Rebuild the Vector Store

Rebuild the vector store when:

- ✏️ Adding new PDF documents to `../knowledge-base/`
- 🔄 Updating existing PDF documents
- 🗑️ Removing PDF documents
- ⚙️ Changing chunking parameters (chunk size/overlap/minimum chunk size)
- 🔀 Switching embedding models
- 📊 Updating metadata structure or document type extraction logic
- 🧹 Improving text cleaning or chunk filtering logic

### How to Rebuild

1. **Modify documents** in `../knowledge-base/` as needed
2. **Run the script**:
   ```bash
   cd /vector-store
   python create_chroma_vectorstore.py
   ```
3. **Restart the application**:
   ```bash
   cd ../agent
   python app.py
   ```

The script automatically:

- Removes any existing vector store
- Creates a fresh ChromaDB with updated embeddings
- Verifies the new vector store

---

## Configuration

The script uses these optimized default settings:

- **CHUNK_SIZE**: 1800 characters (optimized for better context preservation)
- **CHUNK_OVERLAP**: 350 characters (~20% overlap for context continuity)
- **MIN_CHUNK_SIZE**: 50 characters (filters out chunks smaller than this)
- **EMBEDDING_MODEL**: `nomic-embed-text`

These settings are optimized for better RAG retrieval quality with enhanced context preservation.

To modify these settings, edit the script's configuration section in `main()`:

```python
# Configuration - Optimized for better RAG retrieval
CHUNK_SIZE = 1800  # Increased from 1000 for better context preservation
CHUNK_OVERLAP = 350  # Increased from 200 (~20% overlap for context continuity)
MIN_CHUNK_SIZE = 50  # Filter out chunks smaller than this
EMBEDDING_MODEL = "nomic-embed-text"
```

---


## Architecture Benefits

### Why External Creation?

This approach separates **data preparation** from **application runtime**:

| Aspect       | External (Current)     | Internal (Old)        |
| ------------ | ---------------------- | --------------------- |
| Startup Time | Seconds                | Minutes               |
| Consistency  | Same embeddings always | Varies per run        |
| Development  | Fast iteration         | Slow iteration        |
| Resources    | One-time cost          | Repeated cost         |
| Production   | Create once, deploy    | Create on every start |

### Parallel Structure

The architecture now has symmetric data preparation:

```
/
├── db/                    # Structured data (SQLite)
│   ├── create_and_seed_insureds_db.py
│   ├── insureds.db
│   └── insured_data/      # CSV source files
├── vector-store/          # Unstructured data (ChromaDB)
│   └── create_chroma_vectorstore.py
├── knowledge-base/        # PDF source files
│   ├── company/
│   ├── products/
│   └── ...
└── agent/                   # Application runtime
    ├── app.py
   ├── chroma_db/         # Vector store output
    └── ...
```

Both databases:

- ✅ Created externally via dedicated scripts
- ✅ Persistent across application runs
- ✅ Independent of application lifecycle
- ✅ Easy to update and maintain

---

## Technical Details

### Embedding Model

**nomic-embed-text** is optimized for:

- Text retrieval and semantic search
- Efficient local deployment via Ollama
- Good balance of speed and quality
- Compatible with ChromaDB

### Chunking Strategy

**1800 characters with 350 overlap**:

- Larger chunks preserve more complete context and paragraphs
- ~20% overlap maintains context continuity across boundaries
- Filters out low-quality chunks (< 50 chars or < 50% alphabetic)
- Adds document context prefixes (document title and type) to each chunk
- Better separators (paragraphs, sentences) for coherent chunks
- Balances retrieval precision with rich context for better RAG performance

### Enhanced Metadata

Each chunk includes:

- **source**: PDF filename
- **relative_path**: Relative path from knowledge-base root
- **document_type**: Extracted from directory structure (product, company, guide, personnel, agent_support)
- **document_category**: More specific category from file path
- **chunk_index**: Position of chunk within document
- **total_chunks**: Total number of chunks in the document
- **chunk_length**: Size of the chunk in characters
- **page_count**: Number of pages in the source document

This enriched metadata enables:
- Filtering by document type during retrieval
- Better source attribution and context understanding
- Tracking chunk relationships within documents

### Storage

**ChromaDB** provides:

- Persistent local vector storage
- Fast similarity search
- Metadata support
- LangChain integration

---

## Features

### Text Processing
- **Normalization**: Cleans whitespace, removes excessive newlines
- **Quality Filtering**: Removes chunks with too little content (< 50 chars)
- **Structure Preservation**: Respects paragraph and section boundaries

### Document Context Enhancement
- **Document Type Detection**: Automatically categorizes documents (product, company, guide, etc.)
- **Context Prefixes**: Prepends document title and type to each chunk for better semantic matching
- **Metadata Enrichment**: Comprehensive metadata for filtering and source tracking

### Quality Assurance
- **Chunk Validation**: Filters out low-quality chunks before embedding
- **Statistics Reporting**: Shows document type breakdown, chunk size statistics
- **Verification Queries**: Tests retrieval with sample queries
- **Progress Tracking**: Detailed output showing processing steps

## Notes

- All PDF documents in `../knowledge-base/` are processed recursively
- The script provides detailed progress output for transparency
- Verification test queries ensure proper functioning
- Safe to run multiple times - automatically cleans old data
- Vector store is portable - can be copied to other environments
- Documents are skipped if they have too little content (< 50 characters)

---

For application usage and query patterns, see `../agent/README.md`.

---

#### Credit: This markdown file was generated by 🤖 GitHub Copilot.
