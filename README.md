# 🩺 SecureMed Chat - Privacy-First Medical Intake Assistant

A privacy-focused, AI-powered medical intake system that helps patients organize their health information before doctor visits. Built with a zero-persistence architecture ensuring complete data privacy.

**Local Preview**: Run `docker compose up` to start the full stack.

## 🎯 Project Overview

SecureMed Chat is an intelligent medical anamnesis assistant that generates contextual questions based on patient symptoms, helping them prepare comprehensive health summaries for their healthcare providers. The system uses RAG (Retrieval-Augmented Generation) with medical knowledge to ensure relevant and medically-informed questioning.

## 🏗️ Architecture

### System Components

```
┌─────────────────┐
│  Reflex UI      │ ──────► Premium Glassmorphism Frontend (Port 3000)
└────────┬────────┘
         │ WebSocket / HTTPS
         ▼
┌─────────────────┐
│  FastAPI Backend│ ──────► GCP Cloud Run (Scale to Zero)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Redis Session  │ ──────► Ephemeral Context (30m TTL)
└─────────────────┘
```

### Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Session Manager**: Redis (Ephemeral with 30-minute TTL)
- **Frontend**: Reflex (Compiles to React/Next.js)
- **Deployment**: 
  - API: GCP Cloud Run (Serverless) / Docker
  - Frontend: Reflex Cloud / Vercel / Railway

## 🔐 Privacy & Security Architecture

### Zero-Persistence Design

1. **No Data Storage**: 
   - All patient information exists only in memory during the session
   - No database records of patient data
   - No file system persistence

2. **In-Memory PDF Generation**:
   ```python
   # PDFs are generated in memory and streamed directly
   buffer = io.BytesIO()
   # ... PDF generation ...
   pdf_bytes = buffer.getvalue()
   buffer.close()
   ```

3. **Structured Logging Without PII**:
   ```python
   # Logs track operations but never patient data
   logging.info(f"Streaming initial questions for new session (lang={lang}).")
   # Never: logging.info(f"Patient complaint: {complaint}")
   ```

### Security Measures

- **API Key Authentication**: All endpoints protected with X-API-KEY header
- **Input Sanitization**: All user inputs stripped and validated
- **Secret Management**: Using GCP Secret Manager for API keys
- **TLS/HTTPS**: All communications encrypted in transit

### Privacy Features

- **Ephemeral Session State**: No data is permanently stored. A Redis cache handles 30-minute state persistence for active wizards before permanent deletion.
- **Data Minimization**: Only essential information collected (age bracket, not exact age).
- **In-Memory PDF Generation**: Reports are generated in RAM and streamed directly to the patient's browser.
- **No User Accounts**: Complete anonymity by design. No registration or PII required.

## 🔄 Request Flow

1. **Demographics** → Patient provides age, gender, and language preference in the Reflex UI.
2. **Session Init** → Backend generates a short-lived `session_id` in Redis.
3. **Assessment (OPQRST)** → Real-time streaming of symptom-specific questions.
4. **History (SAMPLE)** → Clinical follow-up questions to build a deeper medical profile.
5. **PDF Generation** → In-memory summarization and instant download.
6. **Session Expiry** → Redis key is destroyed after 30 minutes of inactivity.

## 🚀 Deployment Configuration

### Cloud Run Deployment

```bash
gcloud run deploy securemed-chat-service \
  --source . \
  --project=securemed-chat \
  --region=southamerica-east1 \
  --memory=2Gi \
  --min-instances=0 \
  --service-account=securemed-cr-sa@securemed-chat.iam.gserviceaccount.com \
  --set-secrets=SECUREMED_API_KEY=SECUREMED_API_KEY:latest
```

### Local Development (Docker Compose)

The easiest way to start the full stack (Redis + API) is:
```bash
docker compose up --build
```

### Performance & Scaling
- **Cold Starts**: Optimized for ~3sec startup, allowing for "Scale-to-Zero" to eliminate idle costs.
- **Concurrency**: Gunicorn with Uvicorn workers ensures high throughput per instance.
- **Verification**: 100% Backend test coverage (Unit, Integration, Security).

## 📊 API Endpoints

| Endpoint | Purpose | Privacy Consideration |
|----------|---------|----------------------|
| `/api/initial-questions-stream` | Generate symptom questions | No data persistence |
| `/api/follow-up-questions-stream` | Generate medical history questions | Context exists only in request |
| `/api/summarize-and-generate-pdf` | Create medical summary PDF | In-memory generation, immediate disposal |

## 🌍 Internationalization

The system supports multiple languages with complete UI and content translation:

- **English** (en): Default language
- **Portuguese** (pt): Full translation including PDF output
- Language auto-detected from browser settings

## 🛡️ Security Best Practices Implemented

1. **Principle of Least Privilege**: Service accounts with minimal permissions
2. **Defense in Depth**: Multiple security layers (API key, VPC, IAM)
3. **Input Validation**: Pydantic models with field constraints
4. **Error Handling**: Graceful degradation without exposing internals
5. **Rate Limiting**: Built-in Cloud Run throttling
6. **Secure Defaults**: No default API keys in production

## 📈 Monitoring & Observability

- Structured logging for operational insights
- No PII in logs or metrics
- Cloud Run automatic metrics (latency, errors, traffic)
- Health check endpoint at root path

## 🤝 Contributing

We welcome contributions! Please:

1. **Test the live demo**: [https://caazzi-securemed.hf.space/](https://caazzi-securemed.hf.space/)
2. **Review the code** for security and privacy improvements
3. **Suggest enhancements** via issues or pull requests

### Areas for Contribution

- [ ] Additional language support
- [ ] Enhanced medical knowledge base
- [ ] Accessibility improvements (WCAG compliance)
- [ ] Performance optimizations
- [ ] Security audit findings
- [ ] Documentation improvements

## 📝 Compliance & Disclaimers

- **Not Medical Advice**: System explicitly disclaims medical advisory capacity
- **Data Protection**: Designed with GDPR/LGPD principles (no data retention)
- **Healthcare Integration**: Not intended for direct EHR integration
- **Age Verification**: System designed for adult users (18+)

## 🔍 Code Review Focus Areas

When reviewing the code, please pay special attention to:

1. **Privacy Leaks**: Any inadvertent data persistence
2. **Security Vulnerabilities**: Input validation, injection attacks
3. **Performance Bottlenecks**: Async operations, memory usage
4. **Error Handling**: Graceful failures, user experience
5. **Internationalization**: Translation completeness and accuracy

## 📖 Technical Documentation

### Key Design Decisions

1. **Why Prompt Engineering over RAG?**: Foundation models already contain vast medical knowledge. Rigorous clinical frameworks (OPQRST) yield cleaner results than retrieving sparse PDF snippets.
2. **Why Vertex AI?**: HIPAA-compliant infrastructure, regional deployment
3. **Why In-Memory Processing?**: Absolute privacy guarantee

### Performance Metrics

- Cold start: ~3-5 seconds (mitigated by min-instances=1)
- Question generation: <2 seconds
- PDF generation: <1 second
- Memory footprint: ~500MB per concurrent request

## 📬 Contact & Support

For questions about the architecture or to report security concerns, please open an issue with the appropriate label:

- 🔐 `security` - Security vulnerabilities (use responsible disclosure)
- 🔒 `privacy` - Privacy concerns or improvements
- 🏗️ `architecture` - Architectural suggestions
- 📚 `documentation` - Documentation improvements

---

**Remember**: This system is designed for informational purposes only and should not replace professional medical consultation. Always consult with qualified healthcare providers for medical advice.