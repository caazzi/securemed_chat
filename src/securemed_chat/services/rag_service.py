"""
Retrieval-Augmented Generation (RAG) and LLM Service (Optimized for Lazy Loading).

This module builds the necessary LangChain components on-demand.

REVISIONS:
- Replaced print() statements with structured `logging`.
- PERFORMANCE: Changed the vector store retriever from default similarity search
  to Maximum Marginal Relevance (MMR) to fetch a more diverse and relevant
  set of documents, improving context quality and potentially reducing latency.
"""
import logging
import chromadb
from typing import AsyncGenerator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_community.vectorstores import Chroma

from securemed_chat.core.llm import get_llm, get_embeddings
from securemed_chat.core.config import CHROMA_HOST, CHROMA_PORT, COLLECTION_NAME

# (get_language_instructions function remains the same)
def get_language_instructions(lang: str) -> dict:
    if lang == 'pt':
        return { "initial_q_instruction": "Todas as perguntas devem ser em Português.", "follow_up_q_instruction": "Todas as perguntas devem ser em Português.", "summary_instruction": "Os *valores* do JSON devem ser em Português, com base na conversa. As *chaves* do JSON devem permanecer em Inglês, como especificado abaixo.", "example_question": 'Por exemplo, em vez de "Ask about onset," a pergunta deve ser "Quando este sintoma começou?".', "not_mentioned": "Não mencionado" }
    return { "initial_q_instruction": "All questions must be in English.", "follow_up_q_instruction": "All questions must be in English.", "summary_instruction": "The JSON *values* must be in English, based on the conversation. The JSON *keys* must remain in English as specified below.", "example_question": 'For example, instead of "Ask about onset," the question should be "When did this symptom start?".', "not_mentioned": "Not mentioned" }

# --- Lazily Initialized Singletons ---
_vector_store: Chroma | None = None
_rag_chain: Runnable | None = None
_deep_dive_rag_chain: Runnable | None = None
_structuring_chain: Runnable | None = None

def get_vector_store() -> Chroma:
    """Connects to ChromaDB and returns the vector store instance, but only once."""
    global _vector_store
    if _vector_store is None:
        try:
            logging.info(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT} for the first time...")
            chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            chroma_client.heartbeat()
            _vector_store = Chroma( client=chroma_client, collection_name=COLLECTION_NAME, embedding_function=get_embeddings() )
            logging.info(f"ChromaDB connection successful to collection: '{COLLECTION_NAME}'")
        except Exception as e:
            logging.error(f"FAILED TO CONNECT TO CHROMADB: {e}", exc_info=True)
            raise ConnectionError("Could not connect to ChromaDB.") from e
    return _vector_store

def get_initial_rag_chain() -> Runnable:
    """Builds and returns the initial questions RAG chain, but only once."""
    global _rag_chain
    if _rag_chain is None:
        logging.info("Building RAG chain for initial questions for the first time...")
        vector_store = get_vector_store()
        # --- PERFORMANCE OPTIMIZATION: Use MMR Retriever ---
        # Fetch 20 documents, then select the 5 most diverse ones.
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 5, 'fetch_k': 20}
        )
        RAG_PROMPT_TEMPLATE = """System: You are a helpful health assistant. Your goal is to help a patient structure their relevant medical history based on their chief complaint.
CONTEXT: {context}
QUESTION: Based ONLY on the clinical anamnesis information in the CONTEXT above, generate a numbered list of exactly 5 essential questions to get more information about the patient's medical history for this chief complaint: '{chief_complaint}'. Frame the questions from the patient's perspective. {example_question} Do not add any conversational text before or after the list of questions. {language_instruction}"""
        rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        initial_retrieval_chain = (lambda x: x["chief_complaint"]) | retriever
        _rag_chain = ( RunnablePassthrough.assign(context=initial_retrieval_chain) | {"context": lambda x: x["context"], "chief_complaint": lambda x: x["chief_complaint"], "example_question": lambda x: get_language_instructions(x["lang"])["example_question"], "language_instruction": lambda x: get_language_instructions(x["lang"])["initial_q_instruction"]} | rag_prompt | get_llm() | StrOutputParser() )
        logging.info("RAG chain for initial questions is ready.")
    return _rag_chain

