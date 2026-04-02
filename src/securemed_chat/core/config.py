"""
Centralized configuration management for the SecureMed Chat application.
"""
import os
import logging
from pathlib import Path

# --- Core Google Cloud & Vertex AI Settings ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "securemed-chat")
REGION = os.environ.get("GOOGLE_CLOUD_REGION", "us-east1")

# --- Security Settings ---
# SECURITY: The application MUST fail on startup if the API key is not set.
# For local development, set the key in a .env file.
SECUREMED_API_KEY = os.environ.get("SECUREMED_API_KEY")
if not SECUREMED_API_KEY:
    raise ValueError("FATAL: SECUREMED_API_KEY environment variable not set. Aborting startup.")


# --- Model Configuration ---
EMBEDDING_MODEL = "gemini-embedding-001" # Updated to the latest embedding model
LLM_MODEL = "gemini-2.5-flash-lite"    # Updated to a powerful and cost-effective model

# --- RAG & Vector Store Configuration ---
CHUNK_SIZE = 750
CHUNK_OVERLAP = 100
BATCH_SIZE = 100



# --- File & Directory Paths ---
# PRIVACY: The PDF_REPORTS_DIR is no longer needed as PDFs are generated in-memory.
# PDF_REPORTS_DIR = Path.cwd() / "generated_reports"
# PDF_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

logging.info("Configuration loaded successfully.")
logging.info(f"  Project ID: {PROJECT_ID}")
logging.info(f"  Region: {REGION}")
