SecureMed Chat
SecureMed Chat is a privacy first medical chatbot designed to help patients organize their medical history and symptoms before a doctor's visit. It uses a Retrieval-Augmented Generation (RAG) architecture with Google's Gemini models via Vertex AI to ask clinically relevant questions and generate a structured PDF summary for the patient to share.

Core Architecture
This application is built with a modular, service-oriented design in mind, ensuring security, scalability, and clinical relevance.
Backend API: Built with FastAPI, serving as the central orchestrator.
LLM Service: Leverages Google Vertex AI for access to powerful models like Gemini for question generation and summarization.
RAG Pipeline: The "Clinical Brain" of the application.
Knowledge Base: A curated collection of medical documents (PDFs) forms the basis of the chatbot's knowledge.
Vector Database: Uses FAISS to store document embeddings and perform rapid semantic searches for relevant clinical context.
Orchestration: LangChain is used to tie together the retriever, prompts, and the LLM into a coherent chain.

Setup and Installation
Follow these steps to set up and run the project locally.
1. Prerequisites
Python 3.10+
A Google Cloud Platform (GCP) account with a project created.
Google Cloud SDK (gcloud) installed on your machine.
2. Clone the Repository
git clone <your-repository-url>
cd securemed-chat

3. Set Up a Virtual Environment
It is highly recommended to use a virtual environment.
python -m venv smc-env
source smc-env/bin/activate
# On Windows, use: smc-env\Scripts\activate


4. Install Dependencies
pip install -r requirements.txt


5. Authenticate with Google Cloud
You need to authenticate your local machine to allow the application to access Vertex AI services.
# This will open a browser window to log you in.
gcloud auth application-default login

# IMPORTANT: Set the quota project to your GCP project ID.
# Replace 'your-gcp-project-id' with the actual ID.
gcloud auth application-default set-quota-project your-gcp-project-id


How to Run the Application
1. Populate the Knowledge Base
Place your curated medical PDF documents inside the /knowledge_base directory. The quality of these documents directly impacts the relevance of the chatbot's questions.
2. Build the Vector Store
This is a one-time step that processes the PDFs in your knowledge base and creates a local FAISS vector database. Run this script from the project's root directory.
python scripts/build_vector_store.py


3. Run the API Server
Start the FastAPI application using Uvicorn.
uvicorn src.securemed_chat.main:app --reload --host 0.0.0.0


--reload: Automatically restarts the server when you make code changes.
--host 0.0.0.0: Makes the server accessible from your local network (necessary for WSL).
The API will be running at http://localhost:8000.
How to Test
1. Interactive API Documentation
Once the server is running, the easiest way to test the full workflow is via the interactive Swagger UI.
Open your browser to: http://localhost:8000/docs
You can test the /api/generate-questions and /api/summarize-and-create-pdf endpoints directly from this interface.
