"""
Gradio frontend for the SecureMed Anamnesis workflow API.
This script creates a functional, mobile-first, step-by-step user interface 
that consumes the FastAPI endpoints to generate a medical summary.
"""
import gradio as gr
import os
import httpx
import re
import json
import tempfile
import shutil
from typing import AsyncGenerator
from dotenv import load_dotenv

# --- Initial Setup ---
load_dotenv()

INITIAL_QUESTIONS_URL = os.getenv("INITIAL_QUESTIONS_URL", "http://localhost:8000/api/initial-questions-stream")
FOLLOW_UP_QUESTIONS_URL = os.getenv("FOLLOW_UP_QUESTIONS_URL", "http://localhost:8000/api/follow-up-questions-stream")
PDF_URL = os.getenv("PDF_URL", "http://localhost:8000/api/summarize-and-generate-pdf")

SECUREMED_API_KEY = os.getenv("SECUREMED_API_KEY", "your_default_secret_key_for_dev")
HEADERS = {"X-API-KEY": SECUREMED_API_KEY}

if not SECUREMED_API_KEY or SECUREMED_API_KEY == "your_default_secret_key_for_dev":
    print("Warning: SECUREMED_API_KEY is not set or is using a default value. This is not secure for production.")

# --- Enhanced CSS for a professional, theme-aware (light/dark mode) medical theme ---
# This CSS now uses Gradio's built-in theme variables (--variable-name)
# to ensure it adapts perfectly to both light and dark modes.
PROFESSIONAL_CSS = """
/* --- Overall Layout & Font --- */
.gradio-container { 
    max-width: 650px !important; 
    margin: auto !important; 
    padding-top: 2rem; 
    background-color: var(--background-fill-secondary) !important;
}
/* --- App Header --- */
.app-title { 
    font-size: 2.2rem; 
    font-weight: 700; 
    text-align: center; 
    color: var(--neutral-900);
}
.app-subtitle { 
    font-size: 1.1rem; 
    color: var(--neutral-600);
    text-align: center; 
    margin-bottom: 2.5rem; 
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
}
/* --- Content Cards --- */
.step-container { 
    padding: 2rem; 
    margin: 1rem 0; 
    border-radius: var(--radius-xl); 
    box-shadow: var(--shadow-drop-lg);
    background-color: var(--background-fill-primary); 
    border: 1px solid var(--border-color-primary); 
}
.step-title { 
    font-size: 1.6rem; 
    font-weight: 600; 
    color: var(--primary-500); 
    margin-bottom: 0.5rem; 
}
.step-description { 
    font-size: 1rem; 
    color: var(--neutral-700);
    margin-bottom: 1.5rem; 
}
/* --- Interactive Elements --- */
.gr-button { 
    padding: 0.9rem !important; 
    font-size: 1rem !important; 
    font-weight: 600 !important; 
    border-radius: var(--radius-lg) !important;
}
/* --- Final Download Screen --- */
.download-container { 
    text-align: center; 
    padding: 2rem; 
}
.download-container h2 {
    font-size: 1.8rem;
    color: var(--primary-500); /* Using primary color for success */
}
.feedback-link { 
    margin-top: 2rem; 
    font-size: 0.9rem; 
    color: var(--neutral-500);
}
/* --- Error & Status --- */
.status-error { 
    color: var(--color-accent-soft); 
    font-weight: 500; 
    margin-top: 1rem; 
    text-align: center; 
    background-color: var(--color-accent-soft-background);
    border: 1px solid var(--color-accent);
    padding: 10px;
    border-radius: var(--radius-lg);
}
"""

# --- Helper Functions ---
def parse_age_bucket(age_bucket: str) -> int:
    """Extracts the lower bound integer from an age bucket string."""
    if not age_bucket: return 0
    numbers = re.findall(r'\d+', age_bucket)
    return int(numbers[0]) if numbers else 0

# --- API Interaction and Interface Logic ---
async def process_streaming_response(response: httpx.Response) -> AsyncGenerator[str, None]:
    """Helper to parse SSE and yield clean text content."""
    full_text = ""
    async for line in response.aiter_lines():
        if line.startswith("data:"):
            try:
                content = line[len("data:"):].strip()
                if content:
                    full_text += json.loads(content)
                    yield full_text
            except json.JSONDecodeError:
                continue

