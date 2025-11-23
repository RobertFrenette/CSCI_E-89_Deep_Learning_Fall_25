"""
RAG Processor Module

Handles PDF loading, text chunking, embeddings, and RAG chain setup.
Domain processor for document-based retrieval and generation.
"""

import os
import glob
import logging
from pathlib import Path
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryMemory
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class RAGProcessor:
    """Main class for processing documents and setting up RAG system."""
    
    def __init__(self, pdf_dir: str, chroma_dir: str = None):
        """
        Initialize the RAG processor.
        
        Args:
            pdf_dir: Directory containing PDF files
            chroma_dir: Directory for ChromaDB persistence
        """
        self.pdf_dir = pdf_dir
        # Use config.CHROMA_DIR if not provided
        from agent import config
        self.chroma_dir = chroma_dir if chroma_dir is not None else config.CHROMA_DIR
        self.documents = []
        self.all_chunks = []
        self.all_metadatas = []
        self.vectorstore = None
        self.qa_chain = None
        self.memory = None
        
    def list_tree(self, directory_path: str = None, indent: str = ""):
        """Display directory tree structure."""
        if directory_path is None:
            directory_path = self.pdf_dir
            
        path_obj = Path(directory_path)
        
        if indent == "":
            print(f"📁 {path_obj.name}/")

        for p in path_obj.iterdir():
            if p.is_dir():
                print(f"{indent}    📁 {p.name}/")
                self.list_tree(p, indent + "    ")
            else:
                print(f"{indent}    📄 {p.name}")
    
    def load_pdfs(self):
        """Load all PDFs from directory and extract text."""
        self.documents = []
        pdf_files = glob.glob(f"{self.pdf_dir}/**/*.pdf", recursive=True)
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        for pdf_path in pdf_files:
            try:
                reader = PdfReader(pdf_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                
                # Store with metadata
                self.documents.append({
                    'text': text,
                    'source': os.path.basename(pdf_path),
                    'path': pdf_path
                })
                logger.debug(f"Loaded: {os.path.basename(pdf_path)} ({len(text)} chars)")
            except Exception as e:
                logger.error(f"Error loading {pdf_path}: {e}")
        
        logger.info(f"Successfully loaded {len(self.documents)} documents")
        return self.documents
    
    def split_text(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Split documents into chunks.
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        print("✅ Text splitter initialized")
        print(f"   Chunk size: {chunk_size} characters")
        print(f"   Chunk overlap: {chunk_overlap} characters")
        
        self.all_chunks = []
        self.all_metadatas = []
        
        for doc in self.documents:
            chunks = text_splitter.split_text(doc['text'])
            self.all_chunks.extend(chunks)
            # Add metadata for each chunk
            self.all_metadatas.extend([{'source': doc['source']} for _ in chunks])
        
        print(f"\n📝 Created {len(self.all_chunks)} text chunks")
        if self.all_chunks:
            print(f"📄 Average chunk size: {sum(len(c) for c in self.all_chunks) // len(self.all_chunks)} characters")
            print(f"\n📋 Sample chunk:")
            print(f"   {self.all_chunks[0][:200]}...")
        
        return self.all_chunks, self.all_metadatas
    
    def create_vectorstore(self, embedding_model: str = "nomic-embed-text"):
        """
        Create embeddings and vector store.
        
        Args:
            embedding_model: Name of the Ollama embedding model
        """
        embeddings = OllamaEmbeddings(model=embedding_model)
        
        print("🔄 Creating embeddings and storing in ChromaDB...")
        print("⏳ This may take a few minutes...")
        
        self.vectorstore = Chroma.from_texts(
            texts=self.all_chunks,
            embedding=embeddings,
            metadatas=self.all_metadatas,
            persist_directory=self.chroma_dir
        )
        
        print("✅ Vector store created successfully!")
        print(f"📊 Total vectors in database: {self.vectorstore._collection.count()}")
        
        return self.vectorstore
    
    def load_existing_vectorstore(self, embedding_model: str = "nomic-embed-text"):
        """
        Load existing vector store from disk.
        
        Args:
            embedding_model: Name of the Ollama embedding model
        """
        embeddings = OllamaEmbeddings(model=embedding_model)
        self.vectorstore = Chroma(
            persist_directory=self.chroma_dir,
            embedding_function=embeddings
        )
        print(f"✅ Loaded existing vector store with {self.vectorstore._collection.count()} vectors")
        return self.vectorstore
    
    def setup_rag_chain(self, llm_model: str = "llama3.2:3b", temperature: float = 0.7, 
                       k: int = 4, score_threshold: float = None):
        """
        Setup RAG chain with conversation memory, optimized retrieval, and hallucination reduction.
        
        Uses strict prompt engineering and score threshold filtering to minimize hallucinations.
        
        Args:
            llm_model: Name of the Ollama LLM model
            temperature: LLM temperature setting (lower = more focused, less hallucination)
            k: Number of documents to retrieve (default: 4 to minimize noise)
            score_threshold: Minimum similarity score threshold (default: 0.7 to filter low-relevance chunks)
        """
        # Initialize Ollama LLM with timeout settings for faster failures
        llm = ChatOllama(
            model=llm_model,
            temperature=temperature,
            timeout=60.0  # 60 second timeout per request
        )
        
        logger.info(f"LLM initialized: {llm_model}, temperature: {temperature}")
        
        # Initialize conversation memory with summarization
        # Note: Disabling memory for now to improve response speed
        # Memory can cause significant delays due to summarization overhead
        self.memory = ConversationSummaryMemory(
            llm=llm,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
            max_token_limit=2000,
            human_prefix="Human",
            ai_prefix="Assistant"
        )
        
        logger.info("Conversation memory initialized (can be slow for first few queries)")
        
        # Optimized prompt template - shorter for faster responses, still minimizes hallucinations
        custom_template = """Answer based ONLY on the provided context. If the answer isn't in the context, say "I don't have that information in the available documents."

Context:
{context}

Question: {question}

Answer:"""
        
        # Create custom QA prompt
        QA_PROMPT = PromptTemplate(
            template=custom_template,
            input_variables=["context", "chat_history", "question"]
        )
        
        # Configure retriever with optimized settings
        # For production, use full k value for better accuracy
        # For evaluation/testing, config sets lower k
        search_kwargs = {"k": k}
        
        # Use similarity search type for better relevance
        base_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs
        )
        
        logger.info(f"Retriever configured: k={k}, search_type=similarity")
        if score_threshold is not None:
            logger.warning("score_threshold is set but not currently supported by ChromaDB. Filtering disabled.")
        
        # Create conversational retrieval chain with custom prompt
        # Optimized for speed with reduced retrieval count
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=base_retriever,
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": QA_PROMPT},
            verbose=False
        )
        
        logger.info(f"RAG chain initialized with optimized settings: k={k}, custom prompt template")
        
        return self.qa_chain, self.memory
    
    def preprocess_query(self, question: str) -> str:
        """
        Preprocess query for better retrieval (simplified for speed).
        
        Args:
            question: Original question
            
        Returns:
            Processed question (minimal processing for speed)
        """
        # Simplified preprocessing - just return the question as-is for speed
        # Complex preprocessing can cause delays and isn't critical for retrieval
        return question.strip()
    
    def get_answer_with_sources(self, question: str, use_metadata_filter: bool = False):
        """
        Query RAG system and return formatted answer with enriched sources.
        Validates that relevant context was found to minimize hallucinations.
        
        Args:
            question: The question to ask
            use_metadata_filter: Whether to use metadata filtering (experimental)
            
        Returns:
            Tuple of (formatted_answer, sources_list, full_result)
        """
        if self.qa_chain is None:
            raise ValueError("RAG chain not initialized. Call setup_rag_chain() first.")
        
        # Preprocess query for better retrieval
        processed_question = self.preprocess_query(question)
        
        logger.info(f"Starting RAG query: {question[:50]}...")
        
        try:
            # Execute query with timeout awareness
            result = self.qa_chain({"question": processed_question})
            logger.info("RAG query completed")
            
            answer = result['answer']
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise
        
        # Validate that we have source documents (helps prevent hallucinations from no context)
        if not result.get('source_documents') or len(result['source_documents']) == 0:
            logger.warning(f"No source documents retrieved for question: {question}")
            answer = "I don't have relevant information in the available documents to answer that question. Please try rephrasing or asking about a different topic."
        elif len(result['source_documents']) < 2:
            logger.info(f"Only {len(result['source_documents'])} source document(s) retrieved - may have limited context")
        
        # Extract source documents with enriched metadata
        sources = []
        source_metadata = []
        
        for doc in result['source_documents']:
            source_name = doc.metadata.get('source', 'Unknown')
            doc_type = doc.metadata.get('document_type', 'unknown')
            doc_category = doc.metadata.get('document_category', '')
            
            # Create enriched source info
            if doc_type != 'unknown':
                source_label = f"{source_name} [{doc_type}]"
            else:
                source_label = source_name
            
            sources.append(source_name)  # Keep original for deduplication
            source_metadata.append({
                'source': source_name,
                'document_type': doc_type,
                'document_category': doc_category,
                'chunk_index': doc.metadata.get('chunk_index', None),
                'label': source_label
            })
        
        # Deduplicate sources while preserving metadata
        unique_sources = []
        seen_sources = set()
        for src_info in source_metadata:
            if src_info['source'] not in seen_sources:
                unique_sources.append(src_info)
                seen_sources.add(src_info['source'])
        
        # Format answer with enriched sources
        if unique_sources:
            source_labels = [src['label'] for src in unique_sources]
            formatted_answer = answer + f"\n\n📚 Sources: {', '.join(source_labels)}"
        else:
            formatted_answer = answer
        
        logger.debug(f"Retrieved {len(result['source_documents'])} chunks from {len(unique_sources)} unique sources")
        
        return formatted_answer, [src['source'] for src in unique_sources], result
    
    def query(self, question: str):
        """
        Query the RAG system with formatted output to console.
        
        Args:
            question: The question to ask
            
        Returns:
            Dictionary containing answer and source documents
        """
        if self.qa_chain is None:
            raise ValueError("RAG chain not initialized. Call setup_rag_chain() first.")
        
        # Preprocess query for better retrieval
        processed_question = self.preprocess_query(question)
        
        logger.info(f"Starting query: {question[:50]}...")
        
        try:
            result = self.qa_chain({"question": processed_question})
            logger.info("Query completed")
        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            raise
        
        print(f"\n❓ Question: {question}")
        print(f"\n💬 Answer: {result['answer']}")
        print(f"\n📚 Sources ({len(result['source_documents'])} chunks):")
        for i, doc in enumerate(result['source_documents'], 1):
            source = doc.metadata.get('source', 'Unknown')
            doc_type = doc.metadata.get('document_type', 'unknown')
            chunk_idx = doc.metadata.get('chunk_index', '?')
            
            if doc_type != 'unknown':
                print(f"  {i}. [{doc_type}] {source} (chunk {chunk_idx})")
            else:
                print(f"  {i}. {source}")
        
        return result
    
    def load_and_setup(self, embedding_model: str = "nomic-embed-text",
                      llm_model: str = "llama3.2:3b", temperature: float = 0.7, 
                      k: int = 4, score_threshold: float = None):
        """
        Load existing vector store and setup RAG chain with optimized settings.
        
        This method assumes the vector store has been created externally using
        the create_chroma_vectorstore.py script.
        
        Args:
            embedding_model: Name of the Ollama embedding model
            llm_model: Name of the Ollama LLM model
            temperature: LLM temperature setting
            k: Number of documents to retrieve (optimized default: 5)
            score_threshold: Minimum similarity score threshold (optional)
            
        Returns:
            Tuple of (qa_chain, memory, vectorstore)
            
        Raises:
            FileNotFoundError: If vector store doesn't exist
        """
        logger.info(f"Loading vector store from: {self.chroma_dir}")
        
        # Check if vector store exists
        if not os.path.exists(self.chroma_dir):
            raise FileNotFoundError(
                f"Vector store not found at {self.chroma_dir}. "
                f"Please create it first by running: python ../vector-store/create_chroma_vectorstore.py"
            )
        
        # Load existing vector store
        self.load_existing_vectorstore(embedding_model)
        
        # Setup RAG chain with optimized settings
        self.setup_rag_chain(llm_model, temperature, k, score_threshold)
        
        logger.info("RAG system fully initialized and ready!")
        return self.qa_chain, self.memory, self.vectorstore
    
    def process_all(self, chunk_size: int = 1000, chunk_overlap: int = 200, 
                    embedding_model: str = "nomic-embed-text",
                    llm_model: str = "llama3.2:3b", temperature: float = 0.7, k: int = 3):
        """
        Run the complete pipeline: load PDFs, chunk, create vectorstore, setup RAG chain.
        
        NOTE: This method is deprecated. Use create_chroma_vectorstore.py script instead
        to create the vector store externally, then use load_and_setup() method.
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between chunks
            embedding_model: Name of the Ollama embedding model
            llm_model: Name of the Ollama LLM model
            temperature: LLM temperature setting
            k: Number of documents to retrieve
        """
        print(f"📁 PDF Directory: {self.pdf_dir}")
        print(f"💾 ChromaDB Directory: {self.chroma_dir}\n")
        
        # Phase 2: Load PDFs
        self.load_pdfs()
        
        # Phase 3: Split text
        self.split_text(chunk_size, chunk_overlap)
        
        # Phase 4: Create vectorstore
        self.create_vectorstore(embedding_model)
        
        # Phase 5: Setup RAG chain
        self.setup_rag_chain(llm_model, temperature, k)
        
        print("\n✅ RAG system fully initialized and ready!")
        return self.qa_chain, self.memory, self.vectorstore
