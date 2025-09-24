# 🩺 SecureMed Chat - Privacy-First Medical Intake Assistant

A privacy-focused, AI-powered medical intake system that helps patients organize their health information before doctor visits. Built with a zero-persistence architecture ensuring complete data privacy.

**Live Demo**: [https://caazzi-securemed.hf.space/](https://caazzi-securemed.hf.space/)

## 🎯 Project Overview

SecureMed Chat is an intelligent medical anamnesis assistant that generates contextual questions based on patient symptoms, helping them prepare comprehensive health summaries for their healthcare providers. The system uses RAG (Retrieval-Augmented Generation) with medical knowledge to ensure relevant and medically-informed questioning.

## 🏗️ Architecture

### System Components

```
┌─────────────────┐
│  Gradio Frontend│ ──────► HuggingFace Spaces
└────────┬────────┘
         │ HTTPS + API Key
         ▼
┌─────────────────┐
│  FastAPI Backend│ ──────► GCP Cloud Run (2Gi Memory)
└────────┬────────┘         - Auto-scaling with min 1 instance
         │                   - VPC Connector for secure DB access
         ├──────────┐
         ▼          ▼
┌─────────────┐  ┌──────────────┐
│ Vertex AI   │  │ChromaDB Vector│ ──► GCP VM Instance
│ LLM Models  │  │    Store      │     (Internal Network Only)
└─────────────┘  └──────────────┘
```

### Technology Stack

- **Backend**: FastAPI with async/await patterns
- **LLM**: Google Vertex AI (Gemini 2.5 Flash Lite)
- **Embeddings**: Gemini Embedding Model
- **Vector Store**: ChromaDB for medical knowledge retrieval
- **Frontend**: Gradio with internationalization (EN/PT)
- **PDF Generation**: ReportLab (in-memory generation)
- **Deployment**: 
  - API: GCP Cloud Run (Serverless)
  - Vector DB: GCP Compute Engine VM
  - UI: HuggingFace Spaces

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
- **Network Isolation**: ChromaDB accessible only via internal VPC
- **Secret Management**: Using GCP Secret Manager for API keys
- **TLS/HTTPS**: All communications encrypted in transit

### Privacy Features

- **Session-Based Processing**: Data exists only for request duration
- **No User Accounts**: No registration or login required
- **Explicit Disclaimers**: Clear messaging that output is not medical advice
- **Data Minimization**: Only essential information collected (age bracket, not exact age)

## 🔄 Request Flow

1. **User Input** → Gradio interface collects symptoms
2. **Question Generation** → RAG retrieves relevant medical context
3. **Streaming Response** → Questions streamed to user in real-time
4. **Answer Collection** → User provides detailed responses
5. **Summarization** → LLM structures information into medical format
6. **PDF Generation** → In-memory PDF creation and immediate download
7. **Session End** → All data cleared from memory

## 🚀 Deployment Configuration

### Cloud Run Deployment

```bash
gcloud run deploy securemed-chat-service \
  --source . \
  --project=securemed-chat \
  --region=southamerica-east1 \
  --vpc-connector=api-to-db-connector \
  --memory=2Gi \
  --min-instances=1 \
  --service-account=securemed-cr-sa@securemed-chat.iam.gserviceaccount.com \
  --set-env-vars=CHROMA_HOST=securemed-chat.southamerica-east1-a.c.securemed-chat.internal,CHROMA_PORT=8000 \
  --set-secrets=SECUREMED_API_KEY=SECUREMED_API_KEY:latest
```

### Performance Optimizations

- **Lazy Loading**: Models initialized only on first request
- **MMR Retrieval**: Using Maximum Marginal Relevance for diverse context
- **Streaming Responses**: Real-time question delivery
- **Optimized Workers**: Gunicorn with 2 workers for optimal concurrency
- **Multi-stage Docker**: Minimized container size (~200MB)

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

1. **Why RAG over Fine-tuning?**: Maintains flexibility and avoids training on patient data
2. **Why ChromaDB?**: Lightweight, efficient for medical document retrieval
3. **Why Vertex AI?**: HIPAA-compliant infrastructure, regional deployment
4. **Why In-Memory Processing?**: Absolute privacy guarantee

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