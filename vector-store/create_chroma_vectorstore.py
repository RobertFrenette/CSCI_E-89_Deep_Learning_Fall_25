"""
Create and populate ChromaDB vector store from PDF documents.

This script reads PDF files from the knowledge-base directory and creates
a persistent ChromaDB vector store with embeddings for RAG retrieval.

Optimized for better retrieval quality with enhanced metadata and chunking
by adding document context to each chunk.
"""

import os
import sys
import glob
import shutil
import re
from pathlib import Path
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma


def extract_document_type(rel_path: str, filename: str) -> tuple[str, str]:
    """
    Extract document type and category from file path. Returns tuple.
    
    Params:
    - rel_path: Relative file path from knowledge-base root
    - filename: Name of the PDF file
    
    Returns:
    - tuple(document_type, document_category)
    """
    path_parts = Path(rel_path).parts
    
    # Map directory names to document types
    type_mapping = {
        'products': 'product',
        'company': 'company',
        'guides': 'guide',
        'personnel': 'personnel',
        'agent_support': 'agent_support'
    }
    
    # Extract document type from directory structure
    doc_type = 'document'
    doc_category = filename.replace('.pdf', '').replace('_', ' ')
    
    for part in path_parts:
        part_lower = part.lower()
        if part_lower in type_mapping:
            doc_type = type_mapping[part_lower]
            break
    
    # Extract more specific category from filename or parent directory
    if len(path_parts) > 1:
        doc_category = path_parts[-2] if path_parts[-2] != path_parts[0] else doc_category
    
    return doc_type, doc_category

def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text for better chunking. Returns cleaned text.
    
    Params:
    - text: Raw extracted text from PDF
    
    Returns:
    - Cleaned and normalized text
    """
    if not text:
        return text
    
    # Normalize whitespace: replace multiple spaces/newlines with single
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs -> single space
    text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines -> double newline
    text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)  # Clean line breaks
    
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def load_pdfs(pdf_dir: str):
    """
    Load all PDFs from directory and extract text with enhanced metadata. Returns list of document dicts.
    
    Params:
    - pdf_dir: Directory containing PDF files
    
    Returns:
    - List of document dictionaries with text and metadata
    
    Throws:
    - Exception if PDF loading fails
    """
    documents = []
    pdf_files = glob.glob(f"{pdf_dir}/**/*.pdf", recursive=True)
    
    print(f"📄 Found {len(pdf_files)} PDF files")
    print()
    
    for pdf_path in pdf_files:
        try:
            reader = PdfReader(pdf_path)
            
            # Extract text with page tracking
            text = ""
            page_texts = []
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                page_texts.append((page_num, page_text))
                text += page_text + "\n\n"
            
            # Clean and normalize text
            text = clean_text(text)
            
            # Skip documents with too little content
            if len(text) < 50:
                print(f"   ⚠️  Skipping {os.path.basename(pdf_path)}: too little content ({len(text)} chars)")
                continue
            
            # Extract metadata
            rel_path = os.path.relpath(pdf_path, pdf_dir)
            doc_type, doc_category = extract_document_type(rel_path, os.path.basename(pdf_path))
            
            # Store with enriched metadata
            documents.append({
                'text': text,
                'source': os.path.basename(pdf_path),
                'path': pdf_path,
                'relative_path': rel_path,
                'document_type': doc_type,
                'document_category': doc_category,
                'char_count': len(text),
                'page_count': len(reader.pages),
                'page_texts': page_texts  # Store for page number tracking
            })
            print(f"   ✅ {os.path.basename(pdf_path)} [{doc_type}]: {len(text):,} chars, {len(reader.pages)} pages")
        except Exception as e:
            print(f"   ❌ Error loading {os.path.basename(pdf_path)}: {e}")
    
    print()
    print(f"✅ Successfully loaded {len(documents)} documents")
    return documents

def add_document_context(chunk_text: str, doc: dict) -> str:
    """
    Add document context prefix to chunk for better semantic matching. Returns chunk text with context.
    
    Params:
    - chunk_text: Text of the chunk
    - doc: Document metadata dictionary
    
    Returns:
    - Chunk text prefixed with document context
    """
    # Extract document title from filename (remove .pdf, replace _ with spaces)
    doc_title = doc['source'].replace('.pdf', '').replace('_', ' ')
    
    # Create context prefix
    context_prefix = f"[Document: {doc_title} | Type: {doc['document_type']}]\n\n"
    
    # Prepend context to chunk
    return context_prefix + chunk_text

def split_documents(documents: list, chunk_size: int = 1800, chunk_overlap: int = 350, min_chunk_size: int = 50):
    """
    Split documents into chunks with enhanced metadata and filtering. Returns tuple of (chunks, metadatas).
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]  # Define separator / priority
    )
    
    print(f"📝 Splitting documents into chunks...")
    print(f"   Chunk size: {chunk_size} characters (optimized for better context)")
    print(f"   Chunk overlap: {chunk_overlap} characters (~{int(chunk_overlap/chunk_size*100)}%)")
    print(f"   Minimum chunk size: {min_chunk_size} characters (filtering smaller chunks)")
    print()
    
    all_chunks = []
    all_metadatas = []
    filtered_count = 0
    
    for doc in documents:
        # Split into chunks
        chunks = text_splitter.split_text(doc['text'])
        
        # Process each chunk
        for chunk_index, chunk_text in enumerate(chunks):
            # Filter out chunks that are too small or mostly whitespace
            chunk_clean = chunk_text.strip()
            if len(chunk_clean) < min_chunk_size:
                filtered_count += 1
                continue
            
            # Check if chunk is mostly whitespace/punctuation
            alpha_chars = sum(1 for c in chunk_clean if c.isalnum())
            if alpha_chars < min_chunk_size * 0.5:  # Less than 50% alphabetic
                filtered_count += 1
                continue
            
            # Add document context prefix for better semantic matching
            enriched_chunk = add_document_context(chunk_clean, doc)
            
            # Create enriched metadata
            metadata = {
                'source': doc['source'],
                'relative_path': doc['relative_path'],
                'document_type': doc['document_type'],
                'document_category': doc['document_category'],
                'chunk_index': chunk_index,
                'total_chunks': len(chunks),
                'chunk_length': len(chunk_clean),
                'page_count': doc.get('page_count', 0)
            }
            
            all_chunks.append(enriched_chunk)
            all_metadatas.append(metadata)
        
        print(f"   {doc['source']} [{doc['document_type']}]: {len(chunks)} chunks → {len([c for i, c in enumerate(chunks) if len(c.strip()) >= min_chunk_size])} valid")
    
    print()
    print(f"✅ Created {len(all_chunks):,} text chunks")
    if filtered_count > 0:
        print(f"   Filtered out {filtered_count} chunks (too small or low quality)")
    if all_chunks:
        avg_size = sum(len(c) for c in all_chunks) // len(all_chunks)
        min_size = min(len(c) for c in all_chunks)
        max_size = max(len(c) for c in all_chunks)
        print(f"📊 Chunk size stats:")
        print(f"   Average: {avg_size:,} characters")
        print(f"   Range: {min_size:,} - {max_size:,} characters")
    
    return all_chunks, all_metadatas

