"""
Retrieval-Augmented Generation (RAG) Service.

This service is the "Clinical Brain" of the application. It is responsible for:
1. Loading the pre-built vector store from disk.
2. Creating a retriever to search for relevant clinical context.
3. Constructing and invoking a RAG chain to generate clinically relevant
   questions based on a user's chief complaint.
"""
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS

from src.securemed_chat.core.llm import llm, embeddings
from config import VECTOR_STORE_PATH

# --- Check for Vector Store and Load ---
vector_store_path = Path(VECTOR_STORE_PATH)
if not (vector_store_path / "index.faiss").exists():
    raise FileNotFoundError(
        f"Vector store not found at {VECTOR_STORE_PATH}. "
        "Please run 'python scripts/build_vector_store.py' to create it."
    )

print("💾 Loading the vector store... this may take a moment.")
vector_store = FAISS.load_local(
    folder_path=VECTOR_STORE_PATH,
    embeddings=embeddings,
    allow_dangerous_deserialization=True
)
print("👍 Vector store loaded successfully.")


# --- Initialize Retriever ---
# The retriever fetches the top 4 most relevant document chunks for a query.
retriever = vector_store.as_retriever(search_kwargs={'k': 4})


# --- Define the RAG Prompt Template ---
# This is the master instruction for the LLM on how to generate questions.
RAG_PROMPT_TEMPLATE = """
System: You are a helpful health assistant. Your goal is to help a patient structure their relevant medical history based on their chief complaint.

CONTEXT:
{context}

QUESTION:
Based ONLY on the clinical anamnesis information in the CONTEXT above, generate a numbered list of exactly 5 essential questions to get more information about the patient's medical history for this chief complaint: '{chief_complaint}'.

Frame the questions from the patient's perspective. For example, instead of "Ask about onset," the question should be "When did this symptom start?". Do not add any conversational text before or after the list of questions. The output must be in English.
"""
rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)


# --- Create the RAG Chain ---
# This chain links the retriever, prompt, and LLM together.
rag_chain = (
    {"context": retriever, "chief_complaint": RunnablePassthrough()}
    | rag_prompt
    | llm
    | StrOutputParser()
)

print("✅ RAG chain is ready.")


def generate_anamnesis_questions(chief_complaint: str) -> str:
    """
    Generates a list of anamnesis questions based on a chief complaint.

    Args:
        chief_complaint: The patient's chief complaint (e.g., "Persistent dry cough").

    Returns:
        A string containing a numbered list of questions.
    """
    print(f"🧠 Generating questions for chief complaint: '{chief_complaint}'...")
    return rag_chain.invoke(chief_complaint)
