import pytest
import os
import json
from unittest.mock import patch, MagicMock

os.environ["SECUREMED_API_KEY"] = "test_api_key_123"
os.environ["GOOGLE_CLOUD_PROJECT"] = "test_project"
os.environ["GOOGLE_CLOUD_REGION"] = "us-east1"

from fastapi.testclient import TestClient
from securemed_chat.main import app

client = TestClient(app)
HEADERS = {"X-API-KEY": "test_api_key_123"}

@patch("securemed_chat.api.endpoints.stream_initial_questions")
def test_initial_questions_stream(mock_stream):
    async def fake_stream(*args, **kwargs):
        yield "1. What is the onset?"
        
    mock_stream.side_effect = fake_stream
    
    payload = {
        "chief_complaint": "Severe headache",
        "age": 35,
        "gender": "Female",
        "lang": "en"
    }
    with client.stream("POST", "/api/initial-questions-stream", json=payload, headers=HEADERS) as response:
        assert response.status_code == 200
        full_text = ""
        for line in response.iter_lines():
            if line.startswith("data:"):
                data = json.loads(line[len("data:"):].strip())
                full_text += data
        assert "onset" in full_text
        assert mock_stream.called

@patch("securemed_chat.api.endpoints.stream_follow_up_questions")
def test_follow_up_questions_stream(mock_stream):
    async def fake_stream(*args, **kwargs):
        yield "1. Any family history?"
        
    mock_stream.side_effect = fake_stream
    
    payload = {
        "chief_complaint": "Severe headache",
        "age": 35,
        "gender": "Female",
        "initial_answers": "pain",
        "lang": "en"
    }
    with client.stream("POST", "/api/follow-up-questions-stream", json=payload, headers=HEADERS) as response:
        assert response.status_code == 200
        full_text = ""
        for line in response.iter_lines():
            if line.startswith("data:"):
                data = json.loads(line[len("data:"):].strip())
                full_text += data
        assert "family" in full_text
        assert mock_stream.called

@patch("securemed_chat.api.endpoints.summarize_and_structure_anamnesis")
def test_summarize_and_generate_pdf(mock_summary):
    async def fake_summary(*args, **kwargs):
        return {
            "chief_complaint": "Headache",
            "onset": "2 days ago", 
            "character": "throbbing", 
            "associated_symptoms": "none", 
            "past_medical_history": "none", 
            "family_history": "none", 
            "medications": "ibuprofen"
        }
    mock_summary.side_effect = fake_summary
    
    payload = {
        "chief_complaint": "Headache",
        "age": 35,
        "gender": "Female",
        "initial_answers": "pain",
        "follow_up_answers": "none",
        "lang": "en"
    }
    response = client.post("/api/summarize-and-generate-pdf", json=payload, headers=HEADERS)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    assert mock_summary.called
