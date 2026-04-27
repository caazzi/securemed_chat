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
    stream_interview_questions,
    get_interview_chain,
)
from securemed_chat.services.pdf_service import generate_pdf_report_in_memory
from securemed_chat.services.session_service import (
    create_session,
    get_session,
    update_session,
    check_rate_limit,
    check_session_quota,
    increment_session_quota
)
from fastapi import Request

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

# --- Data Models (Ephemeral State Design) ---
class SessionInitRequest(BaseModel):
    # Step 1 — Demographics
    age_bracket: str
    sex: str
    lang: str
    # Step 2 — Chief Complaint
    specialist: str
    chief_complaint: str
    duration: str
    complaint_detail: str = ""
    # Step 3 — Medical History
    conditions: list[str] = []
    medications: list[str] = []
    allergies: str = ""
    # Step 4 — Lifestyle & Family
    family_history: list[str] = []
    smoking: str
    alcohol: str

class InitialRequest(BaseModel):
    session_id: str
    chief_complaint: str = Field(..., max_length=5000)

class InterviewRequest(BaseModel):
    session_id: str

class QAPair(BaseModel):
    question: str
    answer: str = Field(..., max_length=2000)

class GeneratePdfRequest(BaseModel):
    session_id: str
    qa_pairs: list[QAPair] = Field(..., min_length=1, max_length=5)

# --- API Router ---
router = APIRouter(dependencies=[Depends(get_api_key)])

@router.post("/session/init")
async def init_session(request: SessionInitRequest, fastapi_req: Request):
    """Initializes a new ephemeral Redis session with full form data."""
    ip = fastapi_req.client.host
    
    # 1. Check daily quota (max 5 sessions per IP)
    if not await check_session_quota(ip, limit=5):
        raise HTTPException(status_code=429, detail="Daily session limit reached for this IP.")
        
    # 2. Check rate limit for session creation (max 2 per minute)
    if not await check_rate_limit(f"init:{ip}", limit=2, window=60):
        raise HTTPException(status_code=429, detail="Too many session requests. Please wait.")

    session_id = await create_session({
        "age_bracket": request.age_bracket,
        "sex": request.sex,
        "lang": request.lang,
        "specialist": request.specialist,
        "chief_complaint": request.chief_complaint,
        "duration": request.duration,
        "complaint_detail": request.complaint_detail,
        "conditions": request.conditions,
        "medications": request.medications,
        "allergies": request.allergies,
        "family_history": request.family_history,
        "smoking": request.smoking,
        "alcohol": request.alcohol,
    })
    
    # Increment quota after successful creation
    await increment_session_quota(ip)
    
    return {"session_id": session_id}

@router.post("/initial-questions-stream")
async def get_initial_questions_streamed(
    request: InitialRequest,
    fastapi_req: Request,
    chain: Runnable = Depends(get_interview_chain)
):
    """ Streams interview questions based on chief complaint. """
    ip = fastapi_req.client.host
    # Max 5 calls per minute for streaming
    if not await check_rate_limit(f"stream:{ip}", limit=5, window=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a moment.")

    session_data = await get_session(request.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session expired or invalid")
        
    try:
        sanitized_complaint = _sanitize_input(request.chief_complaint)
        await update_session(request.session_id, {"chief_complaint": sanitized_complaint})
        session_data["chief_complaint"] = sanitized_complaint
        
        async def event_generator():
            async for chunk in stream_interview_questions(session_data, session_data.get("lang", "en"), chain):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Unhandled exception in initial questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate questions. Please try again.")

@router.post("/interview-questions-stream")
async def get_interview_questions_streamed(
    request: InterviewRequest,
    fastapi_req: Request,
    chain: Runnable = Depends(get_interview_chain)
):
    """Streams targeted interview questions based on full form context. Single LLM call."""
    ip = fastapi_req.client.host
    # Max 5 calls per minute for streaming
    if not await check_rate_limit(f"stream:{ip}", limit=5, window=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a moment.")

    session_data = await get_session(request.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session expired or invalid")

    try:
        lang = session_data.get("lang", "en")

        async def event_generator():
            async for chunk in stream_interview_questions(session_data, lang, chain):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Unhandled exception in interview questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate questions. Please try again.")

@router.post("/generate-pdf")
async def generate_pdf_endpoint(request: GeneratePdfRequest):
    """Generates PDF deterministically from session form data + Q&A pairs. No LLM call."""
    session_data = await get_session(request.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session expired or invalid")

    try:
        qa_pairs = [{"question": pair.question, "answer": pair.answer} for pair in request.qa_pairs]
        pdf_bytes, filename = generate_pdf_report_in_memory(
            form=session_data,
            qa_pairs=qa_pairs,
            lang=session_data.get("lang", "en")
        )
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        return Response(content=pdf_bytes, media_type='application/pdf', headers=headers)
    except Exception as e:
        logging.error(f"Unhandled exception in PDF generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again.")
