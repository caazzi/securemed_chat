"""
Clinical Agent Service (Replacing RAG).

This module replaces the old vector-search retrieval system with pure,
highly-optimized Clinical Prompt Engineering using established medical
frameworks (OPQRST and SAMPLE).
"""
import logging
from typing import AsyncGenerator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

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

# --- Lazily Initialized Singletons ---
_initial_agent_chain: Runnable | None = None
_follow_up_agent_chain: Runnable | None = None
_structuring_chain: Runnable | None = None

def get_initial_agent_chain() -> Runnable:
    """Builds the initial OPQRST questions chain."""
    global _initial_agent_chain
    if _initial_agent_chain is None:
        logging.info("Building OPQRST agent chain for initial questions...")
        
        PROMPT_TEMPLATE = """System: You are an expert clinical diagnostician.
Your task is to help structure a patient's medical history using the OPQRST framework (Onset, Provocation/Palliation, Quality, Region/Radiation, Severity, Time).

PATIENT CHIEF COMPLAINT: {chief_complaint}

QUESTION: Based purely on clinical best practices for this chief complaint, generate a numbered list of exactly 5 essential follow-up questions. 
Act as a triage nurse asking the patient directly. {example_question} 
Do not add any conversational text or pleasantries. {language_instruction}"""
        
        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        
        _initial_agent_chain = (
            RunnablePassthrough.assign(
                language_instruction=lambda x: get_language_instructions(x["lang"])["initial_q_instruction"],
                example_question=lambda x: get_language_instructions(x["lang"])["example_question"]
            ) 
            | prompt 
            | get_llm() 
            | StrOutputParser()
        )
    return _initial_agent_chain

def get_follow_up_agent_chain() -> Runnable:
    """Builds the follow-up SAMPLE questions chain."""
    global _follow_up_agent_chain
    if _follow_up_agent_chain is None:
        logging.info("Building SAMPLE agent chain for follow-up questions...")
        
        PROMPT_TEMPLATE = """System: You are an expert clinical diagnostician.
The patient has provided information about their chief complaint. Now, use the SAMPLE framework (Symptoms, Allergies, Medications, Past medical history, Last meal/Events) to gather background medical history.

PATIENT CHIEF COMPLAINT: {chief_complaint}
PATIENT'S ANSWERS ABOUT SYMPTOMS: {initial_answers}

QUESTION: Generate a numbered list of exactly 5 essential follow-up questions focused ONLY on their deep medical history (Past conditions, surgeries, family history, active medications, allergies). 
Act as a triage nurse asking the patient directly. 
Do not add any conversational text or pleasantries. {language_instruction}"""

        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        
        _follow_up_agent_chain = (
            RunnablePassthrough.assign(
                language_instruction=lambda x: get_language_instructions(x["lang"])["follow_up_q_instruction"],
            ) 
            | prompt 
            | get_llm() 
            | StrOutputParser()
        )
    return _follow_up_agent_chain

def get_structuring_chain() -> Runnable:
    """Builds the JSON summarization chain."""
    global _structuring_chain
    if _structuring_chain is None:
        logging.info("Building structuring chain for summarization...")
        SUMMARY_PROMPT_TEMPLATE = """System: You are an expert medical assistant specializing in patient history summarization.
Your task is to synthesize the provided chief complaint and the patient's answers into a structured JSON object. Use clear, simple language. If a piece of information is not provided in the answers, use "{not_mentioned}".

CONVERSATION:
- Chief Complaint: {chief_complaint}
- Answers about Symptoms: {initial_answers}
- Answers about Medical History: {follow_up_answers}

Based on the conversation above, extract the relevant information and format it into a JSON object with EXACTLY the following keys. {language_instruction}
"onset": "When did the main symptom begin?", 
"character": "How would the patient describe the symptom (e.g., sharp, dull, constant)?", 
"associated_symptoms": "What other symptoms are occurring alongside the main one?", 
"past_medical_history": "What relevant past illnesses, conditions, or surgeries were mentioned?", 
"family_history": "What relevant family medical conditions were mentioned?", 
"medications": "What current medications and allergies were mentioned?"

You MUST output ONLY the raw, valid JSON object and nothing else."""
        
        prompt = ChatPromptTemplate.from_template(SUMMARY_PROMPT_TEMPLATE)
        _structuring_chain = prompt | get_llm() | JsonOutputParser()
    return _structuring_chain

# --- Service Functions ---
async def stream_initial_questions(chief_complaint: str, lang: str, agent_chain: Runnable) -> AsyncGenerator[str, None]:
    logging.info(f"Streaming OPQRST questions (lang={lang}).")
    input_dict = {"chief_complaint": chief_complaint, "lang": lang}
    async for chunk in agent_chain.astream(input_dict):
        yield chunk

async def stream_follow_up_questions(chief_complaint: str, initial_answers: str, lang: str, agent_chain: Runnable) -> AsyncGenerator[str, None]:
    logging.info(f"Streaming SAMPLE follow-up questions (lang={lang}).")
    input_dict = {"chief_complaint": chief_complaint, "initial_answers": initial_answers, "lang": lang}
    async for chunk in agent_chain.astream(input_dict):
        yield chunk

async def summarize_and_structure_anamnesis(chief_complaint: str, initial_answers: str, follow_up_answers: str, lang: str, structuring_chain: Runnable) -> dict:
    logging.info(f"Structuring patient answers into summary format (lang={lang}).")
    lang_instructions = get_language_instructions(lang)
    input_dict = {
        "chief_complaint": chief_complaint, 
        "initial_answers": initial_answers, 
        "follow_up_answers": follow_up_answers, 
        "not_mentioned": lang_instructions["not_mentioned"], 
        "language_instruction": lang_instructions["summary_instruction"]
    }
    summary_json = await structuring_chain.ainvoke(input_dict)
    return summary_json
