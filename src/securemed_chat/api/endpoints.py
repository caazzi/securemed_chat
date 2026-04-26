"""
API Endpoints (Orchestrator).

This module defines the FastAPI routes. It leverages dependency injection
to trigger the lazy-loading of services in the agent_service module, ensuring
the application starts quickly. Includes Redis-backed ephemeral state.
"""
import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from langchain_core.runnables import Runnable

from securemed_chat.core.config import SECUREMED_API_KEY
from securemed_chat.services.agent_service import (
    stream_initial_questions,
    stream_follow_up_questions,
    summarize_and_structure_anamnesis,
    get_initial_agent_chain,
    get_follow_up_agent_chain,
    get_structuring_chain
)
from securemed_chat.services.pdf_service import generate_pdf_report_in_memory
from securemed_chat.services.session_service import create_session, get_session, update_session

# --- Security & Helper Functions ---
API_KEY_HEADER = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key_header: str = Security(API_KEY_HEADER)):
    if api_key_header == SECUREMED_API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")

def _sanitize_input(text: str) -> str:
    """Strips leading/trailing whitespace from input."""
    if not isinstance(text, str):
        return ""
    return text.strip()

def _create_patient_context(age: int, gender: str, complaint: str) -> str:
    """Creates a standardized patient context string."""
    return f"A {age}-year-old {gender} presenting with: {complaint}"

# --- Data Models (Ephemeral State Design) ---
class SessionInitRequest(BaseModel):
    age: int
    gender: str
    lang: str

class InitialRequest(BaseModel):
    session_id: str
    chief_complaint: str = Field(..., max_length=5000)

class FollowUpRequest(BaseModel):
    session_id: str
    initial_answers: str = Field(..., max_length=5000)

class SummarizationRequest(BaseModel):
    session_id: str
    follow_up_answers: str = Field(..., max_length=5000)

# --- API Router ---
router = APIRouter(dependencies=[Depends(get_api_key)])

@router.post("/session/init")
async def init_session(request: SessionInitRequest):
    """Initializes a new ephemeral Redis session with demographic capabilities."""
    session_id = await create_session({
        "age": request.age,
        "gender": request.gender,
        "lang": request.lang
    })
    return {"session_id": session_id}

@router.post("/initial-questions-stream")
async def get_initial_questions_streamed(
    request: InitialRequest,
    agent_chain: Runnable = Depends(get_initial_agent_chain)
):
    """ Streams OPQRST questions based on chief complaint. """
    session_data = await get_session(request.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session expired or invalid")
        
    try:
        sanitized_complaint = _sanitize_input(request.chief_complaint)
        await update_session(request.session_id, {"chief_complaint": sanitized_complaint})
        
        complaint_context = _create_patient_context(session_data["age"], session_data["gender"], sanitized_complaint)

        async def event_generator():
            async for chunk in stream_initial_questions(complaint_context, session_data["lang"], agent_chain):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Unhandled exception in initial questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate questions. Please try again.")

@router.post("/follow-up-questions-stream")
async def get_follow_up_questions_streamed(
    request: FollowUpRequest,
    agent_chain: Runnable = Depends(get_follow_up_agent_chain)
):
    """ Streams SAMPLE follow-up questions. """
    session_data = await get_session(request.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session expired or invalid")
    if "chief_complaint" not in session_data:
        raise HTTPException(status_code=422, detail="Session is missing chief complaint. Complete the previous step first.")

    try:
        sanitized_answers = _sanitize_input(request.initial_answers)
        await update_session(request.session_id, {"initial_answers": sanitized_answers})

        complaint_context = _create_patient_context(session_data["age"], session_data["gender"], session_data["chief_complaint"])

        async def event_generator():
            async for chunk in stream_follow_up_questions(complaint_context, sanitized_answers, session_data["lang"], agent_chain):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Unhandled exception in follow-up questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate questions. Please try again.")

@router.post("/summarize-and-generate-pdf")
async def summarize_and_generate_pdf_endpoint(
    request: SummarizationRequest,
    structuring_chain: Runnable = Depends(get_structuring_chain)
):
    """ Final endpoint: Summarizes conversation and returns a PDF report. """
    session_data = await get_session(request.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session expired or invalid")
    missing = [k for k in ("chief_complaint", "initial_answers") if k not in session_data]
    if missing:
        raise HTTPException(status_code=422, detail=f"Session is missing required fields: {missing}. Complete all prior steps first.")

    try:
        sanitized_follow_up = _sanitize_input(request.follow_up_answers)

        structured_data = await summarize_and_structure_anamnesis(
            chief_complaint=session_data["chief_complaint"],
            initial_answers=session_data["initial_answers"],
            follow_up_answers=sanitized_follow_up,
            lang=session_data["lang"],
            structuring_chain=structuring_chain
        )
        structured_data['chief_complaint'] = session_data["chief_complaint"]
        
        pdf_bytes, filename = generate_pdf_report_in_memory(structured_data, lang=session_data["lang"])
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        return Response(content=pdf_bytes, media_type='application/pdf', headers=headers)
    except Exception as e:
        logging.error(f"Unhandled exception in PDF generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again.")
