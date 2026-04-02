# SecureMed Chat — Diagnostic Report

> Principal Engineer review performed 2026-04-02.  
> Scope: entire repository. Diagnostic only — no solutions prescribed.

---

## 🔴 Critical — Security

### 1. Hardcoded Internal IP Address in Source Code
`src/securemed_chat/core/config.py:32` — The ChromaDB fallback host is a **literal public IP** (`34.151.247.35`). This IP is committed to the repository and accessible to anyone who clones it. The README claims the VM is "internal network only," but the default in code points to a routable address.

### 2. API Key Guard Is a Warning, Not a Guard
`src/securemed_chat/core/config.py:15-19` — When `SECUREMED_API_KEY` is missing, the application **prints a warning and continues running**. The `raise ValueError` is commented out. This means the API can start in production with no authentication enforced, since `get_api_key()` in `endpoints.py` compares the header against `None`.

### 3. `.envrc` Committed with Production API URL
`.envrc` contains the full production Cloud Run service URL. This file is **not** in `.gitignore` (`.gitignore` lists `.envrc`, but the file exists in the working tree per its presence on disk). If it was committed at any point in history, the URL is permanently in the git history.

### 4. Default API Key in Frontend: `"your_default_secret_key_for_dev"`
`gradio/gradio_app.py:22` — The fallback for `SECUREMED_API_KEY` is a hardcoded string. If the env var is unset in a deployed Gradio space, this weak default is sent as the API key header.

### 5. Error Messages Leak Internal Details to Clients
`endpoints.py:93,96` — HTTP error responses include raw exception messages via f-strings (e.g., `f"Failed to generate initial questions: {e}"`). Stack traces, ChromaDB connection errors, and internal paths can be exposed to callers.

---

## 🟠 High — Architecture & Correctness

### 6. Frontend–Backend API Contract Mismatch
The root-level `gradio_app.py` calls endpoints named `GENERATE_QUESTIONS_URL` and `CREATE_PDF_URL` with a payload shape (`{"chief_complaint": ..., "patient_answers": ...}`) that **does not match** any of the current FastAPI endpoints. The actual backend expects `InitialRequest(chief_complaint, age, gender, lang)`. This root `gradio_app.py` is non-functional against the current API.

### 7. `.envrc` Endpoint URLs Don't Match Actual API Routes
`.envrc` defines routes like `/initial-questions` and `/summarize-and-create-pdf`, but the actual FastAPI routes are `/api/initial-questions-stream` and `/api/summarize-and-generate-pdf`. These will 404.

### 8. Thread-Unsafe Singleton Pattern with Gunicorn Workers
`core/llm.py` and `services/rag_service.py` use module-level globals (`_llm`, `_vector_store`, etc.) for lazy initialization. With `gunicorn -w 2` (Dockerfile), each worker `fork`s the process. Globals are not shared — each worker initializes its own copy. The `global` keyword provides no thread/process safety and there is no locking, so concurrent requests within a single worker can race during initialization.

### 9. No Page-Break Handling in PDF Generation
`services/pdf_service.py` draws content using a decreasing `y_pos` but **never checks** if `y_pos` goes below the page margin. Long patient answers will be rendered off the bottom of the page and silently truncated.

### 10. Temp File Leak in Gradio PDF Flow
`gradio/gradio_app.py:187-212` — A `tempfile.mkdtemp()` is created for each PDF download but **never cleaned up**. The comment on line 209 acknowledges this and hopes "Gradio or the OS will handle cleanup." On a long-running HuggingFace Space, these directories accumulate indefinitely.

---

## 🟡 Medium — Code Quality & Maintainability

### 11. Three Separate `gradio_app.py` Files, Only One Is Active
There are three distinct Gradio frontends:
- `./gradio_app.py` (root, 190 lines — outdated, wrong API contract)
- `./gradio/gradio_app.py` (305 lines — the deployed HF Spaces version)
- `./old_versions/gradio_app.py` + four more numbered copies

It is unclear which is canonical. The root-level `gradio_app.py` and the `gradio/` version have **completely different** API contracts, UI flows, and i18n approaches.

