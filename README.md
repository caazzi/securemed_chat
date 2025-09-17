---
title: securemed_chat
app_file: gradio_app.py
sdk: gradio
sdk_version: 5.45.0
---
# SecureMed Chat 🩺

SecureMed Chat is a privacy-first, AI-powered medical chatbot designed to help patients intelligently organize their medical history and symptoms before a doctor's visit. It aims to bridge the communication gap between patient and provider by creating a structured, clinically-relevant summary of the patient's condition.

The core of the application is a Retrieval-Augmented Generation (RAG) architecture that grounds a powerful Large Language Model (LLM) in established medical knowledge. This ensures the questions asked are safe, relevant, and helpful, avoiding the risk of clinical "hallucinations".

---

## ✨ Core Principles

This project is built on a foundation of key principles outlined in its architecture:

- **Security & Privacy First:** All components are designed with patient privacy as the top priority, with a goal of being stateless regarding personal health information (PHI).
- **Modularity:** The system is composed of distinct services (API, LLM, RAG, PDF generation), allowing for easier updates, scaling, and maintenance.
- **Clinical Relevance:** The RAG system, our "Clinical Brain," ensures the LLM's interactions are grounded in a curated medical knowledge base.
- **User Experience:** The conversational flow is designed to be simple, intuitive, and reassuring for the patient.

---

## 🏗️ Architecture Overview

The application uses a modular, service-oriented design. The FastAPI Backend Server acts as the central **Orchestrator**, managing the conversation flow and coordinating between services.

When a user submits their main symptom, the Orchestrator queries the **RAG Pipeline** (the "Clinical Brain"). This pipeline performs a semantic search on a **FAISS Vector Database**—built from a curated knowledge base of medical guidelines and anamnesis frameworks—to find the most relevant clinical context. This context is then combined with the user's input and sent to **Google's Gemini model via Vertex AI**, which generates a set of clinically-relevant questions for the patient.

```mermaid
graph TD
    subgraph User
        A[Patient]
    end

    subgraph System
        B(FastAPI Orchestrator)
        C(RAG Pipeline - 'The Clinical Brain')
        D{Vector DB <br> (FAISS)}
        E(LLM Service <br> (Gemini on Vertex AI))
        F(PDF Generation)
    end

    A -- 1. Chief Complaint --> B
    B -- 2. Query --> C
    C -- 3. Semantic Search --> D
    D -- 4. Retrieve Context --> C
    C -- 5. Augmented Prompt --> E
    E -- 6. Generate Questions --> B
    B -- 7. Send Questions --> A
    A -- 8. Answers --> B
    B -- 9. Summarize --> E
    E -- 10. Structured Summary --> B
    B -- 11. Generate Report --> F
    F -- 12. PDF --> A
```

---

## 🚀 Project Status & Roadmap

This project is actively under development. Here is the current status and a look at what's next.

### ✅ Implemented Features

- **Backend API:** Fully functional orchestrator built with FastAPI.
- **RAG Pipeline:** The "Clinical Brain" is operational, using LangChain to connect the retriever and LLM.
- **Vector Database:** Local vector store creation and search using FAISS.
- **LLM Integration:** Question generation and summarization powered by Google's Gemini models via Vertex AI.
- **PDF Generation:** On-the-fly creation of a structured PDF summary.

### 🗺️ Future Roadmap

- **User Interface:** Develop a simple and secure front-end client (e.g., a web app or a WhatsApp integration) to replace API-based testing.
- **Enhanced Security:** Implement robust, HIPAA-compliant security protocols for handling any potential data in transit.
- **Knowledge Base Expansion:** Continuously curate and expand the medical knowledge base with more clinical guidelines and symptom-specific question sets.
- **Deployment:** Containerize the services and deploy them to a secure cloud environment.

---

## 🛠️ Getting Started

Follow these steps to set up and run the project locally.

### 1. Prerequisites

- Python 3.10+
- A Google Cloud Platform (GCP) account with a project created.
- Google Cloud SDK (`gcloud`) installed and configured on your machine.

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd securemed-chat
```

### 3. Set Up a Virtual Environment

It is highly recommended to use a virtual environment.

```bash
# Create the environment
python -m venv smc-env

# Activate it (Linux/macOS)
source smc-env/bin/activate

# Activate it (Windows)
smc-env\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Authenticate with Google Cloud

You need to authenticate your local machine to allow the application to access Vertex AI services.

```bash
# This will open a browser window to log you in.
gcloud auth application-default login

# IMPORTANT: Set the quota project to your GCP project ID.
# Replace 'your-gcp-project-id' with the actual ID.
gcloud auth application-default set-quota-project your-gcp-project-id
```

---

## ⚙️ How to Run the Application

### 1. Populate the Knowledge Base

Place your curated medical PDF documents inside the `/knowledge_base` directory. The quality and relevance of these documents directly impact the chatbot's performance. Good sources include clinical textbooks or anamnesis frameworks like OLDCARTS.

### 2. Build the Vector Store

This is a one-time step that processes the PDFs in your knowledge base and creates a local FAISS vector database. Run this script from the project's root directory.

```bash
python scripts/build_vector_store.py
```

### 3. Run the API Server

Start the FastAPI application using Uvicorn.

```bash
uvicorn src.securemed_chat.main:app --reload --host 0.0.0.0
```

- `--reload`: Automatically restarts the server when you make code changes.
- `--host 0.0.0.0`: Makes the server accessible from your local network.

The API will be running at `http://localhost:8000`.

---

## 🧪 How to Test

Once the server is running, the easiest way to test the full workflow is via the interactive Swagger UI documentation.

1.  Open your browser to: [http://localhost:8000/docs](http://localhost:8000/docs)
2.  Use the `/api/generate-questions` endpoint to simulate a user providing their chief complaint.
3.  Use the `/api/summarize-and-create-pdf` endpoint to provide answers and receive the final PDF summary.