def create_vectorstore(chunks: list, metadatas: list, chroma_dir: str, embedding_model: str = "nomic-embed-text"):
    """
    Create embeddings and vector store in ChromaDB. Returns vector store.
    
    Params:
    - chunks: List of text chunks
    - metadatas: List of metadata dictionaries corresponding to chunks
    - chroma_dir: Directory to persist ChromaDB vector store
    - embedding_model: Name of the embedding model to use
    
    Returns:
    - Chroma vector store instance
    """
    print("🔄 Creating embeddings and storing in ChromaDB...")
    print(f"   Model: {embedding_model}")
    print(f"   Output directory: {chroma_dir}")
    print()
    print("⏳ This may take a few minutes...")
    print()
    
    embeddings = OllamaEmbeddings(model=embedding_model)
    
    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=chroma_dir
    )
    
    print("✅ Vector store created successfully!")
    return vectorstore

def verify_vectorstore(chroma_dir: str, embedding_model: str = "nomic-embed-text"):
    """
    Verify the created vector store.
    
    Params:
    - chroma_dir: Directory where the ChromaDB vector store is persisted
    - embedding_model: Name of the embedding model used
    
    Returns:
    - Chroma vector store instance
    """
    print("🔍 Verifying vector store...")
    print()
    
    embeddings = OllamaEmbeddings(model=embedding_model)
    vectorstore = Chroma(
        persist_directory=chroma_dir,
        embedding_function=embeddings
    )
    
    # Get collection info
    collection = vectorstore._collection
    count = collection.count()
    
    print(f"✅ Vector store verified")
    print(f"   Total vectors: {count:,}")
    print()
    
    # Test a sample query
    print("🧪 Testing sample query...")
    test_query = "What is AI Agent Insure?"
    results = vectorstore.similarity_search(test_query, k=3)
    
    print(f"   Query: '{test_query}'")
    print(f"   Retrieved {len(results)} documents:")
    for i, doc in enumerate(results, 1):
        preview = doc.page_content[:120].replace('\n', ' ')
        source = doc.metadata.get('source', 'Unknown')
        doc_type = doc.metadata.get('document_type', 'unknown')
        chunk_idx = doc.metadata.get('chunk_index', '?')
        print(f"   {i}. [{doc_type}] {source} (chunk {chunk_idx})")
        print(f"      {preview}...")
    print()
    return vectorstore

