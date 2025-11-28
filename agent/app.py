"""
Main application file for the Multimodal RAG Chatbot
Run this file to start the application
"""

import os
import sys
from pathlib import Path

# Add project root to Python path to enable absolute imports
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
import whisper
import gradio as gr
from agent.processors.rag_processor import RAGProcessor
from agent.processors.sql_processor import SQLProcessor
from agent.logger import setup_logging
from agent.ui import create_interface
from agent.routing.sql_query_handler import SQLQueryHandler
from agent.processors.query_service import QueryService
from agent import config

# Setup logging
logger = logging.getLogger(__name__)

class RAGChatbotApp:
    """
    Main application class for the multimodal RAG chatbot.

    Attributes:
        processor: RAGProcessor instance
        qa_chain: RAG chain
        memory: Conversation memory
        vectorstore: ChromaDB vector store
        whisper_model: Whisper model
        sql_processor: SQLProcessor instance
        sql_query_handler: SQLQueryHandler instance
        query_processor: QueryService instance

    Methods:
        initialize_audio: Initialize Whisper model for speech-to-text
        initialize_sql: Initialize SQL database connection and create SQLQueryHandler instance
        initialize_rag: Initialize the RAG processing system and set up RAG chain
        process_query: Process user query from text or audio input
        clear_conversation: Clear conversation memory and reset UI inputs
        run: Run the complete application. Optionally run a test query

    Raises:
        RuntimeError: If Whisper model fails to load, SQL database fails to initialize, or RAG system fails to initialize
        FileNotFoundError: If vector store not found
    """
    
    def __init__(self):
        """
        Initialize the application and set all component attributes to None.
        """
        self.processor = None
        self.qa_chain = None
        self.memory = None
        self.vectorstore = None
        self.whisper_model = None
        self.sql_processor = None
        self.sql_query_handler = None
        self.query_processor = None

    def initialize_audio(self):
        """
        Initialize Whisper model for speech-to-text.
        Raises RuntimeError if Whisper model fails to load.
        """
        try:
            logger.info(f"Loading Whisper model: {config.WHISPER_MODEL}")
            self.whisper_model = whisper.load_model(config.WHISPER_MODEL)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError(f"Could not initialize audio processing: {e}")
    
    def initialize_sql(self):
        """
        Initialize SQL database connection and create SQLQueryHandler instance.
        """
        logger.info("Initializing SQL database...")
        try:
            self.sql_processor = SQLProcessor(config.SQL_DB_PATH)
            self.sql_processor.connect()
            
            # Create SQL query handler
            self.sql_query_handler = SQLQueryHandler(self.sql_processor)
            
            # Test connection by counting insureds and claims
            insured_count = self.sql_processor.count_insureds()
            claims_count = self.sql_processor.count_claims()
            logger.info(f"Database connected: {insured_count} insureds, {claims_count} claims")
            logger.info("SQL database initialized successfully")
        except FileNotFoundError as e:
            logger.warning(f"Database not found: {e}")
            logger.warning("SQL database queries will not be available")
            self.sql_processor = None
            self.sql_query_handler = None
        except Exception as e:
            logger.error(f"Failed to initialize SQL database: {e}")
            self.sql_processor = None
            self.sql_query_handler = None
    
    def initialize_rag(self):
        """
        Initialize the RAG processing system and set up RAG chain.
        Raises RuntimeError if vector store not found or initialization fails.
        """
        logger.info("Initializing RAG system...")
        
        try:
            # Create RAG processor
            self.processor = RAGProcessor(
                pdf_dir=config.PDF_DIR,
                chroma_dir=config.CHROMA_DIR
            )
            
            # Load existing vector store and setup RAG chain with optimized settings
            self.qa_chain, self.memory, self.vectorstore = self.processor.load_and_setup(
                embedding_model=config.EMBEDDING_MODEL,
                llm_model=config.LLM_MODEL,
                temperature=config.TEMPERATURE,
                k=config.RETRIEVAL_K,
                score_threshold=getattr(config, 'RETRIEVAL_SCORE_THRESHOLD', None)
            )
            
            vector_count = self.vectorstore._collection.count()
            logger.info(f"RAG system initialized with {vector_count} vectors")
        except FileNotFoundError as e:
            logger.error(f"Vector store not found: {e}")
            logger.error(f"Please run 'python ../vector-store/create_chroma_vectorstore.py' first")
            raise RuntimeError(
                f"Vector store not found at {config.CHROMA_DIR}. "
                f"Please create it first by running: python ../vector-store/create_chroma_vectorstore.py"
            )
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}", exc_info=True)
            raise RuntimeError(f"Could not initialize RAG system: {e}")
    
    def process_query(self, text_input, audio_input):
        """
        Process user query from text or audio input. Delegates to QueryProcessor service.
        Returns tuple of (cleared_text_input, response_text, audio_response).
        """
        if not self.query_processor:
            error_msg = "Query processor not initialized. Please wait for initialization to complete."
            logger.error(error_msg)
            return "", f"❌ {error_msg}", None
        
        return self.query_processor.process_query(text_input, audio_input)
    
    def clear_conversation(self):
        """
        Clear conversation memory and reset UI inputs.
        Returns tuple of cleared inputs and outputs.
        """
        try:
            if self.memory:
                self.memory.clear()
                logger.info("Conversation history cleared")
            return "", None, "", None
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return "", None, "", None
    
    def run(self, run_test=True):
        """
        Run the complete application. Optionally run a test query.
        """
        print("=" * 60)
        print("🚀 Starting RAG Chatbot Application")
        print("=" * 60)
        print()
        
        # Initialize audio
        self.initialize_audio()
        
        # Initialize SQL database
        self.initialize_sql()
        
        # Initialize RAG
        self.initialize_rag()
        
        # Initialize query service (after all components are ready)
        self.query_processor = QueryService(
            whisper_model=self.whisper_model,
            sql_query_handler=self.sql_query_handler,
            rag_processor=self.processor
        )
        
        # Test query (optional)
        if run_test:
            print("🔍 Running test query...\n")
            test_question = config.EXAMPLE_QUESTIONS[0] if hasattr(config, "EXAMPLE_QUESTIONS") else "What is AI Agent Insure?"
            result = self.processor.query(test_question)
            # Show retrieved chunks with enhanced metadata
            print(f"\n🔍 Retrieved {len(result['source_documents'])} chunks:")
            for i, doc in enumerate(result['source_documents'], 1):
                preview = doc.page_content[:150].replace('\n', ' ')
                source = doc.metadata.get('source', 'Unknown')
                doc_type = doc.metadata.get('document_type', 'unknown')
                chunk_idx = doc.metadata.get('chunk_index', '?')
                if doc_type != 'unknown':
                    print(f"  {i}. [{doc_type}] {source} (chunk {chunk_idx})")
                else:
                    print(f"  {i}. {source}")
                print(f"     Preview: {preview}...")
            print()
        
        # Create and launch Gradio interface
        print(f"🌍 Access the app at: http://{config.SERVER_NAME}:{config.SERVER_PORT}")
        print("🌐 Launching Gradio Interface")
        print("=" * 60)
        print()
        
        # Set favicon using absolute path
        favicon_path = os.path.join(os.path.dirname(__file__), "assets", "favicon.png")
        
        # Create the Gradio interface
        demo = create_interface(self)
        
        # Launch the interface
        demo.launch(
            share=config.SHARE,
            debug=config.DEBUG,
            server_name=config.SERVER_NAME,
            server_port=config.SERVER_PORT,
            favicon_path=favicon_path
        )

def main():
    """
    Main entry point for the application. Sets up logging, creates RAGChatbotApp instance, and launches the application.
    """
    setup_logging()
    logger.info("Application starting...")
    
    try:
        app = RAGChatbotApp()
        app.run(run_test=True)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
