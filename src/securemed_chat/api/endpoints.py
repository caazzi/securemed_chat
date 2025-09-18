"""
API Endpoints (Orchestrator).

This module defines the FastAPI routes that act as the main orchestrator for
the application's workflow. It includes security measures and performance optimizations.
"""
import re
import json
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

# Correct, absolute imports
from securemed_chat.core.llm import llm
from securemed_chat.core.config import SECUREMED_API_KEY
from securemed_chat.services.rag_service import (
    stream_initial_questions,
    stream_follow_up_questions,
    summarize_and_structure_anamnesis  # <-- FIX: Import the new function
)
from securemed_chat.services.pdf_service import generate_pdf_report_in_memory

# --- Security & Helper Functions ---

API_KEY_HEADER = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key_header: str = Security(API_KEY_HEADER)):
    """Dependency to validate the API key from the X-API-KEY header."""
    if api_key_header == SECUREMED_API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")

def sanitize_input(text: str) -> str:
    """Basic input sanitization."""
    if not isinstance(text, str):
        return ""
    return text.strip()

# This function is no longer needed here as the JsonOutputParser handles it in the service
# def extract_json_from_llm(llm_output: str) -> dict: ...


# --- Pydantic Models ---

class InitialRequest(BaseModel):
    chief_complaint: str
    age: int
    gender: str

class FollowUpRequest(BaseModel):
    chief_complaint: str
    age: int
    gender: str
    initial_answers: str

class SummarizationRequest(BaseModel):
    chief_complaint: str
    age: int
    gender: str
    initial_answers: str
    follow_up_answers: str

# --- API Router ---
router = APIRouter(dependencies=[Depends(get_api_key)])


@router.post("/initial-questions-stream")
async def get_initial_questions_streamed(request: InitialRequest):
    """
    PERFORMANCE: Endpoint for the first step that streams RAG-based questions.
    """
    try:
        sanitized_complaint = sanitize_input(request.chief_complaint)
        complaint_context = f"A {request.age}-year-old {request.gender} presenting with: {sanitized_complaint}"

        async def event_generator() -> AsyncGenerator[str, None]:
            async for chunk in stream_initial_questions(complaint_context):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate initial questions: {e}")

@router.post("/follow-up-questions-stream")
async def get_follow_up_questions_streamed(request: FollowUpRequest):
    """
    PERFORMANCE: Endpoint for the second step that streams follow-up questions.
    """
    try:
        sanitized_complaint = sanitize_input(request.chief_complaint)
        sanitized_answers = sanitize_input(request.initial_answers)
        complaint_context = f"A {request.age}-year-old {request.gender} presenting with: {sanitized_complaint}"

        async def event_generator() -> AsyncGenerator[str, None]:
            async for chunk in stream_follow_up_questions(complaint_context, sanitized_answers):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate follow-up questions: {e}")

@router.post("/summarize-and-generate-pdf")
async def summarize_and_generate_pdf_endpoint(request: SummarizationRequest):
    """
    Final endpoint: Summarizes conversation and returns a PDF report directly.
    The PDF is generated in-memory for enhanced privacy and security.
    """
    try:
        # --- FIX: Replace old logic with a call to the new service function ---
        structured_data = await summarize_and_structure_anamnesis(
            chief_complaint=sanitize_input(request.chief_complaint),
            initial_answers=sanitize_input(request.initial_answers),
            follow_up_answers=sanitize_input(request.follow_up_answers)
        )
        # Add the original chief complaint back into the data for the PDF
        structured_data['chief_complaint'] = sanitize_input(request.chief_complaint)

        # PRIVACY/SECURITY: Generate PDF in memory and return bytes directly
        pdf_bytes = generate_pdf_report_in_memory(structured_data)

        headers = {
            'Content-Disposition': 'attachment; filename="Medical_Summary_Report.pdf"'
        }
        return Response(content=pdf_bytes, media_type='application/pdf', headers=headers)

    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
