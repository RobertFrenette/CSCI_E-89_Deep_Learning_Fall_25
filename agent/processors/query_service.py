"""
Query Service
Instantiates the RAGProcessor and SQLProcessor instances and uses them to handle queries.
Used in the app.py to handle queries.

Service layer that orchestrates the complete query processing pipeline:
- Input handling (audio/text)
- Query routing (SQL vs RAG)
- Query execution
- Response formatting
- Audio generation

Coordinates domain processors (RAG, SQL, Audio) to handle queries.
"""

import logging
from typing import Optional, Tuple
from agent.processors.audio_processor import transcribe_audio, text_to_speech
from agent.routing.query_router import detect_query_type
from agent.routing.sql_query_handler import SQLQueryHandler
from agent.processors.rag_processor import RAGProcessor

logger = logging.getLogger(__name__)


class QueryService:
    """
    Service that orchestrates the complete query processing pipeline.
    
    Coordinates domain processors to handle:
    - Audio transcription (if audio input)
    - Query routing (SQL vs RAG)
    - Query execution via domain processors
    - Response formatting
    - Audio response generation (for RAG queries)

    Attributes:
        whisper_model: Loaded Whisper model for speech-to-text
        sql_query_handler: SQLQueryHandler instance (can be None)
        rag_processor: RAGProcessor instance for document queries

    Methods:
        process_query: Process user query from text or audio input
        _handle_input: Handle input processing (audio transcription or text extraction)
        _process_sql_query: Process SQL database query
        _process_rag_query: Process RAG document query
    """
    
    def __init__(
        self,
        whisper_model,
        sql_query_handler: Optional[SQLQueryHandler],
        rag_processor: RAGProcessor
    ):
        """
        Initialize the query processor.
        
        Args:
            whisper_model: Loaded Whisper model for speech-to-text
            sql_query_handler: SQLQueryHandler instance (can be None)
            rag_processor: RAGProcessor instance for document queries
            
        Returns:
            None
        """
        self.whisper_model = whisper_model
        self.sql_query_handler = sql_query_handler
        self.rag_processor = rag_processor
    
    def process_query(
        self, 
        text_input: Optional[str], 
        audio_input: Optional[str]
    ) -> Tuple[str, str, Optional[str]]:
        """
        Process user query from text or audio input.
        
        Handles the complete pipeline:
        1. Input processing (audio transcription or text extraction)
        2. Query routing (SQL vs RAG detection)
        3. Query execution (SQL database or RAG system)
        4. Response formatting
        5. Audio generation (for RAG queries only)
        
        Args:
            text_input: Text question from user (can be None)
            audio_input: Audio file path from user (can be None)
            
        Returns:
            Tuple of (cleared_text_input, response_text, audio_response)
            - cleared_text_input: Empty string (cleared for UI)
            - response_text: Formatted answer with sources
            - audio_response: Path to audio file, or None
        """
        try:
            # Step 1: Handle input (audio or text)
            question, is_audio_input, error_msg = self._handle_input(text_input, audio_input)
            if question is None:
                if error_msg:
                    return "", error_msg, None
                return "", "❌ Please provide either text or audio input.", None
            
            # Step 2: Route query (SQL vs RAG)
            query_type, cleaned_question = detect_query_type(question)
            logger.debug(f"Query type detected: {query_type}")
            
            # Step 3: Execute query based on type
            if query_type == 'sql':
                answer_with_sources, audio_output = self._process_sql_query(cleaned_question)
            else:
                answer_with_sources, audio_output = self._process_rag_query(cleaned_question)
            
            # Step 4: Format final response
            if is_audio_input:
                final_response = f"🎤 You asked: {question}\n\n{answer_with_sources}"
            else:
                final_response = answer_with_sources
            
            return "", final_response, audio_output
            
        except Exception as e:
            error_msg = f"❌ Unexpected error: {str(e)}"
            logger.error(f"Unexpected error in process_query: {e}", exc_info=True)
            return "", error_msg, None
    
    def _handle_input(
        self, 
        text_input: Optional[str], 
        audio_input: Optional[str]
    ) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        Handle input processing (audio transcription or text extraction).
        
        Args:
            text_input: Text input (can be None)
            audio_input: Audio input path (can be None)
            
        Returns:
            Tuple of (question, is_audio_input, error_message)
            - question: Extracted/transcribed question, or None if invalid
            - is_audio_input: True if audio was processed, False if text
            - error_message: Error message if processing failed, or None
        """
        is_audio_input = audio_input is not None
        
        if is_audio_input:
            logger.info("Processing audio input")
            try:
                question = transcribe_audio(audio_input, self.whisper_model)
                if not question:
                    logger.warning("Audio transcription returned empty result")
                    return None, True, "❌ Could not transcribe audio. Please check your microphone and try again."
                logger.info(f"Transcribed audio: {question[:100]}...")
                return question, True, None
            except Exception as e:
                logger.error(f"Audio transcription failed: {e}")
                return None, True, f"❌ Audio transcription error: {str(e)}"
        elif text_input:
            question = text_input
            logger.info(f"Processing text input: {question[:100]}...")
            return question, False, None
        else:
            return None, False, None
    
    def _process_sql_query(self, question: str) -> Tuple[str, Optional[str]]:
        """
        Process SQL database query.
        
        Args:
            question: User's question (already cleaned)
            
        Returns:
            Tuple of (formatted_response, audio_output)
            - formatted_response: Formatted answer
            - audio_output: Always None for SQL queries
        """
        if not self.sql_query_handler:
            return "SQL database is not available.", None
        
        logger.info("Routing to SQL database")
        try:
            sql_response = self.sql_query_handler.handle_query(question)
            answer_with_sources = f"📊 Database Query Results:\n\n{sql_response}"
            return answer_with_sources, None  # Skip audio for database queries
        except Exception as e:
            logger.error(f"SQL query failed: {e}", exc_info=True)
            raise RuntimeError(f"Database query error: {str(e)}")
    
    def _process_rag_query(self, question: str) -> Tuple[str, Optional[str]]:
        """
        Process RAG document query.
        
        Args:
            question: User's question (already cleaned)
            
        Returns:
            Tuple of (formatted_response, audio_output)
            - formatted_response: Answer with sources
            - audio_output: Path to audio file, or None if generation failed
        """
        logger.info("Routing to RAG system")
        try:
            # Execute RAG query
            answer_with_sources, sources, result = self.rag_processor.get_answer_with_sources(question)
            answer_text = result['answer']
            logger.debug(f"RAG sources: {sources}")
            
            # Generate audio response for RAG queries
            audio_output = None
            try:
                audio_output = text_to_speech(answer_text)
                if not audio_output:
                    logger.warning("Text-to-speech returned no audio")
            except Exception as e:
                logger.error(f"Text-to-speech failed: {e}")
                audio_output = None
            
            return answer_with_sources, audio_output
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            raise RuntimeError(f"Document search error: {str(e)}")
