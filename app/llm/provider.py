# app/llm/provider.py
import os
from langchain_ollama import ChatOllama

# Model names based on your local Ollama setup
FAST_MODEL_NAME = "llama3.2:1b"
DEFAULT_QUALITY_MODEL_NAME = "qwen3:14b"

def get_fast_llm(temperature: float = 0.0) -> ChatOllama:
    """
    Returns the fast, lightweight model for extraction and routing.
    Llama 3.2 1B is incredibly fast but less capable of deep nuance.
    """
    return ChatOllama(
        model=FAST_MODEL_NAME,
        temperature=temperature,
    )

def get_quality_llm(temperature: float = 0.7) -> ChatOllama:
    """
    Returns the quality model for semantic judgment and rewriting.
    Checks environment variable QUALITY_MODEL, defaulting to qwen3:14b.
    """
    model_name = os.environ.get("QUALITY_MODEL", DEFAULT_QUALITY_MODEL_NAME)
    print(f"Using quality model: {model_name}")
    return ChatOllama(
        model=model_name,
        temperature=temperature
    )