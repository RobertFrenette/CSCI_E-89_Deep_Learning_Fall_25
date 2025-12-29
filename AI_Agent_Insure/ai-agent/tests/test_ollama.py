"""
Tests for Ollama client
Tests require Ollama to be running
"""
import pytest
import os
from src.ollama_client import OllamaClient


# Get Ollama URL from environment or default to localhost
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


@pytest.fixture
def client():
    """Create Ollama client instance"""
    return OllamaClient(base_url=OLLAMA_URL)


@pytest.fixture
def test_model():
    """Get test model from environment or use default"""
    return os.getenv("OLLAMA_TEST_MODEL", "llama3.1")


@pytest.mark.integration
def test_ollama_health_check(client):
    """Test that Ollama is accessible"""
    assert client.check_health(), "Ollama is not accessible"


@pytest.mark.integration
def test_list_models(client):
    """Test listing available models"""
    models = client.list_models()
    assert isinstance(models, list)
    # At least one model should be available
    assert len(models) > 0, "No models found in Ollama"


@pytest.mark.integration
def test_generate_basic(client, test_model):
    """Test basic text generation"""
    prompt = "Say 'Hello, World!' and nothing else."
    response = client.generate(model=test_model, prompt=prompt)
    
    assert "response" in response
    assert isinstance(response["response"], str)
    assert len(response["response"]) > 0
    assert "model" in response
    assert response["model"] == test_model


@pytest.mark.integration
def test_generate_with_system_prompt(client, test_model):
    """Test generation with system prompt"""
    system = "You are a helpful insurance assistant."
    prompt = "What is insurance?"
    
    response = client.generate(
        model=test_model,
        prompt=prompt,
        system=system
    )
    
    assert "response" in response
    assert isinstance(response["response"], str)
    assert len(response["response"]) > 0


@pytest.mark.integration
def test_chat_interface(client, test_model):
    """Test chat interface with message history"""
    messages = [
        {"role": "user", "content": "Hello! What is insurance?"}
    ]
    
    response = client.chat(model=test_model, messages=messages)
    
    assert "message" in response
    assert "role" in response["message"]
    assert "content" in response["message"]
    assert response["message"]["role"] == "assistant"
    assert len(response["message"]["content"]) > 0


@pytest.mark.integration
def test_chat_conversation(client, test_model):
    """Test multi-turn conversation"""
    messages = [
        {"role": "user", "content": "My name is Alice."},
        {"role": "assistant", "content": "Hello Alice! How can I help you?"},
        {"role": "user", "content": "What did I say my name was?"}
    ]
    
    response = client.chat(model=test_model, messages=messages)
    
    assert "message" in response
    content = response["message"]["content"].lower()
    # Should remember the name from context
    assert "alice" in content


@pytest.mark.integration
def test_generate_with_parameters(client, test_model):
    """Test generation with custom parameters"""
    prompt = "Write a short sentence about insurance."
    
    response = client.generate(
        model=test_model,
        prompt=prompt,
        temperature=0.7,
        top_p=0.9,
        max_tokens=50
    )
    
    assert "response" in response
    assert isinstance(response["response"], str)


@pytest.mark.integration
@pytest.mark.slow
def test_pull_model(client):
    """Test pulling a model (skipped by default, use -m slow to run)"""
    # This test is marked as slow and will be skipped unless explicitly run
    # Uncomment and modify to test model pulling
    # model_name = "llama3.2:3b"
    # result = client.pull_model(model_name)
    # assert "status" in result or "completed_at" in result
    pytest.skip("Model pulling test - run manually with -m slow")

