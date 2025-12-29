"""
RAG (Retrieval-Augmented Generation) Engine
Combines vector search with LLM generation for intelligent question answering
"""
import logging
from typing import List, Dict, Optional, Any
from .vector_search import VectorSearch
from .ollama_client import OllamaClient
from .chromadb_client import ChromaDBClient

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    RAG Engine for insurance domain question answering
    Combines ChromaDB vector search with Ollama LLM generation
    """
    
    # Default system prompt for insurance domain
    DEFAULT_SYSTEM_PROMPT = """You are an expert AI assistant specialized in insurance and risk management for AI Agent Insure. 
Your role is to provide accurate, clear, and professional answers based EXCLUSIVELY on the provided context from insurance documentation.

CRITICAL INSTRUCTIONS:
1. **Always provide factual information. Don't guess.** - Only use information explicitly found in the provided context. Never make up or infer information that isn't directly stated.
2. **If you don't know the answer, say so** - If the provided context doesn't contain enough information to answer the question, clearly state "I don't have enough information in the provided documentation to answer this question" or "Based on the provided documentation, I cannot determine [specific aspect]"
3. **Answer ONLY from the provided context** - Do not use any external knowledge or make assumptions beyond what is explicitly stated
4. **Do not specify or list specific documents in the response** - Do not mention document names within the body of your answer. Instead, list all source documents at the end of your response in a "Sources:" section
5. **Be comprehensive** - Provide detailed, well-structured answers that fully address the question when information is available
6. **Be professional** - Use proper insurance terminology and maintain a professional tone
7. **Structure your response** - Use bullet points, numbered lists, or clear paragraphs for readability
8. **Be specific** - Include relevant details, numbers, coverage types, and key features when available

