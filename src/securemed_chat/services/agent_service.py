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

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert clinical triage nurse conducting a structured medical intake.\n"
                "Your task is to generate exactly 5 follow-up questions using the OPQRST framework "
                "(Onset, Provocation/Palliation, Quality, Region/Radiation, Severity, Time).\n"
                "Output only the numbered list of questions. Do not add pleasantries, explanations, or preamble.\n"
                "{language_instruction} {example_question}"
            )),
            ("human", (
                "The patient's chief complaint is delimited below. Generate 5 OPQRST questions for it.\n"
                "<chief_complaint>{chief_complaint}</chief_complaint>"
            )),
        ])

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

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert clinical triage nurse conducting a structured medical intake.\n"
                "Using the SAMPLE framework (Symptoms, Allergies, Medications, Past medical history, Last meal/Events), "
                "generate exactly 5 follow-up questions focused on the patient's deep medical background: "
                "past conditions, surgeries, family history, active medications, and allergies.\n"
                "Output only the numbered list of questions. Do not add pleasantries, explanations, or preamble.\n"
                "{language_instruction}"
            )),
            ("human", (
                "The patient's chief complaint and symptom answers are delimited below.\n"
                "<chief_complaint>{chief_complaint}</chief_complaint>\n"
                "<symptom_answers>{initial_answers}</symptom_answers>\n"
                "Generate 5 SAMPLE questions about their medical history."
            )),
        ])

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

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert medical assistant specializing in patient history summarization.\n"
                "Synthesize the patient's inputs into a structured JSON object using clear, simple language.\n"
                "If a piece of information was not provided, use \"{not_mentioned}\" as the value.\n"
                "{language_instruction}\n"
                "You MUST output ONLY the raw, valid JSON object with EXACTLY these keys: "
                "onset, character, associated_symptoms, past_medical_history, family_history, medications."
            )),
            ("human", (
                "Summarize the following patient conversation into the required JSON format.\n"
                "<chief_complaint>{chief_complaint}</chief_complaint>\n"
                "<symptom_answers>{initial_answers}</symptom_answers>\n"
                "<history_answers>{follow_up_answers}</history_answers>"
            )),
        ])

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
