# SecureMed Chat — Privacy-First Medical Intake Assistant

An AI-powered web app that helps patients organize their symptoms before a doctor's visit. The core design constraint: **zero data persistence** — no database, no user accounts, no logs containing health data.

---

## The Problem

Patients arrive at consultations anxious and forget key details. Doctors have limited time. The gap between what the patient knows and what the doctor hears costs both sides.

SecureMed bridges that gap with a guided AI interview that generates a structured clinical summary — then destroys all data when the session ends.

---

## How It Works

1. Patient enters their specialty and chief complaint in plain text
2. The AI generates 3–5 targeted follow-up questions using clinical frameworks (OPQRST + SAMPLE)
3. Answers are compiled into a structured summary the patient can download as a PDF
4. Session data is destroyed — nothing is retained on the server

---

## Architecture

```
┌─────────────────┐
│  Reflex UI      │ ──────► Glassmorphism Frontend (Port 3000)
└────────┬────────┘
         │ WebSocket / HTTPS
         ▼
┌─────────────────┐
│  FastAPI Backend│ ──────► GCP Cloud Run (Scale to Zero)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Redis Session  │ ──────► Ephemeral Context (30-min TTL, then destroyed)
└─────────────────┘
```

---

## Privacy Model

No health data is ever written to disk. Every design decision flows from this constraint:

- **No database** — session state lives in Redis with a 30-minute TTL
- **No user accounts** — complete anonymity, no registration required
- **In-memory PDF generation** — reports are built in RAM and streamed directly to the browser
- **PII-free logs** — structured logging tracks operations, never patient content
- **No model training** — API calls use contracts that exclude session data from training

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Gunicorn/Uvicorn |
| Session | Redis (ephemeral, 30-min TTL) |
| Frontend | Reflex (compiles to React/Next.js) |
| AI | Vertex AI (Gemini) |
| Deployment | GCP Cloud Run (serverless, scale-to-zero) |
| CI/CD | GitHub Actions — 100% test coverage (unit, integration, security) |

---

## Key Design Decision: Prompt Engineering over RAG

Early versions used ChromaDB and a VM-based RAG pipeline. We replaced it with specialized clinical prompt engineering using established frameworks (OPQRST for symptom assessment, SAMPLE for medical history).

Foundation models already contain the necessary medical knowledge. Structured prompting yields cleaner, faster results at a fraction of the infrastructure cost — eliminating ~$100/month in cloud spend.

---

## Local Setup

```bash
docker compose up --build
```

Starts Redis + FastAPI backend. Then run the frontend:

```bash
cd reflex_app && reflex run
```

Requires a `.env` file with:
```
SECUREMED_API_KEY=your_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

---

## Deployment (GCP Cloud Run)

```bash
gcloud run deploy securemed-chat-service \
  --source . \
  --project=securemed-chat \
  --region=southamerica-east1 \
  --memory=2Gi \
  --min-instances=0 \
  --set-secrets=SECUREMED_API_KEY=SECUREMED_API_KEY:latest
```

---

> **Disclaimer**: SecureMed is an organizational tool, not a medical device. It does not provide diagnoses or medical advice. Always consult a qualified healthcare provider.
