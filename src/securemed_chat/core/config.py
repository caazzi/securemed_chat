"""
Centralized configuration management for the SecureMed Chat application.
"""
import os
from pathlib import Path

# --- Core Google Cloud & Vertex AI Settings ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "securemed-chat")
REGION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

# --- Model Configuration ---
EMBEDDING_MODEL = "gemini-embedding-001" # Updated model name
LLM_MODEL = "gemini-2.5-flash-lite" # Updated model name

# --- RAG & Vector Store Configuration ---
CHUNK_SIZE = 750
CHUNK_OVERLAP = 100
BATCH_SIZE = 100

# --- ChromaDB connection settings ---
CHROMA_HOST = os.getenv("CHROMA_HOST", "34.151.247.35")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "securemed_docs")

# --- File & Directory Paths ---
# This path is now relative to the project root, not the file location
PDF_REPORTS_DIR = Path.cwd() / "generated_reports"

# Ensure necessary directories exist upon application startup.
PDF_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

print("✅ Configuration loaded successfully.")
print(f"   - Project ID: {PROJECT_ID}")
print(f"   - ChromaDB Host: {CHROMA_HOST}:{CHROMA_PORT}")
print(f"   - PDF Reports Dir: {PDF_REPORTS_DIR}")
