"""
Ollama client wrapper for LLM inference
Provides a simple interface to interact with Ollama API
"""
import requests
from typing import Optional, Dict, List, Any
import os


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama client
        
        Args:
            base_url: Base URL for Ollama API (defaults to http://localhost:11434)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.api_url = f"{self.base_url}/api"
    
    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Ollama
        
        Args:
            model: Model name (e.g., "llama3.1")
            prompt: User prompt
            system: System prompt (optional)
            stream: Whether to stream the response
            **kwargs: Additional parameters (temperature, top_p, etc.)
        
        Returns:
            Response dictionary with 'response' and 'model' keys
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            **kwargs
        }
        
        if system:
            payload["system"] = system
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Ollama generate request: model={model}, prompt_len={len(prompt)}, system_len={len(system) if system else 0}, stream={stream}")
            
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=300  # Increased to 5 minutes for larger contexts
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ollama request timed out after 300 seconds")
            logger.error(f"Model: {model}, Prompt length: {len(prompt)}")
            raise requests.exceptions.Timeout(f"Ollama request timed out. The model may be processing a large context. Try reducing the context size or using a faster model.")
        except requests.exceptions.HTTPError as e:
            # Log more details about the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ollama generate error: {e}")
            logger.error(f"URL: {self.api_url}/generate")
            logger.error(f"Payload: {payload}")
            logger.error(f"Response status: {response.status_code}")
            logger.error(f"Response text: {response.text[:500]}")
            raise
        
        if stream:
            return response.iter_lines()
        else:
            return response.json()
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chat with Ollama using message history
        
        Args:
            model: Model name (e.g., "llama3.1")
            messages: List of message dicts with 'role' and 'content' keys
            stream: Whether to stream the response
            **kwargs: Additional parameters
        
        Returns:
            Response dictionary with 'message' and 'model' keys
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            total_content_length = sum(len(msg.get('content', '')) for msg in messages)
            logger.debug(f"Ollama chat request: model={model}, messages={len(messages)}, content_len={total_content_length}, stream={stream}")
            
            response = requests.post(
                f"{self.api_url}/chat",
                json=payload,
                timeout=300  # Increased to 5 minutes for larger contexts
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ollama chat request timed out after 300 seconds")
            logger.error(f"Model: {model}, Messages count: {len(messages)}")
            raise requests.exceptions.Timeout(f"Ollama request timed out. The model may be processing a large context. Try reducing the context size or using a faster model.")
        
        if stream:
            return response.iter_lines()
        else:
            return response.json()
    
    def list_models(self) -> List[str]:
        """
        List available models in Ollama
        
        Returns:
            List of model names
        """
        response = requests.get(f"{self.api_url}/tags", timeout=10)
        response.raise_for_status()
        data = response.json()
        return [model["name"] for model in data.get("models", [])]
    
    def pull_model(self, model: str) -> Dict[str, Any]:
        """
        Pull/download a model from Ollama
        
        Args:
            model: Model name to pull
        
        Returns:
            Response dictionary
        """
        response = requests.post(
            f"{self.api_url}/pull",
            json={"name": model},
            timeout=600  # Model downloads can take time
        )
        response.raise_for_status()
        return response.json()
    
    def check_health(self) -> bool:
        """
        Check if Ollama is running and accessible
        
        Returns:
            True if Ollama is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

