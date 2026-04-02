import pytest
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient
from securemed_chat.main import app

client = TestClient(app)
HEADERS = {"X-API-KEY": "ci_test_key_123"}

@patch("securemed_chat.api.endpoints.create_session", new_callable=AsyncMock)
def test_init_session(mock_create):
    mock_create.return_value = "fake-session-id"
    payload = {"age": 35, "gender": "Female", "lang": "en"}
    response = client.post("/api/session/init", json=payload, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["session_id"] == "fake-session-id"
    mock_create.assert_called_once()

@patch("securemed_chat.api.endpoints.get_session", new_callable=AsyncMock)
@patch("securemed_chat.api.endpoints.update_session", new_callable=AsyncMock)
@patch("securemed_chat.api.endpoints.stream_initial_questions")
def test_initial_questions_stream(mock_stream, mock_update, mock_get):
    mock_get.return_value = {"age": 35, "gender": "Female", "lang": "en"}
    
    async def fake_stream(*args, **kwargs):
        yield "1. What is the onset?"
    mock_stream.side_effect = fake_stream
    
    payload = {
        "session_id": "fake-session-id",
        "chief_complaint": "Severe headache"
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
        mock_update.assert_called_once()

@patch("securemed_chat.api.endpoints.get_session", new_callable=AsyncMock)
@patch("securemed_chat.api.endpoints.update_session", new_callable=AsyncMock)
@patch("securemed_chat.api.endpoints.stream_follow_up_questions")
def test_follow_up_questions_stream(mock_stream, mock_update, mock_get):
    mock_get.return_value = {
        "age": 35, 
        "gender": "Female", 
        "lang": "en",
        "chief_complaint": "Severe headache"
    }
    
    async def fake_stream(*args, **kwargs):
        yield "1. Any family history?"
    mock_stream.side_effect = fake_stream
    
    payload = {
        "session_id": "fake-session-id",
        "initial_answers": "pain"
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
        mock_update.assert_called_once()

@patch("securemed_chat.api.endpoints.get_session", new_callable=AsyncMock)
@patch("securemed_chat.api.endpoints.summarize_and_structure_anamnesis")
def test_summarize_and_generate_pdf(mock_summary, mock_get):
    mock_get.return_value = {
        "age": 35, 
        "gender": "Female", 
        "lang": "en",
        "chief_complaint": "Headache",
        "initial_answers": "pain"
    }
    
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
        "session_id": "fake-session-id",
        "follow_up_answers": "none"
    }
    response = client.post("/api/summarize-and-generate-pdf", json=payload, headers=HEADERS)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    assert mock_summary.called
