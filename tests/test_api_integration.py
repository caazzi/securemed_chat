import pytest
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient
from securemed_chat.main import app

client = TestClient(app)
HEADERS = {"X-API-KEY": "ci_test_key_123"}

FULL_SESSION_PAYLOAD = {
    "age_bracket": "26-35",
    "sex": "Female",
    "lang": "en",
    "specialist": "Gastroenterologist",
    "chief_complaint": "Stomach pain and heartburn",
    "duration": "Weeks",
    "complaint_detail": "Gets worse at night",
    "conditions": [],
    "medications": [],
    "allergies": "",
    "family_history": [],
    "smoking": "Never smoked",
    "alcohol": "Rarely",
}

FULL_SESSION_DATA = {**FULL_SESSION_PAYLOAD}

@patch("securemed_chat.api.endpoints.create_session", new_callable=AsyncMock)
def test_init_session(mock_create):
    mock_create.return_value = "fake-session-id"
    response = client.post("/api/session/init", json=FULL_SESSION_PAYLOAD, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["session_id"] == "fake-session-id"
    mock_create.assert_called_once()



# --- Sprint 1 new tests ---

@patch("securemed_chat.api.endpoints.create_session", new_callable=AsyncMock)
def test_init_session_with_full_form(mock_create):
    mock_create.return_value = "fake-session-id"
    response = client.post("/api/session/init", json=FULL_SESSION_PAYLOAD, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["session_id"] == "fake-session-id"
    mock_create.assert_called_once()
    stored = mock_create.call_args[0][0]
    assert stored["age_bracket"] == "26-35"
    assert stored["sex"] == "Female"
    assert stored["specialist"] == "Gastroenterologist"
    assert stored["chief_complaint"] == "Stomach pain and heartburn"
    assert stored["duration"] == "Weeks"
    assert stored["smoking"] == "Never smoked"
    assert stored["alcohol"] == "Rarely"

@patch("securemed_chat.api.endpoints.get_session", new_callable=AsyncMock)
@patch("securemed_chat.api.endpoints.stream_interview_questions")
def test_interview_questions_stream(mock_stream, mock_get):
    mock_get.return_value = FULL_SESSION_DATA

    async def fake_stream(*args, **kwargs):
        yield "1. Question?"

    mock_stream.side_effect = fake_stream

    with client.stream("POST", "/api/interview-questions-stream", json={"session_id": "fake-id"}, headers=HEADERS) as response:
        assert response.status_code == 200
        full_text = ""
        for line in response.iter_lines():
            if line.startswith("data:"):
                full_text += json.loads(line[len("data:"):].strip())
        assert "Question" in full_text
        assert mock_stream.called

@patch("securemed_chat.api.endpoints.get_session", new_callable=AsyncMock)
def test_interview_stream_session_not_found(mock_get):
    mock_get.return_value = {}
    response = client.post("/api/interview-questions-stream", json={"session_id": "bad-id"}, headers=HEADERS)
    assert response.status_code == 404

@patch("securemed_chat.api.endpoints.generate_pdf_report_in_memory")
@patch("securemed_chat.api.endpoints.get_session", new_callable=AsyncMock)
def test_generate_pdf_with_qa_pairs(mock_get, mock_pdf):
    mock_get.return_value = FULL_SESSION_DATA
    mock_pdf.return_value = (b"%PDF-fake-pdf-content", "Medical_Summary_Report.pdf")

    payload = {
        "session_id": "fake-id",
        "qa_pairs": [{"question": "Where is the pain?", "answer": "Upper abdomen"}],
    }
    response = client.post("/api/generate-pdf", json=payload, headers=HEADERS)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")

@patch("securemed_chat.api.endpoints.get_session", new_callable=AsyncMock)
def test_generate_pdf_session_not_found(mock_get):
    mock_get.return_value = {}
    payload = {
        "session_id": "bad-id",
        "qa_pairs": [{"question": "Any pain?", "answer": "Yes"}],
    }
    response = client.post("/api/generate-pdf", json=payload, headers=HEADERS)
    assert response.status_code == 404

@patch("securemed_chat.api.endpoints.generate_pdf_report_in_memory")
@patch("securemed_chat.api.endpoints.stream_interview_questions")
@patch("securemed_chat.api.endpoints.get_session", new_callable=AsyncMock)
@patch("securemed_chat.api.endpoints.create_session", new_callable=AsyncMock)
def test_full_session_happy_path(mock_create, mock_get, mock_stream, mock_pdf):
    # 1. POST /session/init with full form
    mock_create.return_value = "happy-session-id"
    response1 = client.post("/api/session/init", json=FULL_SESSION_PAYLOAD, headers=HEADERS)
    assert response1.status_code == 200
    assert response1.json()["session_id"] == "happy-session-id"

    # 2. POST /interview-questions-stream 
    mock_get.return_value = FULL_SESSION_DATA
    async def fake_stream(*args, **kwargs):
        yield "1. Happy Question?"
    mock_stream.side_effect = fake_stream
    
    with client.stream("POST", "/api/interview-questions-stream", json={"session_id": "happy-session-id"}, headers=HEADERS) as response2:
        assert response2.status_code == 200
        full_text = ""
        for line in response2.iter_lines():
            if line.startswith("data:"):
                full_text += json.loads(line[len("data:"):].strip())
        assert "Happy Question" in full_text
    
    # 3. POST /generate-pdf
    mock_pdf.return_value = (b"%PDF-happy-pdf", "Report.pdf")
    payload = {
        "session_id": "happy-session-id",
        "qa_pairs": [{"question": "Happy?", "answer": "Yes"}],
    }
    response3 = client.post("/api/generate-pdf", json=payload, headers=HEADERS)
    assert response3.status_code == 200
    assert response3.headers["content-type"] == "application/pdf"
    assert response3.content.startswith(b"%PDF-")
