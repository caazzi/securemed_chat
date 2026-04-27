"""
Centralized configuration management for the SecureMed Chat application.
"""
import os

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "securemed-chat")
REGION = os.environ.get("GOOGLE_CLOUD_REGION", "us-east1")

SECUREMED_API_KEY = os.environ.get("SECUREMED_API_KEY")
if not SECUREMED_API_KEY:
    raise ValueError("FATAL: SECUREMED_API_KEY environment variable not set. Aborting startup.")

LLM_MODEL = "gemini-flash-latest"
