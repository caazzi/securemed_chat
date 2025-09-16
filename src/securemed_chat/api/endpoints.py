"""
API Endpoints (Orchestrator).

This module defines the FastAPI routes that act as the main orchestrator for
the application's workflow.
"""
import re
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Correct, absolute imports based on the new project structure
from securemed_chat.core.llm import llm
from securemed_chat.services.rag_service import generate_initial_questions, generate_follow_up_questions
from securemed_chat.services.pdf_service import generate_pdf_report

# --- Pydantic Models for a structured, multi-step conversation ---

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

class QuestionsResponse(BaseModel):
    questions: list[str]

# --- API Router ---
router = APIRouter()

def parse_questions_from_llm(text: str) -> list[str]:
    """Utility to clean the numbered list output from the LLM."""
    questions = re.findall(r"^\s*[-*]?\s*\d*\.?\s*(.*)", text, re.MULTILINE)
    return [q.strip() for q in questions if q.strip()]

@router.post("/initial-questions", response_model=QuestionsResponse)
async def get_initial_questions(request: InitialRequest):
    """
    Endpoint for the first step: Generates RAG-based questions from a chief complaint.
    """
    try:
        complaint_context = f"A {request.age}-year-old {request.gender} presenting with: {request.chief_complaint}"
        generated_text = generate_initial_questions(complaint_context)
        return {"questions": parse_questions_from_llm(generated_text)}
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate initial questions: {e}")

@router.post("/follow-up-questions", response_model=QuestionsResponse)
async def get_follow_up_questions(request: FollowUpRequest):
    """
    Endpoint for the second step: Generates deeper medical history questions.
    """
    try:
        complaint_context = f"A {request.age}-year-old {request.gender} presenting with: {request.chief_complaint}"
        generated_text = generate_follow_up_questions(complaint_context, request.initial_answers)
        return {"questions": parse_questions_from_llm(generated_text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate follow-up questions: {e}")

@router.post("/summarize-and-create-pdf")
async def summarize_and_create_pdf(request: SummarizationRequest):
    """
    Final endpoint: Summarizes the full conversation and generates a PDF report.
    """
    SUMMARIZATION_PROMPT = f"""
    Analyze the following patient's text. The patient is a {request.age}-year-old {request.gender}.
    Extract the key medical information and structure it as a clean JSON object.
    The JSON should have keys: "onset", "character", "associated_symptoms", "past_medical_history", "family_history", and "medications".
    If a key's information is not present, use "N/A" for its value.
    Ensure the output is ONLY the raw JSON object, without any markdown formatting.

    Patient's full text: "Initial Answers: {request.initial_answers}\\n\\nFollow-up History Answers: {request.follow_up_answers}"
    """
    try:
        summary_response = llm.invoke(SUMMARIZATION_PROMPT)
        summary_content = summary_response.content.strip().replace("```json", "").replace("```", "")
        structured_data = json.loads(summary_content)
        structured_data['chief_complaint'] = request.chief_complaint
        pdf_path = generate_pdf_report(structured_data)
        return FileResponse(
            path=pdf_path,
            filename=pdf_path.name,
            media_type='application/pdf'
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse summary from language model.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create PDF report: {e}")