When answering:
- Start with a direct answer to the question (or state that you don't have enough information)
- Provide supporting details from the context
- Cite the source documents
- If multiple documents contain relevant information, synthesize them coherently"""

    def __init__(
        self,
        chromadb_client: Optional[ChromaDBClient] = None,
        ollama_client: Optional[OllamaClient] = None,
        model: str = "llama3.1",
        collection_name: str = "knowledge_base",
        top_k: int = 5,
        max_context_length: int = 3000
    ):
        """
        Initialize RAG Engine
        
        Args:
            chromadb_client: ChromaDB client instance (creates new if None)
            ollama_client: Ollama client instance (creates new if None)
            model: Ollama model name to use
            collection_name: ChromaDB collection name
            top_k: Number of retrieved documents to use as context
            max_context_length: Maximum characters for context (to manage token limits)
        """
        self.chromadb_client = chromadb_client or ChromaDBClient()
        self.vector_search = VectorSearch(self.chromadb_client)
        self.ollama_client = ollama_client or OllamaClient()
        self.model = model
        self.collection_name = collection_name
        self.top_k = top_k
        self.max_context_length = max_context_length
        
        # Verify services are available
        if not self.ollama_client.check_health():
            logger.warning("⚠️  Ollama may not be accessible")
        else:
            logger.info(f"✅ Ollama is healthy, model '{self.model}' ready")
        if not self.chromadb_client.check_health():
            logger.warning("⚠️  ChromaDB may not be accessible")
    
    def _build_context(self, retrieved_docs: List[Dict]) -> str:
        """
        Build context string from retrieved documents, prioritizing high-relevance documents
        
        Args:
            retrieved_docs: List of retrieved document dictionaries
            
        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return ""
        
        # Sort by similarity (relevance) descending to prioritize most relevant docs
        sorted_docs = sorted(retrieved_docs, key=lambda x: x.get('similarity', 0), reverse=True)
        
        context_parts = []
        total_length = 0
        
        for i, doc in enumerate(sorted_docs, 1):
            doc_text = doc.get('document', '').strip()
            if not doc_text:
                continue
                
            metadata = doc.get('metadata', {})
            similarity = doc.get('similarity', 0)
            
            # Get source information - clean up the source name
            source = metadata.get('source', 'Unknown')
            # Extract just the filename if it's a path
            if '/' in source:
                source = source.split('/')[-1]
            if source.endswith('.pdf'):
                source = source[:-4]  # Remove .pdf extension
            
            source_dir = metadata.get('source_dir', '')
            
            # Format document with clear source attribution
            doc_entry = f"--- DOCUMENT {i}: {source}"
            if source_dir:
                doc_entry += f" (Category: {source_dir})"
            doc_entry += f" [Relevance Score: {similarity:.3f}] ---\n\n{doc_text}\n"
            
            # Check if adding this would exceed max length
            if total_length + len(doc_entry) > self.max_context_length:
                # Try to include at least part of this document if there's space
                remaining_space = self.max_context_length - total_length
                if remaining_space > 200:  # Only include if there's meaningful space
                    doc_entry = doc_entry[:remaining_space] + "\n[... content truncated due to length limit ...]"
                    context_parts.append(doc_entry)
                logger.warning(f"⚠️  Context length limit ({self.max_context_length} chars) reached, included {i-1} full documents and partial document {i}")
                logger.warning(f"   Total context length: {total_length + len(doc_entry)} chars (limit: {self.max_context_length})")
                break
            
            context_parts.append(doc_entry)
            total_length += len(doc_entry)
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """
        Build prompt with query and context
        
        Args:
            query: User query
            context: Retrieved context from vector store
            
        Returns:
            Formatted prompt
        """
        if not context:
            return f"""Question: {query}

Please answer the question. If you don't have enough information, please say so."""
        
        return f"""You have been provided with relevant documentation from AI Agent Insure's knowledge base. 
Use this information to provide a comprehensive and accurate answer to the user's question.

=== DOCUMENTATION CONTEXT ===
{context}

=== USER QUESTION ===
{query}

=== YOUR TASK ===
Provide a detailed, well-structured answer that:
1. Directly addresses the question (or clearly states if you don't have enough information)
2. Uses information ONLY from the documentation above - Never guess or make assumptions
3. Always provides factual information - If you don't know the answer, say so explicitly
4. Do NOT mention document names within the body of your answer - List all source documents at the end in a "Sources:" section
5. Is comprehensive and includes relevant details when available
6. Uses professional insurance terminology
7. If the documentation doesn't fully answer the question, clearly state what information is missing

Answer:"""
    
    def query(
        self,
        query: str,
        collection_name: Optional[str] = None,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        sql_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query using RAG pipeline
        
        Args:
            query: User question
            collection_name: Collection to search (defaults to instance default)
            top_k: Number of documents to retrieve (defaults to instance default)
            metadata_filter: Optional metadata filter for search
            system_prompt: Custom system prompt (defaults to insurance domain prompt)
            temperature: LLM temperature (0.0-1.0)
            stream: Whether to stream the response
            
        Returns:
            Dictionary with:
            - 'answer': Generated answer
            - 'sources': List of source documents used
            - 'model': Model used
            - 'retrieved_docs': Number of documents retrieved
            - 'context_length': Length of context used
        """
        collection = collection_name or self.collection_name
        k = top_k or self.top_k
        
        logger.info(f"Processing RAG query: '{query[:50]}...'")
        
        # Step 1: Retrieve relevant documents
        try:
            retrieved_docs = self.vector_search.search(
                query=query,
                collection_name=collection,
                n_results=k,
                metadata_filter=metadata_filter
            )
            logger.info(f"Retrieved {len(retrieved_docs)} documents")
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return {
                'answer': "I'm sorry, I couldn't retrieve information from the knowledge base. Please try again later.",
                'sources': [],
                'model': self.model,
                'retrieved_docs': 0,
                'context_length': 0,
                'error': str(e)
            }
        
        # Step 2: Build context from retrieved documents
        context_length = 0
        try:
            context = self._build_context(retrieved_docs)
            
            # Add SQL context if provided (for hybrid queries)
            if sql_context:
                context = f"{sql_context}\n\n---\n\nDocumentation Context:\n{context}"
            
            context_length = len(context)
            
            # Step 3: Build prompt
            prompt = self._build_prompt(query, context)
            system = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        except Exception as e:
            logger.error(f"Context/prompt building failed: {e}")
            return {
                'answer': "I'm sorry, I encountered an error while processing your query. Please try again.",
                'sources': [],
                'model': self.model,
                'retrieved_docs': len(retrieved_docs),
                'context_length': 0,
                'error': str(e)
            }
        
        # Step 4: Generate answer using Ollama
        try:
            import time
            start_time = time.time()
            
            logger.info(f"🤖 Sending request to Ollama model: {self.model}")
            logger.info(f"   Context length: {context_length} chars, Prompt length: {len(prompt)} chars")
            logger.info(f"   System prompt length: {len(system)} chars")
            logger.info(f"   Temperature: {temperature}, Streaming: {stream}")
            
            response = self.ollama_client.generate(
                model=self.model,
                prompt=prompt,
                system=system,
                temperature=temperature,
                stream=stream
            )
            
            request_time = time.time() - start_time
            logger.info(f"   Request sent in {request_time:.2f}s")
            
            # Extract sources from retrieved documents
            sources = []
            for doc in retrieved_docs:
                metadata = doc.get('metadata', {})
                source = metadata.get('source', 'Unknown')
                if source not in sources:
                    sources.append(source)
            
            if stream:
                # Return stream for streaming responses with logging
                first_token_time = None
                chunk_count = [0]  # Use list to allow modification in nested function
                
                def logged_stream():
                    nonlocal first_token_time
                    try:
                        for line in response:
                            if first_token_time is None and line:
                                first_token_time = time.time() - start_time
                                logger.info(f"✅ First token received after {first_token_time:.2f}s")
                            chunk_count[0] += 1
                            yield line
                    finally:
                        # Log completion when stream ends
                        total_time = time.time() - start_time
                        logger.info(f"✅ Model generation completed in {total_time:.2f}s")
                        logger.info(f"   Total chunks received: {chunk_count[0]}")
                        if first_token_time:
                            logger.info(f"   Time to first token: {first_token_time:.2f}s")
                            logger.info(f"   Generation time: {total_time - first_token_time:.2f}s")
                
                return {
                    'stream': logged_stream(),  # Return the logged stream iterator
                    'sources': sources,
                    'model': self.model,
                    'retrieved_docs': len(retrieved_docs),
                    'context_length': context_length,
                    'retrieved_documents': retrieved_docs
                }
            else:
                # Handle non-streaming response
                generation_time = time.time() - start_time
                answer = response.get('response', '')
                
                # Extract token counts if available
                prompt_eval_count = response.get('prompt_eval_count')
                eval_count = response.get('eval_count')
                total_duration = response.get('total_duration', 0) / 1e9  # Convert nanoseconds to seconds
                
                logger.info(f"✅ Model generation completed in {generation_time:.2f}s")
                logger.info(f"   Generated answer length: {len(answer)} chars")
                if prompt_eval_count is not None:
                    logger.info(f"   Input tokens: {prompt_eval_count}, Output tokens: {eval_count}")
                if total_duration > 0:
                    logger.info(f"   Model processing time: {total_duration:.2f}s")
                    if eval_count and eval_count > 0:
                        tokens_per_sec = eval_count / (total_duration or generation_time)
                        logger.info(f"   Generation speed: {tokens_per_sec:.1f} tokens/sec")
                
                return {
                    'answer': answer.strip(),
                    'sources': sources,
                    'model': self.model,
                    'retrieved_docs': len(retrieved_docs),
                    'context_length': context_length,
                    'retrieved_documents': retrieved_docs  # Include full docs for debugging
                }
            
        except Exception as e:
            generation_time = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(f"❌ Model generation failed after {generation_time:.2f}s: {e}")
            logger.error(f"   Model: {self.model}, Context length: {context_length}, Prompt length: {len(prompt) if 'prompt' in locals() else 0}")
            return {
                'answer': "I'm sorry, I encountered an error while generating a response. Please try again.",
                'sources': [],
                'model': self.model,
                'retrieved_docs': len(retrieved_docs),
                'context_length': context_length,
                'error': str(e)
            }
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        collection_name: Optional[str] = None,
        top_k: Optional[int] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Chat interface with conversation history
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            collection_name: Collection to search
            top_k: Number of documents to retrieve
            temperature: LLM temperature
            stream: Whether to stream response
            
        Returns:
            Response dictionary with answer and metadata
        """
        # Extract the last user message for retrieval
        user_query = None
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_query = msg.get('content')
                break
        
        if not user_query:
            return {
                'answer': "Please provide a question.",
                'sources': [],
                'model': self.model,
                'retrieved_docs': 0,
                'error': 'No user query found'
            }
        
        # Use RAG for the query, but include conversation history in prompt
        collection = collection_name or self.collection_name
        k = top_k or self.top_k
        
        # Retrieve documents
        try:
            retrieved_docs = self.vector_search.search(
                query=user_query,
                collection_name=collection,
                n_results=k
            )
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            retrieved_docs = []
        
        # Build context
        context = self._build_context(retrieved_docs)
        
        # Build messages with context - use improved prompt structure
        if context:
            # Build a comprehensive prompt with context
            user_query_with_context = f"""You have been provided with relevant documentation from AI Agent Insure's knowledge base.

=== DOCUMENTATION CONTEXT ===
{context}

=== USER QUESTION ===
{user_query}

=== YOUR TASK ===
Provide a detailed, well-structured answer that:
1. Directly addresses the question (or clearly states if you don't have enough information)
2. Uses information ONLY from the documentation above - Never guess or make assumptions
3. Always provides factual information - If you don't know the answer, say so explicitly
4. Do NOT mention document names within the body of your answer - List all source documents at the end in a "Sources:" section
5. Is comprehensive and includes relevant details when available
6. Uses professional insurance terminology
7. If the documentation doesn't fully answer the question, clearly state what information is missing

Answer:"""
            
            # Create enhanced messages with system prompt and context-enhanced user query
            enhanced_messages = [
                {'role': 'system', 'content': self.DEFAULT_SYSTEM_PROMPT},
                {'role': 'user', 'content': user_query_with_context}
            ]
            
            # Add previous conversation history (excluding the last user message which we just replaced)
            for msg in messages[:-1]:  # Exclude the last user message
                if msg.get('role') in ['user', 'assistant']:
                    enhanced_messages.append(msg)
        else:
            # No context available, use standard messages
            enhanced_messages = [
                {'role': 'system', 'content': self.DEFAULT_SYSTEM_PROMPT}
            ] + messages
        
        # Generate using chat interface
        try:
            import time
            start_time = time.time()
            
            total_messages_length = sum(len(msg.get('content', '')) for msg in enhanced_messages)
            logger.info(f"🤖 Sending chat request to Ollama model: {self.model}")
            logger.info(f"   Messages count: {len(enhanced_messages)}, Total content length: {total_messages_length} chars")
            logger.info(f"   Context length: {len(context)} chars")
            logger.info(f"   Temperature: {temperature}, Streaming: {stream}")
            
            response = self.ollama_client.chat(
                model=self.model,
                messages=enhanced_messages,
                temperature=temperature,
                stream=stream
            )
            
            request_time = time.time() - start_time
            logger.info(f"   Request sent in {request_time:.2f}s")
            
            if stream:
                answer_parts = []
                first_token_time = None
                chunk_count = 0
                for line in response:
                    if first_token_time is None and line:
                        first_token_time = time.time() - start_time
                        logger.info(f"✅ First token received after {first_token_time:.2f}s")
                    if line:
                        try:
                            import json
                            chunk = json.loads(line)
                            if 'message' in chunk and 'content' in chunk['message']:
                                answer_parts.append(chunk['message']['content'])
                                chunk_count += 1
                        except:
                            pass
                answer = ''.join(answer_parts)
                
                total_time = time.time() - start_time
                logger.info(f"✅ Model generation completed in {total_time:.2f}s")
                logger.info(f"   Total chunks received: {chunk_count}, Answer length: {len(answer)} chars")
                if first_token_time:
                    logger.info(f"   Time to first token: {first_token_time:.2f}s")
                    logger.info(f"   Generation time: {total_time - first_token_time:.2f}s")
            else:
                generation_time = time.time() - start_time
                answer = response.get('message', {}).get('content', '')
                
                # Extract token counts if available
                prompt_eval_count = response.get('prompt_eval_count')
                eval_count = response.get('eval_count')
                total_duration = response.get('total_duration', 0) / 1e9
                
                logger.info(f"✅ Model generation completed in {generation_time:.2f}s")
                logger.info(f"   Generated answer length: {len(answer)} chars")
                if prompt_eval_count is not None:
                    logger.info(f"   Input tokens: {prompt_eval_count}, Output tokens: {eval_count}")
                if total_duration > 0:
                    logger.info(f"   Model processing time: {total_duration:.2f}s")
                    if eval_count and eval_count > 0:
                        tokens_per_sec = eval_count / (total_duration or generation_time)
                        logger.info(f"   Generation speed: {tokens_per_sec:.1f} tokens/sec")
            
            # Extract sources
            sources = []
            for doc in retrieved_docs:
                metadata = doc.get('metadata', {})
                source = metadata.get('source', 'Unknown')
                if source not in sources:
                    sources.append(source)
            
            return {
                'answer': answer.strip(),
                'sources': sources,
                'model': self.model,
                'retrieved_docs': len(retrieved_docs),
                'context_length': len(context)
            }
            
        except Exception as e:
            generation_time = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(f"❌ Chat generation failed after {generation_time:.2f}s: {e}")
            logger.error(f"   Model: {self.model}, Messages count: {len(enhanced_messages) if 'enhanced_messages' in locals() else 0}")
            return {
                'answer': "I'm sorry, I encountered an error. Please try again.",
                'sources': [],
                'model': self.model,
                'retrieved_docs': len(retrieved_docs),
                'context_length': len(context) if 'context' in locals() else 0,
                'error': str(e)
            }