### 12. `old_versions/` Directory Is a Dumping Ground
Contains 5 copies of `gradio_app.py` with numbered names (`(1).py`, `(2).py`, etc.), old notebooks, Zone.Identifier files (Windows NTFS metadata), and a `planned_architecture.pdf`. This directory is `.gitignore`'d but still exists on disk, adding confusion.

### 13. Inconsistent Logging: `print()` vs `logging`
- `config.py` uses `print()` with emoji (`✅ Configuration loaded`)
- `llm.py` uses `logging.info()`
- `pdf_service.py` uses `print()` with emoji (`📄 Structured PDF report...`)
- `gradio/gradio_app.py` uses `print()` with `DEBUG:` and `ERROR:` prefixes

There is no unified logging strategy. The `print()` calls bypass structured logging and won't appear correctly in Cloud Run log aggregation.

### 14. Unpinned Dependencies
`requirements.txt` has **zero version pins**. Every dependency (`fastapi`, `langchain`, `chromadb`, `gradio`, etc.) will resolve to `latest` at build time. A single breaking change in any upstream package will silently break production builds.

### 15. `langchain_community` Import for `Chroma` Is Deprecated
`rag_service.py:18` imports `from langchain_community.vectorstores import Chroma`. LangChain has announced this path as deprecated in favor of `langchain_chroma`. This will break in a future LangChain release.

### 16. No `__init__.py` Exports
`src/securemed_chat/api/__init__.py`, `core/__init__.py`, and `services/__init__.py` exist but appear empty (0 bytes). There are no explicit `__all__` exports, making the package interface implicit.

### 17. `langdetect` Is a Listed Dependency but Never Used
`requirements.txt` includes `langdetect`, but no source file imports or references it. The language is determined via the `lang` field sent from the frontend.

---

## 🔵 Low — Repository Hygiene & DevOps

### 18. Zero Tests
There are no test files, no test directory, no pytest/unittest configuration, and no CI/CD pipeline. For a medical application with privacy claims, this is a significant gap in quality assurance.

### 19. `__pycache__` Directories Exist in the Repository
Multiple `__pycache__/` directories are present on disk across `src/`. While `.gitignore` excludes them, their presence suggests they may have been committed in earlier history or that builds run inside the repo root.

### 20. Dockerfile Uses Deprecated `as` Syntax
`Dockerfile:2` — `FROM python:3.11 as builder` uses the legacy `as` keyword. The modern syntax is `FROM python:3.11 AS builder` (uppercase). While still functional, this emits deprecation warnings in recent Docker/BuildKit versions.

### 21. `.dockerignore` Has a Typo
`.dockerignore:16` lists `pycache/` instead of `__pycache__/`. The actual Python cache directories are named `__pycache__` and won't be excluded by this pattern.

### 22. `vector_store/index.pkl` — 43 MB Pickle File
A 43 MB pickle file sits in `vector_store/`. While `.gitignore` excludes `vector_store/`, if this was ever committed, it bloats git history permanently. Pickle files also carry deserialization security risks.

### 23. `run-scaler/` Is Untracked and Undocumented
`git status` shows `run-scaler/` as an untracked directory. It contains a Cloud Function for scaling Cloud Run min-instances, but there's no documentation on how to deploy it, what Pub/Sub topic it subscribes to, or what IAM permissions it needs.

### 24. `gradio` dependency in API `requirements.txt`
The API server's `requirements.txt` includes `gradio`, which is a ~200 MB dependency. The API (FastAPI backend) never imports or uses Gradio. This needlessly inflates the Docker image.

### 25. `Runnable` Type Hint from LangChain on Public API
`endpoints.py:20` imports `Runnable` from `langchain_core.runnables` and uses it as a type annotation on endpoint `Depends()` parameters. This tightly couples the API layer to LangChain internals. If LangChain restructures its module tree, the API endpoints break.

---

## 📊 Summary by Severity

| Severity | Count |
|----------|-------|
| 🔴 Critical (Security) | 5 |
| 🟠 High (Architecture) | 5 |
| 🟡 Medium (Code Quality) | 7 |
| 🔵 Low (Hygiene/DevOps) | 8 |
| **Total** | **25** |
