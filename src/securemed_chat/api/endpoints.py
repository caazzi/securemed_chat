"""
API Endpoints (Orchestrator).

This module defines the FastAPI routes. It now leverages dependency injection
to trigger the lazy-loading of services in the rag_service module, ensuring
the application starts quickly.

REVISIONS:
- FIX: Corrected typo from `AProuter` to `APIRouter`.
- Centralized the creation of the `complaint_context` string into a single
  helper function `_create_patient_context` to avoid code duplication.
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
from securemed_chat.services.rag_service import (
    stream_initial_questions,
    stream_follow_up_questions,
    summarize_and_structure_anamnesis,
    get_initial_rag_chain,
    get_follow_up_rag_chain,
    get_structuring_chain
)
from securemed_chat.services.pdf_service import generate_pdf_report_in_memory

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
    # This function centralizes the context creation logic.
    return f"A {age}-year-old {gender} presenting with: {complaint}"

# (Pydantic Models are unchanged)
class InitialRequest(BaseModel):
    chief_complaint: str = Field(..., max_length=5000)
    age: int
    gender: str
    lang: str
class FollowUpRequest(BaseModel):
    chief_complaint: str = Field(..., max_length=5000)
    age: int
    gender: str
    initial_answers: str = Field(..., max_length=5000)
    lang: str
class SummarizationRequest(BaseModel):
    chief_complaint: str = Field(..., max_length=5000)
    age: int
    gender: str
    initial_answers: str = Field(..., max_length=5000)
    follow_up_answers: str = Field(..., max_length=5000)
    lang: str

# --- API Router ---
router = APIRouter(dependencies=[Depends(get_api_key)])

@router.post("/initial-questions-stream")
async def get_initial_questions_streamed(
    request: InitialRequest,
    rag_chain: Runnable = Depends(get_initial_rag_chain)
):
    """ Endpoint for the first step that streams RAG-based questions. """
    try:
        sanitized_complaint = _sanitize_input(request.chief_complaint)
        # Use the centralized helper function
        complaint_context = _create_patient_context(request.age, request.gender, sanitized_complaint)

        async def event_generator():
            async for chunk in stream_initial_questions(complaint_context, request.lang, rag_chain):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except ConnectionError as e:
        logging.error(f"ConnectionError in initial questions: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")
    except Exception as e:
        logging.error(f"Unhandled exception in initial questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate initial questions: {e}")

@router.post("/follow-up-questions-stream")
async def get_follow_up_questions_streamed(
    request: FollowUpRequest,
    deep_dive_rag_chain: Runnable = Depends(get_follow_up_rag_chain)
):
    """ Endpoint for the second step that streams follow-up questions. """
    try:
        sanitized_complaint = _sanitize_input(request.chief_complaint)
        sanitized_answers = _sanitize_input(request.initial_answers)
        # Use the centralized helper function again for consistency
        complaint_context = _create_patient_context(request.age, request.gender, sanitized_complaint)

        async def event_generator():
            async for chunk in stream_follow_up_questions(complaint_context, sanitized_answers, request.lang, deep_dive_rag_chain):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Unhandled exception in follow-up questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate follow-up questions: {e}")

@router.post("/summarize-and-generate-pdf")
async def summarize_and_generate_pdf_endpoint(
    request: SummarizationRequest,
    structuring_chain: Runnable = Depends(get_structuring_chain)
):
    """ Final endpoint: Summarizes conversation and returns a localized PDF report. """
    try:
        sanitized_complaint = _sanitize_input(request.chief_complaint)
        structured_data = await summarize_and_structure_anamnesis(
            chief_complaint=sanitized_complaint,
            initial_answers=_sanitize_input(request.initial_answers),
            follow_up_answers=_sanitize_input(request.follow_up_answers),
            lang=request.lang,
            structuring_chain=structuring_chain
        )
        structured_data['chief_complaint'] = sanitized_complaint
        pdf_bytes, filename = generate_pdf_report_in_memory(structured_data, lang=request.lang)
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        return Response(content=pdf_bytes, media_type='application/pdf', headers=headers)
    except ConnectionError as e:
        logging.error(f"ConnectionError in PDF generation: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")
    except ValueError as e:
        logging.warning(f"ValueError in PDF generation (likely bad input): {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Unhandled exception in PDF generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
