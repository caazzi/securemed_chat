"""
Core LLM and Embeddings Module.

This module initializes and provides centralized access to the Large Language Model (LLM)
and the text embedding model from Google Vertex AI.

By centralizing model initialization, we ensure that the models are loaded only once
and can be easily reused across different parts of the application (e.g., RAG service,
summarization endpoint). This also makes it simple to swap out models by changing
the configuration in one place.
"""

from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings
from config import LLM_MODEL, EMBEDDING_MODEL, REGION, PROJECT_ID

# Initialize the Chat Model (LLM) for conversational tasks and summarization
# A low temperature is used for more deterministic and factual outputs.
llm = ChatVertexAI(
    model_name=LLM_MODEL,
    temperature=0.2,
    project=PROJECT_ID,
    location=REGION
)

# Initialize the Embeddings Model for converting text to vectors
embeddings = VertexAIEmbeddings(
    model_name=EMBEDDING_MODEL,
    project=PROJECT_ID,
    location=REGION
)

print("✅ Vertex AI LLM and Embedding models initialized.")