async def handle_initial_questions(chief_complaint: str, age_bucket: str, gender: str) -> AsyncGenerator:
    """Validates input and streams questions from the first API endpoint."""
    if not all([chief_complaint, age_bucket, gender]):
        error_msg = "<p class='status-error'>Please fill out all fields to continue.</p>"
        yield gr.update(), gr.update(visible=False), gr.HTML(error_msg), ""
        return

    yield gr.update(visible=False), gr.update(visible=True), gr.HTML(), "*Loading questions...*"
    
    age_int = parse_age_bucket(age_bucket)
    payload = {"chief_complaint": chief_complaint, "age": age_int, "gender": gender}
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", INITIAL_QUESTIONS_URL, json=payload, headers=HEADERS, timeout=30.0) as response:
                response.raise_for_status()
                async for clean_chunk in process_streaming_response(response):
                    yield gr.update(visible=False), gr.update(visible=True), gr.HTML(), clean_chunk

    except Exception:
        error_html = "<p class='status-error'>An error occurred while fetching questions. Please check your connection and try again.</p>"
        yield gr.update(visible=True), gr.update(visible=False), gr.HTML(error_html), ""

async def handle_follow_up_questions(chief_complaint: str, age_bucket: str, gender: str, initial_answers: str) -> AsyncGenerator:
    """Validates answers and streams questions from the second endpoint."""
    if not initial_answers.strip():
        yield gr.update(), gr.update(visible=False), gr.HTML("<p class='status-error'>Please provide answers about your symptoms before proceeding.</p>"), ""
        return
    
    yield gr.update(visible=False), gr.update(visible=True), gr.HTML(), "*Loading questions...*"
    
    age_int = parse_age_bucket(age_bucket)
    payload = {"chief_complaint": chief_complaint, "age": age_int, "gender": gender, "initial_answers": initial_answers}
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", FOLLOW_UP_QUESTIONS_URL, json=payload, headers=HEADERS, timeout=30.0) as response:
                response.raise_for_status()
                async for clean_chunk in process_streaming_response(response):
                     yield gr.update(visible=False), gr.update(visible=True), gr.HTML(), clean_chunk

    except Exception:
        error_html = "<p class='status-error'>An error occurred while fetching questions. Please check your connection and try again.</p>"
        yield gr.update(visible=True), gr.update(visible=False), gr.HTML(error_html), ""

async def handle_generate_pdf(chief_complaint: str, age_bucket: str, gender: str, initial_answers: str, follow_up_answers: str) -> AsyncGenerator:
    """Calls the PDF endpoint, receives bytes, and provides a named file for download."""
    if not follow_up_answers.strip():
        yield gr.update(), gr.update(visible=False), gr.HTML("<p class='status-error'>Please answer the medical history questions to continue.</p>"), gr.update(visible=False)
        return
    
    yield gr.update(visible=False), gr.update(visible=True), gr.HTML(), gr.DownloadButton(visible=False)

    age_int = parse_age_bucket(age_bucket)
    payload = {
        "chief_complaint": chief_complaint, "age": age_int, "gender": gender, 
        "initial_answers": initial_answers, "follow_up_answers": follow_up_answers
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(PDF_URL, json=payload, headers=HEADERS, timeout=60.0)
            response.raise_for_status()
            pdf_bytes = response.content
        
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, "Medical_Health_Summary.pdf")
        
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
            
        yield gr.update(), gr.update(), gr.HTML(), gr.DownloadButton(value=file_path, visible=True)

    except Exception:
        error_html = "<p class='status-error'>Sorry, we couldn't generate your summary due to a technical issue. Please try again.</p>"
        yield gr.update(visible=True), gr.update(visible=False), gr.HTML(error_html), gr.DownloadButton(visible=False)

