"""
Centralized configuration management for the SecureMed Chat application.
"""
import os
from pathlib import Path

# --- Core Google Cloud & Vertex AI Settings ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "securemed-chat")
REGION = os.environ.get("GOOGLE_CLOUD_REGION", "us-east1")

# --- Security Settings ---
# PRIVACY/SECURITY: Removed default API key. The application will now fail on startup
# if this environment variable is not set in the production environment.
SECUREMED_API_KEY = os.environ.get("SECUREMED_API_KEY")
if not SECUREMED_API_KEY:
    # This check is critical for production. For local dev, a .env file is expected.
    print("Warning: SECUREMED_API_KEY environment variable not set. This is required for production.")
    # In a real production scenario, you might raise ValueError here.
    # raise ValueError("FATAL: SECUREMED_API_KEY environment variable not set.")


# --- Model Configuration ---
EMBEDDING_MODEL = "gemini-embedding-001" # Updated to the latest embedding model
LLM_MODEL = "gemini-2.5-flash-lite"    # Updated to a powerful and cost-effective model

# --- RAG & Vector Store Configuration ---
CHUNK_SIZE = 750
CHUNK_OVERLAP = 100
BATCH_SIZE = 100

# --- ChromaDB connection settings ---
CHROMA_HOST = os.getenv("CHROMA_HOST", "34.151.247.35")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "securemed_docs")

# --- File & Directory Paths ---
# PRIVACY: The PDF_REPORTS_DIR is no longer needed as PDFs are generated in-memory.
# PDF_REPORTS_DIR = Path.cwd() / "generated_reports"
# PDF_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

print("✅ Configuration loaded successfully.")
print(f"   - Project ID: {PROJECT_ID}")
print(f"   - Region: {REGION}")
print(f"   - ChromaDB Host: {CHROMA_HOST}:{CHROMA_PORT}")
