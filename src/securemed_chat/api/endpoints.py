"""
API Endpoints (Orchestrator).

This module defines the FastAPI routes that act as the main orchestrator for
the application's workflow. It handles incoming HTTP requests from the user
interface, calls the appropriate services (RAG, LLM summarization, PDF),
and returns the final response.
"""
import re
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import core services and models
from src.securemed_chat.services.rag_service import generate_anamnesis_questions
from src.securemed_chat.services.pdf_service import generate_pdf_report
from src.securemed_chat.core.llm import llm

# --- Pydantic Models for Request/Response Schemas ---
class ComplaintRequest(BaseModel):
    chief_complaint: str

class AnswersRequest(BaseModel):
    chief_complaint: str
    patient_answers: str

class QuestionsResponse(BaseModel):
    questions: list[str]

# --- API Router ---
router = APIRouter()

# --- Summarization Prompt ---
SUMMARIZATION_PROMPT_TEMPLATE = """
Analyze the following patient's text based on their chief complaint.
Extract the key medical information and structure it as a JSON object.
The JSON should have keys like "onset", "character", "associated_symptoms", and "relevant_history".
Ensure the output is only the raw JSON object, without any markdown formatting like ```json.

Chief Complaint: "{chief_complaint}"
Patient's answers: "{patient_answers}"
"""

@router.post("/generate-questions", response_model=QuestionsResponse)
async def get_questions(request: ComplaintRequest):
    """
    Endpoint to generate anamnesis questions based on a chief complaint.
    """
    if not request.chief_complaint:
        raise HTTPException(status_code=400, detail="Chief complaint cannot be empty.")

    try:
        generated_text = generate_anamnesis_questions(request.chief_complaint)
        # Use regex to parse the numbered list cleanly, handling potential variations
        questions = re.findall(r"^\s*[-*]?\s*\d*\.?\s*(.*)", generated_text, re.MULTILINE)
        cleaned_questions = [q.strip() for q in questions if q.strip()]

        return {"questions": cleaned_questions}
    except Exception as e:
        print(f"Error during question generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate questions.")


@router.post("/summarize-and-create-pdf")
async def summarize_and_create_pdf(request: AnswersRequest):
    """
    Endpoint to summarize patient answers and generate a downloadable PDF report.
    """
    if not request.patient_answers:
        raise HTTPException(status_code=400, detail="Patient answers cannot be empty.")

    try:
        # 1. Summarize answers using the LLM
        print("✍️ Summarizing answers into a structured format...")
        prompt = SUMMARIZATION_PROMPT_TEMPLATE.format(
            chief_complaint=request.chief_complaint,
            patient_answers=request.patient_answers
        )
        summary_response = llm.invoke(prompt)
        summary_content = summary_response.content.strip()

        # 2. Parse the JSON output from the LLM
        try:
            # Clean potential markdown formatting
            json_str_cleaned = summary_content.replace("```json", "").replace("```", "").strip()
            structured_data = json.loads(json_str_cleaned)
        except json.JSONDecodeError:
            print(f"❌ Error: Could not parse JSON from LLM output: {summary_content}")
            raise HTTPException(status_code=500, detail="Failed to parse summary from language model.")

        # Ensure the original chief complaint is included
        structured_data['chief_complaint'] = request.chief_complaint

        # 3. Generate the PDF report
        pdf_path = generate_pdf_report(structured_data)

        # 4. Return the PDF file as a response for download
        return FileResponse(
            path=pdf_path,
            filename=pdf_path.name,
            media_type='application/pdf'
        )
    except Exception as e:
        print(f"Error during summarization or PDF generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create PDF report.")
