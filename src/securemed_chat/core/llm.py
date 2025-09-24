"""
Core LLM and Embeddings Module (Optimized for Lazy Loading).

This module provides singleton access to the Vertex AI models, ensuring they are
initialized only once per instance, when first requested. This dramatically
improoves application startup time.

REVISIONS:
- Replaced all print() statements with the standard `logging` module for
  production-grade, structured logging.
"""
import logging
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings
from .config import LLM_MODEL, EMBEDDING_MODEL, REGION, PROJECT_ID

# --- STRUCTURED LOGGING ---
# Configure logger for structured output compatible with cloud environments.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- LAZY LOADING REFACTOR ---
# These are initialized as None and will be loaded by the getter functions on first use.
_llm = None
_embeddings = None

def get_llm() -> ChatVertexAI:
    """
    Initializes and returns the main LLM, loading it only once per instance.
    This is the "singleton" pattern for lazy loading.
    """
    global _llm
    if _llm is None:
        logging.info("Initializing Vertex AI LLM for the first time...")
        _llm = ChatVertexAI(
            model_name=LLM_MODEL,
            temperature=0.2,
            project=PROJECT_ID,
            location=REGION,
            streaming=True
        )
        logging.info("Vertex AI LLM initialized successfully.")
    return _llm

def get_embeddings() -> VertexAIEmbeddings:
    """
    Initializes and returns the embedding model, loading it only once per instance.
    """
    global _embeddings
    if _embeddings is None:
        logging.info("Initializing Vertex AI Embeddings model for the first time...")
        _embeddings = VertexAIEmbeddings(
            model_name=EMBEDDING_MODEL,
            project=PROJECT_ID,
            location=REGION
        )
        logging.info("Vertex AI Embeddings initialized successfully.")
    return _embeddings

logging.info("Core LLM module loaded. Models will be initialized on first use.")
