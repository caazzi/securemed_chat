"""
Clinical Agent Service (Replacing RAG).

This module replaces the old vector-search retrieval system with pure,
highly-optimized Clinical Prompt Engineering using established medical
frameworks (OPQRST and SAMPLE).
"""
import logging
from typing import AsyncGenerator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser

from securemed_chat.core.llm import get_llm

def get_language_instructions(lang: str) -> dict:
    if lang == 'pt':
        return {
            "initial_q_instruction": "Todas as perguntas devem ser em Português.",
            "follow_up_q_instruction": "Todas as perguntas devem ser em Português.",
            "summary_instruction": "Os *valores* do JSON devem ser em Português. As *chaves* devem permanecer em Inglês.",
            "example_question": 'Por exemplo, "Quando este sintoma começou?".',
            "not_mentioned": "Não mencionado"
        }
    return {
        "initial_q_instruction": "All questions must be in English.",
        "follow_up_q_instruction": "All questions must be in English.",
        "summary_instruction": "The JSON *values* must be in English. The JSON *keys* must remain in English.",
        "example_question": 'For example, "When did this symptom start?".',
        "not_mentioned": "Not mentioned"
    }

# --- Sprint 1: Single Interview Chain ---
_interview_chain: Runnable | None = None

def get_interview_chain() -> Runnable:
    """Single interview chain. Receives full form context, generates up to 5 targeted questions."""
    global _interview_chain
    if _interview_chain is None:
        logging.info("Building interview chain...")
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a clinical intake assistant helping a patient prepare for a medical appointment.\n"
                "You have received the patient's structured medical form. Your task is to generate up to 5\n"
                "open-ended follow-up questions to capture what the form could not: the nuanced, specific\n"
                "details of the patient's current complaint that will help the doctor most.\n\n"
                "STRICT RULES (DO NOT VIOLATE):\n"
                "1. YOU ARE NOT A DOCTOR. Never suggest diagnoses, treatments, medications, or causes for symptoms.\n"
                "2. Do not ask about information already collected in the form (do not re-ask about medications,\n"
                "   known conditions, or allergies already listed).\n"
                "3. Focus questions on the current complaint only: character, onset, radiation, severity,\n"
                "   timing, aggravating/relieving factors, and associated symptoms not yet mentioned.\n"
                "4. If the chief complaint suggests a critical emergency (e.g., severe chest pain, sudden\n"
                "   difficulty breathing, loss of consciousness), output ONLY an emergency warning directing\n"
                "   the patient to seek immediate care — do not generate questions.\n"
                "5. Generate between 3 and 5 questions. Fewer is better if the form already provides rich context.\n"
                "6. Use simple language accessible to lay people. Avoid medical jargon.\n"
                "7. Output only the numbered list of questions. No preamble, no pleasantries.\n"
                "\n{language_instruction}"
            )),
            ("human", (
                "Age bracket: {age_bracket}\n"
                "Biological sex: {sex}\n"
                "Specialist: {specialist}\n"
                "Chief complaint: {chief_complaint}\n"
                "Duration: {duration}\n"
                "Additional detail: {complaint_detail}\n"
                "Pre-existing conditions: {conditions}\n"
                "Current medications: {medications}\n"
                "Drug allergies: {allergies}\n"
                "Family history: {family_history}\n"
                "Smoking: {smoking}\n"
                "Alcohol: {alcohol}"
            )),
        ])
        _interview_chain = prompt | get_llm() | StrOutputParser()
    return _interview_chain

async def stream_interview_questions(
    session_data: dict,
    lang: str,
    chain: Runnable
) -> AsyncGenerator[str, None]:
    """Streams questions from the interview chain."""
    logging.info(f"Streaming interview questions (lang={lang}).")
    lang_instructions = get_language_instructions(lang)

    def join_list(items):
        return ", ".join(items) if items else "None"

    input_dict = {
        "age_bracket": session_data.get("age_bracket", ""),
        "sex": session_data.get("sex", ""),
        "specialist": session_data.get("specialist", ""),
        "chief_complaint": session_data.get("chief_complaint", ""),
        "duration": session_data.get("duration", ""),
        "complaint_detail": session_data.get("complaint_detail", "") or "None",
        "conditions": join_list(session_data.get("conditions", [])),
        "medications": join_list(session_data.get("medications", [])),
        "allergies": session_data.get("allergies", "") or "None",
        "family_history": join_list(session_data.get("family_history", [])),
        "smoking": session_data.get("smoking", ""),
        "alcohol": session_data.get("alcohol", ""),
        "language_instruction": lang_instructions["initial_q_instruction"],
    }
    async for chunk in chain.astream(input_dict):
        yield chunk
