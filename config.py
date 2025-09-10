"""
Centralized configuration management for the SecureMed Chat application.

This module reads settings from environment variables and provides a single
source of truth for configurations like project IDs, model names, and file paths.
This approach avoids hardcoding sensitive information and makes the application
more portable across different environments (development, staging, production).
"""

import os
from pathlib import Path

# --- Core Google Cloud & Vertex AI Settings ---
# It's recommended to set GOOGLE_CLOUD_PROJECT in your environment.
# The application will fall back to the value specified here if it's not set.
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "securemed-chat")
REGION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

# --- Model Configuration ---
# Specifies the models to be used for embedding and language generation.
EMBEDDING_MODEL = "gemini-embedding-001"
LLM_MODEL = "gemini-2.5-flash-lite"

# --- RAG & Vector Store Configuration ---
# Text splitting parameters for document processing.
CHUNK_SIZE = 750
CHUNK_OVERLAP = 100

# Batch size for processing documents during vector store creation.
BATCH_SIZE = 100

# --- File & Directory Paths ---
# Establishes the directory structure for the application's data.
# The base directory is the parent of the directory where this file resides.
BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"
PDF_REPORTS_DIR = BASE_DIR / "generated_reports"

# Ensure necessary directories exist upon application startup.
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
PDF_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# --- Vector Store Settings ---
# Path to the FAISS index file within the vector store directory.
VECTOR_STORE_PATH = str(VECTOR_STORE_DIR)

print("✅ Configuration loaded successfully.")
print(f"   - Project ID: {PROJECT_ID}")
print(f"   - Knowledge Base: {KNOWLEDGE_BASE_DIR}")
print(f"   - Vector Store: {VECTOR_STORE_DIR}")