def create_interface():
    """Builds and returns the Gradio interface."""
    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.blue,
        font=[gr.themes.GoogleFont("Roboto"), "ui-sans-serif", "system-ui", "sans-serif"],
    )

    with gr.Blocks(title="SecureMed Assistant", theme=theme, css=PROFESSIONAL_CSS) as interface:
        state_complaint = gr.State()
        state_age = gr.State()
        state_gender = gr.State()
        state_initial_answers = gr.State()

        gr.Markdown("<h1 class='app-title'>🩺 SecureMed Assistant</h1>")
        gr.Markdown("<p class='app-subtitle'>Feeling ready for your doctor's visit is the first step to getting better care. We'll help you organize your thoughts, and never keep any information.</p>")

        with gr.Group(visible=True) as step1:
            with gr.Column(elem_classes="step-container"):
                gr.Markdown("<h2 class='step-title'>Step 1 of 3: Your Concern</h2><p class='step-description'>First, please tell us a bit about yourself and what's bothering you.</p>")
                complaint_input = gr.Textbox(label="What's your main health concern?", placeholder="E.g., Severe headache for 2 days")
                age_input = gr.Radio(label="Age", choices=["18-29", "30-44", "45-64", "65-79", "80+"])
                gender_input = gr.Radio(label="Gender", choices=["Male", "Female", "Other"])
                status_step1 = gr.HTML()
                next_btn_1 = gr.Button("Next", variant="primary")

        with gr.Group(visible=False) as step2:
            with gr.Column(elem_classes="step-container"):
                gr.Markdown("<h2 class='step-title'>Step 2 of 3: About Your Symptoms</h2><p class='step-description'>Please describe your symptoms based on the questions below.</p>")
                initial_questions_display = gr.Markdown()
                initial_answers_input = gr.Textbox(label="Your Answers", lines=8, placeholder="Provide detailed answers here...")
                status_step2 = gr.HTML()
                with gr.Row():
                    back_btn_2 = gr.Button("Back")
                    next_btn_2 = gr.Button("Next: Medical History", variant="primary")

        with gr.Group(visible=False) as step3:
            with gr.Column(elem_classes="step-container"):
                gr.Markdown("<h2 class='step-title'>Step 3 of 3: Medical History</h2><p class='step-description'>These final questions help provide a complete picture for your doctor.</p>")
                follow_up_questions_display = gr.Markdown()
                follow_up_answers_input = gr.Textbox(label="Your Medical History", lines=8, placeholder="Provide detailed answers here...")
                status_step3 = gr.HTML()
                with gr.Row():
                    back_btn_3 = gr.Button("Back")
                    next_btn_3 = gr.Button("Generate Summary", variant="primary")

        with gr.Group(visible=False) as step4:
            with gr.Column(elem_classes="step-container download-container"):
                gr.Markdown("<h2>✅ Your Summary is Ready!</h2><p>Get the PDF below to share with your doctor.</p>")
                pdf_download_button = gr.DownloadButton("⬇️ Download Health Summary", variant="primary", visible=False)
                reset_btn = gr.Button("Start Over")
                tally_link = "https://tally.so/r/wbaPvo"
                gr.HTML(f"<div class='feedback-link'>Help us improve! <a href='{tally_link}' target='_blank' rel='noopener noreferrer'>Give Anonymous Feedback</a></div>")

        next_btn_1.click(
            lambda complaint, age, gender: (complaint, age, gender),
            inputs=[complaint_input, age_input, gender_input],
            outputs=[state_complaint, state_age, state_gender]
        ).then(
            handle_initial_questions,
            inputs=[state_complaint, state_age, state_gender],
            outputs=[step1, step2, status_step1, initial_questions_display]
        )
        
        next_btn_2.click(
            lambda answers: answers,
            inputs=[initial_answers_input],
            outputs=[state_initial_answers]
        ).then(
            handle_follow_up_questions,
            inputs=[state_complaint, state_age, state_gender, state_initial_answers],
            outputs=[step2, step3, status_step2, follow_up_questions_display]
        )

        next_btn_3.click(
            handle_generate_pdf,
            inputs=[state_complaint, state_age, state_gender, state_initial_answers, follow_up_answers_input],
            outputs=[step3, step4, status_step3, pdf_download_button]
        )

        back_btn_2.click(lambda: (gr.update(visible=True), gr.update(visible=False)), None, [step1, step2])
        back_btn_3.click(lambda: (gr.update(visible=True), gr.update(visible=False)), None, [step2, step3])

        all_steps = [step1, step2, step3, step4]
        all_inputs = [complaint_input, age_input, gender_input, initial_answers_input, follow_up_answers_input]
        all_outputs = [status_step1, status_step2, status_step3, initial_questions_display, follow_up_questions_display, pdf_download_button]
        
        def reset_state():
            return (
                gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                "", None, None, "", "",
                gr.HTML(), gr.HTML(), gr.HTML(), "", "", gr.DownloadButton(visible=False)
            )
        reset_btn.click(reset_state, outputs=all_steps + all_inputs + all_outputs)
        
    return interface

if __name__ == "__main__":
    app_interface = create_interface()
    if os.path.exists("gradio_cached_examples"):
        shutil.rmtree("gradio_cached_examples")
    app_interface.queue().launch()