def show_directory_tree(directory_path: str, prefix: str = "", is_last: bool = True):
    """
    Display directory tree structure. Recursively prints a visual tree representation.
    
    Params:
    - directory_path: Path to the directory
    - prefix: Prefix string for tree structure (used in recursion)
    - is_last: Boolean indicating if the current item is the last in its level
    
    Returns:
    - None
    
    Throws:
    - PermissionError if directory cannot be accessed
    """
    path_obj = Path(directory_path)
    
    if prefix == "":
        print(f"📁 {path_obj.name}/")
    
    try:
        items = sorted(path_obj.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            current_prefix = "└── " if is_last_item else "├── "
            next_prefix = "    " if is_last_item else "│   "
            
            if item.is_dir():
                print(f"{prefix}{current_prefix}📁 {item.name}/")
                show_directory_tree(item, prefix + next_prefix, is_last_item)
            else:
                print(f"{prefix}{current_prefix}📄 {item.name}")
    except PermissionError:
        pass

def main():
    """
    Main function to create and populate the vector store.
    
    Returns:
    - None
    """
    print("=" * 70)
    print("Creating AI Agent Insure - Knowledge Base Vector Store")
    print("=" * 70)
    print()
    
    # Define paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    pdf_dir = project_root / "knowledge-base"
    chroma_dir = project_root / "vector-store" / "chroma_db"
    
    # Configuration - Optimized (after testing)for better RAG retrieval
    CHUNK_SIZE = 1800  # Increased from 1000 for better context preservation
    CHUNK_OVERLAP = 350  # Increased from 200 (~20% overlap for context continuity)
    MIN_CHUNK_SIZE = 50  # Filter out chunks smaller than this
    EMBEDDING_MODEL = "nomic-embed-text"
    
    print(f"📁 Project root: {project_root}")
    print(f"📁 PDF directory: {pdf_dir}")
    print(f"📁 Vector store output: {chroma_dir}")
    print()
    
    # Verify PDF directory exists
    if not pdf_dir.exists():
        print(f"❌ PDF directory not found: {pdf_dir}")
        print("Please ensure the knowledge-base folder exists with PDF files.")
        sys.exit(1)
    
    # Show directory structure
    print("📂 Knowledge base structure:")
    show_directory_tree(pdf_dir)
    print()
    
    # Delete existing vector store if it exists
    if chroma_dir.exists():
        print(f"🗑️  Removing existing vector store: {chroma_dir}")
        shutil.rmtree(chroma_dir)
        print("✅ Existing vector store removed")
        print()
    
    # Create parent directory
    chroma_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # Load PDFs
    print("=" * 70)
    print("Step 1: Loading PDF Documents")
    print("=" * 70)
    print()
    documents = load_pdfs(str(pdf_dir))
    
    if not documents:
        print("❌ No documents loaded. Exiting.")
        sys.exit(1)
    
    total_chars = sum(doc['char_count'] for doc in documents)
    print(f"📊 Total content: {total_chars:,} characters")
    print()
    
    # Split documents
    print("=" * 70)
    print("Step 2: Splitting Documents into Chunks")
    print("=" * 70)
    print()
    chunks, metadatas = split_documents(documents, CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE)
    print()
    
    # Create vector store
    print("=" * 70)
    print("Step 3: Creating Vector Store with Embeddings")
    print("=" * 70)
    print()
    vectorstore = create_vectorstore(chunks, metadatas, str(chroma_dir), EMBEDDING_MODEL)
    vector_count = vectorstore._collection.count()
    print(f"📊 Total vectors in database: {vector_count:,}")
    print()
    
    # Verify
    print("=" * 70)
    print("Step 4: Verification")
    print("=" * 70)
    print()
    verify_vectorstore(str(chroma_dir), EMBEDDING_MODEL)
    
    # Summary
    print("=" * 70)
    print("✅ Vector Store Created Successfully!")
    print("=" * 70)
    print()
    print(f"📊 Summary:")
    print(f"   Documents processed: {len(documents)}")
    print(f"   Text chunks created: {len(chunks):,}")
    print(f"   Vectors stored: {vector_count:,}")
    print(f"   Embedding model: {EMBEDDING_MODEL}")
    print(f"   Chunk size: {CHUNK_SIZE} chars (overlap: {CHUNK_OVERLAP} chars)")
    print()
    
    # Document type breakdown
    doc_type_counts = {}
    for doc in documents:
        doc_type = doc['document_type']
        doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
    if doc_type_counts:
        print(f"📂 Documents by type:")
        for doc_type, count in sorted(doc_type_counts.items()):
            print(f"   {doc_type}: {count} documents")
        print()
    print(f"📁 Vector store location: {chroma_dir}")
    print()
    print("🚀 You can now run the application:")
    print(f"   cd {project_root / 'agent'}")
    print("   python app.py")
    print()

if __name__ == "__main__":
    main()
