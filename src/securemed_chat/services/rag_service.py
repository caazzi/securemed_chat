"""
Retrieval-Augmented Generation (RAG) and LLM Service.
"""
import chromadb
from typing import AsyncGenerator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_community.vectorstores import Chroma

# Correct, absolute imports
from securemed_chat.core.llm import llm, embeddings
from securemed_chat.core.config import CHROMA_HOST, CHROMA_PORT, COLLECTION_NAME

vector_store = None
rag_chain = None
deep_dive_rag_chain = None
structuring_chain = None

try:
    print(f"🔗 Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    chroma_client.heartbeat()
    print("👍 ChromaDB connection successful.")

    vector_store = Chroma(
        client=chroma_client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )
    print(f"📚 Successfully connected to collection: '{COLLECTION_NAME}'")

except Exception as e:
    print(f"❌ FAILED TO CONNECT TO CHROMADB: {e}")

if vector_store:
    retriever = vector_store.as_retriever(search_kwargs={'k': 4})

    # --- Chain 1: Initial Questions ---
    RAG_PROMPT_TEMPLATE = """
    System: You are a helpful health assistant. Your goal is to help a patient structure their relevant medical history based on their chief complaint.
    CONTEXT: {context}
    QUESTION: Based ONLY on the clinical anamnesis information in the CONTEXT above, generate a numbered list of exactly 5 essential questions to get more information about the patient's medical history for this chief complaint: '{chief_complaint}'. Frame the questions from the patient's perspective. For example, instead of "Ask about onset," the question should be "When did this symptom start?". Do not add any conversational text before or after the list of questions.
    """
    rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    rag_chain = (
        {"context": retriever, "chief_complaint": RunnablePassthrough()}
        | rag_prompt
        | llm
        | StrOutputParser()
    )
    print("✅ RAG chain for initial questions is ready.")

    # --- Chain 2: Follow-up Questions ---
    DEEP_DIVE_RAG_PROMPT_TEMPLATE = """
    System: You are a medical assistant. Use the provided CONTEXT to ask relevant follow-up questions based on the patient's chief complaint and their initial answers.
    CONTEXT: {context}
    PATIENT PROFILE: {chief_complaint}
    PATIENT'S INITIAL ANSWERS: {initial_answers}
    QUESTION: Based on the CONTEXT and the patient's answers, generate a numbered list of exactly 5 essential follow-up questions to explore their deeper medical history (like past surgeries, chronic conditions, family history, and medications). Frame questions from the patient's perspective. Do not add any conversational text.
    """
    deep_dive_rag_prompt = ChatPromptTemplate.from_template(DEEP_DIVE_RAG_PROMPT_TEMPLATE)
    retrieval_chain = (lambda x: f"{x['chief_complaint']} {x['initial_answers']}") | retriever
    deep_dive_rag_chain = (
        RunnablePassthrough.assign(context=retrieval_chain)
        | deep_dive_rag_prompt
        | llm
        | StrOutputParser()
    )
    print("✅ RAG chain for follow-up questions is ready.")

    # --- Chain 3: Structuring Summary ---
    SUMMARY_PROMPT_TEMPLATE = """
    System: You are an expert medical assistant specializing in patient history summarization.
    Your task is to synthesize the provided chief complaint and the patient's answers into a structured JSON object.
    Use clear, simple language. If a piece of information is not provided in the answers, use "Not mentioned".

    CONVERSATION:
    - Chief Complaint: {chief_complaint}
    - Answers about Symptoms: {initial_answers}
    - Answers about Medical History: {follow_up_answers}

    Based on the conversation above, extract the relevant information and format it into a JSON object with the following keys:
    "onset": When did the main symptom begin?
    "character": How would the patient describe the symptom (e.g., sharp, dull, constant)?
    "associated_symptoms": What other symptoms are occurring alongside the main one?
    "past_medical_history": What relevant past illnesses, conditions, or surgeries were mentioned?
    "family_history": What relevant family medical conditions were mentioned?
    "medications": What current medications and allergies were mentioned?

    You MUST output ONLY the raw, valid JSON object and nothing else.
    """
    summary_prompt = ChatPromptTemplate.from_template(SUMMARY_PROMPT_TEMPLATE)
    structuring_chain = summary_prompt | llm | JsonOutputParser()
    print("✅ Structuring chain for summarization is ready.")


async def stream_initial_questions(chief_complaint: str) -> AsyncGenerator[str, None]:
    """Streams the response for initial questions."""
    if not rag_chain:
        raise ConnectionError("RAG chain is not available due to ChromaDB connection issue.")
    print("🧠 Streaming initial questions for new session.")
    async for chunk in rag_chain.astream(chief_complaint):
        yield chunk

async def stream_follow_up_questions(chief_complaint: str, initial_answers: str) -> AsyncGenerator[str, None]:
    """Streams the response for follow-up questions."""
    if not deep_dive_rag_chain:
        raise ConnectionError("Follow-up RAG chain is not available.")
    print("🧠 Streaming follow-up questions for existing session.")
    input_dict = {"chief_complaint": chief_complaint, "initial_answers": initial_answers}
    async for chunk in deep_dive_rag_chain.astream(input_dict):
        yield chunk

async def summarize_and_structure_anamnesis(chief_complaint: str, initial_answers: str, follow_up_answers: str) -> dict:
    """Uses an LLM to process conversational answers into a structured dictionary."""
    if not structuring_chain:
        raise ConnectionError("Structuring chain is not available.")
    print("🧠 Structuring patient answers into summary format.")
    input_dict = {
        "chief_complaint": chief_complaint,
        "initial_answers": initial_answers,
        "follow_up_answers": follow_up_answers
    }
    summary_json = await structuring_chain.ainvoke(input_dict)
    return summary_json
