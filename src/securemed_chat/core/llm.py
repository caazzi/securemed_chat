"""
Core LLM and Embeddings Module.
"""
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings
from .config import LLM_MODEL, EMBEDDING_MODEL, REGION, PROJECT_ID

# Initialize the Chat Model (LLM) for conversational tasks and summarization
# PERFORMANCE: Enabled streaming to allow for real-time data transfer to the client.
llm = ChatVertexAI(
    model_name=LLM_MODEL,
    temperature=0.2,
    project=PROJECT_ID,
    location=REGION,
    streaming=True
)

# Initialize the Embeddings Model for converting text to vectors
embeddings = VertexAIEmbeddings(
    model_name=EMBEDDING_MODEL,
    project=PROJECT_ID,
    location=REGION
)

print("✅ Vertex AI LLM and Embedding models initialized.")