def get_follow_up_rag_chain() -> Runnable:
    """Builds and returns the follow-up questions RAG chain, but only once."""
    global _deep_dive_rag_chain
    if _deep_dive_rag_chain is None:
        logging.info("Building RAG chain for follow-up questions for the first time...")
        vector_store = get_vector_store()
        # --- PERFORMANCE OPTIMIZATION: Use MMR Retriever ---
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 5, 'fetch_k': 20}
        )
        DEEP_DIVE_RAG_PROMPT_TEMPLATE = """System: You are a medical assistant. Use the provided CONTEXT to ask relevant follow-up questions based on the patient's chief complaint and their initial answers.
CONTEXT: {context}
PATIENT PROFILE: {chief_complaint}
PATIENT'S INITIAL ANSWERS: {initial_answers}
QUESTION: Based on the CONTEXT and the patient's answers, generate a numbered list of exactly 5 essential follow-up questions to explore their deeper medical history (like past surgeries, chronic conditions, family history, and medications). Frame questions from the patient's perspective. Do not add any conversational text. {language_instruction}"""
        deep_dive_rag_prompt = ChatPromptTemplate.from_template(DEEP_DIVE_RAG_PROMPT_TEMPLATE)
        follow_up_retrieval_chain = (lambda x: f"{x['chief_complaint']} {x['initial_answers']}") | retriever
        _deep_dive_rag_chain = ( RunnablePassthrough.assign(context=follow_up_retrieval_chain) | {"context": lambda x: x["context"], "chief_complaint": lambda x: x["chief_complaint"], "initial_answers": lambda x: x["initial_answers"], "language_instruction": lambda x: get_language_instructions(x["lang"])["follow_up_q_instruction"]} | deep_dive_rag_prompt | get_llm() | StrOutputParser() )
        logging.info("RAG chain for follow-up questions is ready.")
    return _deep_dive_rag_chain

def get_structuring_chain() -> Runnable:
    """Builds and returns the summarization chain, but only once."""
    global _structuring_chain
    if _structuring_chain is None:
        logging.info("Building structuring chain for summarization for the first time...")
        SUMMARY_PROMPT_TEMPLATE = """System: You are an expert medical assistant specializing in patient history summarization.
Your task is to synthesize the provided chief complaint and the patient's answers into a structured JSON object. Use clear, simple language. If a piece of information is not provided in the answers, use "{not_mentioned}".
CONVERSATION:
- Chief Complaint: {chief_complaint}
- Answers about Symptoms: {initial_answers}
- Answers about Medical History: {follow_up_answers}
Based on the conversation above, extract the relevant information and format it into a JSON object with the following keys. {language_instruction}
"onset": "When did the main symptom begin?", "character": "How would the patient describe the symptom (e.g., sharp, dull, constant)?", "associated_symptoms": "What other symptoms are occurring alongside the main one?", "past_medical_history": "What relevant past illnesses, conditions, or surgeries were mentioned?", "family_history": "What relevant family medical conditions were mentioned?", "medications": "What current medications and allergies were mentioned?"
You MUST output ONLY the raw, valid JSON object and nothing else."""
        summary_prompt = ChatPromptTemplate.from_template(SUMMARY_PROMPT_TEMPLATE)
        _structuring_chain = summary_prompt | get_llm() | JsonOutputParser()
        logging.info("Structuring chain for summarization is ready.")
    return _structuring_chain

# --- Service Functions now accept the chain as a regular argument ---
async def stream_initial_questions(chief_complaint: str, lang: str, rag_chain: Runnable) -> AsyncGenerator[str, None]:
    # PRIVACY: Note we are not logging the chief_complaint content itself.
    logging.info(f"Streaming initial questions for new session (lang={lang}).")
    input_dict = {"chief_complaint": chief_complaint, "lang": lang}
    async for chunk in rag_chain.astream(input_dict):
        yield chunk

async def stream_follow_up_questions(chief_complaint: str, initial_answers: str, lang: str, deep_dive_rag_chain: Runnable) -> AsyncGenerator[str, None]:
    # PRIVACY: Note we are not logging the content of the answers.
    logging.info(f"Streaming follow-up questions for existing session (lang={lang}).")
    input_dict = {"chief_complaint": chief_complaint, "initial_answers": initial_answers, "lang": lang}
    async for chunk in deep_dive_rag_chain.astream(input_dict):
        yield chunk

async def summarize_and_structure_anamnesis(chief_complaint: str, initial_answers: str, follow_up_answers: str, lang: str, structuring_chain: Runnable) -> dict:
    # PRIVACY: Note we are not logging any patient-provided data.
    logging.info(f"Structuring patient answers into summary format (lang={lang}).")
    lang_instructions = get_language_instructions(lang)
    input_dict = {"chief_complaint": chief_complaint, "initial_answers": initial_answers, "follow_up_answers": follow_up_answers, "not_mentioned": lang_instructions["not_mentioned"], "language_instruction": lang_instructions["summary_instruction"]}
    summary_json = await structuring_chain.ainvoke(input_dict)
    return summary_json
