"""
Retrieval-Augmented Generation (RAG) and LLM Service.
"""
import chromadb
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma

# Correct, absolute imports
from securemed_chat.core.llm import llm, embeddings
from securemed_chat.core.config import CHROMA_HOST, CHROMA_PORT, COLLECTION_NAME

vector_store = None
rag_chain = None
deep_dive_rag_chain = None

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

    DEEP_DIVE_RAG_PROMPT_TEMPLATE = """
    System: You are a medical assistant. Use the provided CONTEXT to ask relevant follow-up questions based on the patient's chief complaint and their initial answers.
    CONTEXT: {context}
    PATIENT PROFILE: {chief_complaint}
    PATIENT'S INITIAL ANSWERS: {initial_answers}
    QUESTION: Based on the CONTEXT and the patient's answers, generate a numbered list of exactly 5 essential follow-up questions to explore their deeper medical history (like past surgeries, chronic conditions, family history, and medications). Frame questions from the patient's perspective. Do not add any conversational text.
    """
    deep_dive_rag_prompt = ChatPromptTemplate.from_template(DEEP_DIVE_RAG_PROMPT_TEMPLATE)

    # --- START: CORRECTED CODE ---
    # Define the retrieval part of the chain separately for clarity.
    # This creates a valid runnable that formats a query string from the input
    # and then passes it to the retriever.
    retrieval_chain = (
        (lambda x: f"{x['chief_complaint']} {x['initial_answers']}")
        | retriever
    )

    # Correctly construct the main chain using the retrieval_chain.
    deep_dive_rag_chain = (
        RunnablePassthrough.assign(
            context=retrieval_chain
        )
        | deep_dive_rag_prompt
        | llm
        | StrOutputParser()
    )
    # --- END: CORRECTED CODE ---

    print("✅ RAG chain for follow-up questions is ready.")

def generate_initial_questions(chief_complaint: str) -> str:
    if not rag_chain:
        raise ConnectionError("RAG chain is not available due to ChromaDB connection issue.")
    print(f"🧠 Generating initial questions for: '{chief_complaint}'...")
    return rag_chain.invoke(chief_complaint)

def generate_follow_up_questions(chief_complaint: str, initial_answers: str) -> str:
    if not deep_dive_rag_chain:
        raise ConnectionError("Follow-up RAG chain is not available.")
    print(f"🧠 Generating RAG-based follow-up questions for: '{chief_complaint}'...")
    return deep_dive_rag_chain.invoke({
        "chief_complaint": chief_complaint,
        "initial_answers": initial_answers
    })
