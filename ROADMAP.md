# 🗺️ SecureMed Chat - Roadmap & Future Improvements

This document tracks upcoming planned architecture upgrades, technical debt, and product enhancements for SecureMed Chat. 

## 🏗️ Architecture & UX Upgrades

### 1. Frontend Migration (Deprecating Gradio)
* **Problem:** Gradio is excellent for fast prototyping, but lacks the granular UI/UX control, WCAG accessibility compliance, and robust state management required for a production-grade medical application.
* **Solution:** Replace the Gradio frontend with a more robust **Python-native framework** that allows for advanced state management and granular UI control. Top candidates include:
  * **Reflex** (formerly Pynecone): The best option for production. You write pure Python, but it compiles underneath to a high-performance React/Next.js web app.
  * **Streamlit**: The industry standard for Python UIs. Excellent component library and native `st.session_state` makes multi-step wizards very easy to build.
  * **Chainlit**: Purpose-built for AI conversational agents. Provides a beautiful default chat UI and handles streaming flawlessly out of the box.

### 2. Ephemeral Session State Management
* **Problem:** True "zero persistence" currently forces the frontend to send the entire conversation history back to the backend on every request. If a user's browser refreshes during Step 2, they lose all progress.
* **Solution:** Introduce an "Ephemeral State" model using **Redis** with a strict 30-minute Time-To-Live (TTL). The backend provides a short-lived `session_id`. When the session expires, the key is permanently destroyed. This preserves privacy while drastically improving user experience against accidental disconnects.

---

## 🛠️ Code Maintenance & Technical Debt

### 1. Robust PDF Pagination
* **Issue:** In `services/pdf_service.py`, if a patient provides an extremely long medical history, the text will run off the bottom of the PDF page and be silently truncated.
* **Fix:** Implement robust page-break logic in ReportLab (e.g., checking `if y_pos < inch: c.showPage()`) to dynamically handle overflowing text.

### 2. Dependency Management
* **Issue:** `requirements.txt` has unpinned dependencies, which can cause silent build breakages if upstream packages push breaking changes. Also, `langdetect` is listed but currently unused.
* **Fix:** Use a virtual environment snapshot (`pip freeze`) or a tool like `poetry`/`pip-tools` to strongly pin versions. Remove `langdetect`.

### 3. Dockerfile best practices
* **Issue:** The Dockerfile uses the legacy lowercase `as builder` syntax. 
* **Fix:** Update to modern `AS builder` syntax. Consider utilizing multi-stage builds more aggressively if image size becomes a concern again.

### 4. CI/CD & Test Coverage
* **Issue:** We have baseline integration tests (`test_api_integration.py`) and security assertions (`test_security.py`), but lack unit tests for individual agents and endpoints.
* **Fix:** Implement a GitHub Actions workflow that automatically runs `pytest` on every Pull Request, and mandate minimum test coverage constraints.

---

## 📚 Historical Context
*Note: Severe security vulnerabilities (hardcoded IPs, insecure default API keys) and expensive architectural bloat (dedicated RAG/ChromaDB VMs) were successfully resolved in the `feature/prompt-engineering` refactor (April 2026). The deployment now scales to zero cost on Cloud Run.*
