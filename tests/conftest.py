import os
import pytest

# Global test environment configuration
# Setting these before anything else ensures modules that import core.config don't crash
os.environ["SECUREMED_API_KEY"] = "ci_test_key_123"
os.environ["GOOGLE_CLOUD_PROJECT"] = "ci_test_project"
os.environ["GOOGLE_CLOUD_REGION"] = "us-east1"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
