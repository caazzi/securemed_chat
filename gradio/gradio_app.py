"""
Gradio frontend for the SecureMed Anamnesis workflow API.
This script creates a trust-focused, step-by-step user interface that
consumes the FastAPI endpoints to generate a medical report.
"""
import gradio as gr
import os
import httpx
import tempfile
from typing import Tuple, Optional
from dotenv import load_dotenv
from datetime import datetime

# --- Initial Setup ---
load_dotenv()

# Get API URLs from the .env or .envrc file
INITIAL_QUESTIONS_URL = os.getenv("INITIAL_QUESTIONS_URL")
FOLLOW_UP_QUESTIONS_URL = os.getenv("FOLLOW_UP_QUESTIONS_URL")
PDF_URL = os.getenv("PDF_URL")

if not all([INITIAL_QUESTIONS_URL, FOLLOW_UP_QUESTIONS_URL, PDF_URL]):
    raise ValueError("The API URLs were not correctly defined in the .env or .envrc file.")

# --- UI Styling (Heavily Revised for Trust and Clarity) ---
ENHANCED_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --primary-color: #005f73;
    --secondary-color: #0a9396;
    --accent-color: #94d2bd;
    --background-light: #f8f9fa;
    --text-primary: #212529;
    --text-secondary: #495057;
    --border-color: #dee2e6;
    --border-radius: 12px;
    --shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.gradio-container {
    max-width: 800px !important;
    margin: 0 auto !important;
    font-family: 'Inter', sans-serif !important;
    background-color: var(--background-light);
}

/* Header Section */
.hero-section { text-align: center; padding: 40px 20px; border-bottom: 1px solid var(--border-color); }
.app-logo { font-size: 2.5rem; margin-bottom: 8px; }
.hero-title { font-size: 2.25rem !important; font-weight: 700 !important; color: var(--primary-color) !important; margin-bottom: 12px !important; }
.hero-subtitle { font-size: 1.1rem !important; color: var(--text-secondary); max-width: 600px; margin: 0 auto; }
.disclaimer { display: inline-flex; align-items: center; gap: 8px; font-size: 0.9rem; color: var(--text-secondary); margin-top: 24px; border: 1px solid var(--border-color); padding: 12px 18px; border-radius: 100px; background-color: #ffffff;}

/* Progress Bar */
.progress-bar { display: flex; justify-content: space-between; padding: 20px; }
.progress-step { display: flex; align-items: center; gap: 8px; color: var(--border-color); font-weight: 500; }
.progress-step.active { color: var(--primary-color); }
.progress-step .step-circle { width: 30px; height: 30px; border-radius: 50%; border: 2px solid var(--border-color); display: grid; place-items: center; font-size: 0.9rem; }
.progress-step.active .step-circle { border-color: var(--primary-color); background-color: var(--primary-color); color: white; }

/* Step Container */
.step-container { border: none; border-radius: var(--border-radius); padding: 32px; margin: 24px; background-color: #ffffff; box-shadow: var(--shadow); }
.step-header { margin-bottom: 24px; }
.step-title { font-size: 1.5rem !important; font-weight: 600 !important; color: var(--text-primary) !important; }
.step-description { font-size: 1rem; color: var(--text-secondary); margin-top: 4px; }

/* Form Elements & Buttons */
.button-row { display: flex; justify-content: space-between; margin-top: 24px; }
.gr-button { font-weight: 600 !important; }
.btn-secondary { background: var(--background-light) !important; color: var(--text-primary) !important; border: 1px solid var(--border-color) !important; }

/* Final Download Screen */
.download-container { text-align: center; padding: 40px; }
.download-icon { font-size: 3rem; color: #28a745; margin-bottom: 16px; } /* Changed color to green */
.next-steps { text-align: left; background-color: var(--background-light); padding: 16px; border-radius: var(--border-radius); margin-top: 24px; }

/* Custom File Download Link */
.file-download-box {
    border: 1px solid var(--border-color);
    padding: 12px 18px;
    border-radius: var(--border-radius);
    background-color: var(--background-light);
    text-align: left;
    overflow: hidden; /* Clear the float */
    margin-top: 16px;
}
.file-download-box a {
    color: var(--primary-color);
    font-weight: 500;
    text-decoration: none;
}
.file-download-box a:hover {
    text-decoration: underline;
}
.file-size-info {
    float: right;
    color: var(--text-secondary);
}
"""

# --- Progress Bar Helper ---
PROGRESS_BAR_BASE_HTML = """
<div class="progress-bar">
    <div class="progress-step {s1_active}"><div class="step-circle">1</div> Information</div>
    <div class="progress-step {s2_active}"><div class="step-circle">2</div> Questions</div>
    <div class="progress-step {s3_active}"><div class="step-circle">3</div> History</div>
    <div class="progress-step {s4_active}"><div class="step-circle">4</div> Report</div>
</div>
"""

def create_progress_html(active_step: int) -> str:
    """Generates the HTML for the progress bar based on the current step."""
    return PROGRESS_BAR_BASE_HTML.format(
        s1_active="active" if active_step >= 1 else "",
        s2_active="active" if active_step >= 2 else "",
        s3_active="active" if active_step >= 3 else "",
        s4_active="active" if active_step >= 4 else ""
    )

# --- Interface Logic Functions ---
async def handle_initial_questions(chief_complaint: str, age: int, gender: str) -> Tuple:
    if not all([chief_complaint, age, gender]):
        error_msg = "<p class='status-error'>Please fill out all fields: concern, age, and gender.</p>"
        return gr.update(), gr.update(), gr.HTML(error_msg), "", gr.update(visible=False)
    payload = {"chief_complaint": chief_complaint, "age": int(age), "gender": gender}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(INITIAL_QUESTIONS_URL, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        questions = "### Initial Questions\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(data.get("questions", [])))
        progress_html = create_progress_html(2)
        return gr.update(visible=False), gr.update(visible=True), gr.HTML(), questions, gr.update(value=progress_html, visible=True)
    except Exception as e:
        error_html = f"<p class='status-error'>API error: {e}</p>"
        return gr.update(), gr.update(), gr.HTML(error_html), "", gr.update(visible=False)

async def handle_follow_up_questions(chief_complaint: str, age: int, gender: str, initial_answers: str) -> Tuple:
    if not initial_answers.strip():
        return gr.update(), gr.update(), gr.HTML("<p class='status-error'>Please answer the initial questions.</p>"), "", gr.update()
    payload = {"chief_complaint": chief_complaint, "age": int(age), "gender": gender, "initial_answers": initial_answers}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(FOLLOW_UP_QUESTIONS_URL, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        questions = "### Additional Questions (Medical History)\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(data.get("questions", [])))
        progress_html = create_progress_html(3)
        return gr.update(visible=False), gr.update(visible=True), gr.HTML(), questions, gr.update(value=progress_html, visible=True)
    except Exception as e:
        error_html = f"<p class='status-error'>API error: {e}</p>"
        return gr.update(), gr.update(), gr.HTML(error_html), "", gr.update()

async def handle_generate_pdf(chief_complaint: str, age: int, gender: str, initial_answers: str, follow_up_answers: str) -> Tuple:
    if not follow_up_answers.strip():
        return gr.update(), gr.update(), gr.HTML("<p class='status-error'>Please answer the history questions.</p>"), None, None, gr.update()
    payload = {"chief_complaint": chief_complaint, "age": int(age), "gender": gender, "initial_answers": initial_answers, "follow_up_answers": follow_up_answers}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(PDF_URL, json=payload, timeout=60.0)
            response.raise_for_status()

        # Create a timestamped filename and save the PDF to a temporary path
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        file_name = f"Medical_Summary_Report_{timestamp}.pdf"
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, file_name)

        with open(pdf_path, "wb") as f:
            f.write(await response.aread())

        progress_html = create_progress_html(4)

        # --- MODIFICATION START ---
        # Construct custom HTML for the download link instead of using the default gr.File display
        file_size_kb = os.path.getsize(pdf_path) / 1024
        download_html = f"""
        <div class="file-download-box">
            <a href="/file={pdf_path}" download="{file_name}">📄 {file_name}</a>
            <span class="file-size-info">{file_size_kb:.1f} KB</span>
        </div>
        """
        # Return path to hidden file handler and HTML to the display component
        return gr.update(visible=False), gr.update(visible=True), gr.HTML(), pdf_path, download_html, gr.update(value=progress_html, visible=True)
        # --- MODIFICATION END ---

    except Exception as e:
        error_html = f"<p class='status-error'>Failed to generate PDF: {e}</p>"
        # Ensure the correct number of values are returned on error
        return gr.update(), gr.update(), gr.HTML(error_html), None, None, gr.update()

# --- UI Navigation Functions ---
def go_to_step(step_num: int):
    """Updates visibility of step containers and the progress bar."""
    all_steps = 4
    step_visibility = [gr.update(visible=False)] * all_steps
    step_visibility[step_num - 1] = gr.update(visible=True)

    progress_update = gr.update(visible=False)
    # Don't show progress bar on step 1
    if step_num > 1:
        progress_update = gr.update(value=create_progress_html(step_num), visible=True)
    else: # Explicitly hide for step 1
        progress_update = gr.update(visible=False)

    return tuple(step_visibility) + (progress_update,)

def full_reset():
    """Resets the entire interface to its initial state."""
    updates = go_to_step(1)
    # Also clear all input fields
    return updates + (
        "", gr.update(value=None), gr.update(value=None), # Step 1 inputs
        "", # Step 2 input
        ""  # Step 3 input
    )


# --- Gradio Interface Construction ---
def create_interface():
    with gr.Blocks(title="SecureMed Assistant", theme=gr.themes.Soft(), css=ENHANCED_CSS) as interface:
        # State variables to hold data between steps
        state_complaint = gr.State("")
        state_age = gr.State()
        state_gender = gr.State("")
        state_initial_answers = gr.State("")

        # Header
        gr.HTML("""
        <div class="hero-section">
            <div class="app-logo">🩺</div>
            <h1 class="hero-title">SecureMed Assistant</h1>
            <p class="hero-subtitle">Prepare for your doctor's visit by organizing your symptoms and medical history. Get a structured report to share.</p>
            <div class="disclaimer">🛡️ <strong>Privacy First:</strong> Your information is processed in memory and never stored.</div>
        </div>
        """)

        # A single, dynamic progress bar component, initially hidden
        progress_bar = gr.HTML(visible=False)

        # Step 1: Patient Information
        with gr.Group(visible=True) as step1:
            with gr.Column(elem_classes="step-container"):
                gr.HTML("""
                <div class="step-header">
                    <h2 class="step-title">Let's Get Started</h2>
                    <p class="step-description">Please provide some basic details about your primary health concern.</p>
                </div>
                """)
                complaint_input = gr.Textbox(label="What is your primary health concern?", placeholder="E.g., Severe headache for 2 days")
                with gr.Row():
                    age_input = gr.Number(label="Age", minimum=0, maximum=120, step=1)
                    gender_input = gr.Radio(label="Gender", choices=["Male", "Female", "Other"])
                status_step1 = gr.HTML()
                with gr.Row(elem_classes="button-row"):
                    next_btn_1 = gr.Button("Next", variant="primary")

        # Step 2: Answer Initial Questions
        with gr.Group(visible=False) as step2:
            with gr.Column(elem_classes="step-container"):
                gr.HTML('<div class="step-header"><h2 class="step-title">Answering Key Questions</h2><p class="step-description">Please describe your symptoms based on the questions below.</p></div>')
                initial_questions_display = gr.Markdown()
                initial_answers_input = gr.Textbox(label="Your Answers", lines=10, placeholder="Provide detailed answers here...")
                status_step2 = gr.HTML()
                with gr.Row(elem_classes="button-row"):
                    back_btn_2 = gr.Button("Back", elem_classes="btn-secondary")
                    next_btn_2 = gr.Button("Next: Medical History", variant="primary")

        # Step 3: Answer History Questions
        with gr.Group(visible=False) as step3:
            with gr.Column(elem_classes="step-container"):
                gr.HTML('<div class="step-header"><h2 class="step-title">Medical History</h2><p class="step-description">These final questions help provide a complete picture for your doctor.</p></div>')
                follow_up_questions_display = gr.Markdown()
                follow_up_answers_input = gr.Textbox(label="Your Answers About Your History", lines=10, placeholder="Provide detailed answers here...")
                status_step3 = gr.HTML()
                with gr.Row(elem_classes="button-row"):
                    back_btn_3 = gr.Button("Back", elem_classes="btn-secondary")
                    next_btn_3 = gr.Button("Generate Report", variant="primary")

        # Step 4: Download Report
        with gr.Group(visible=False) as step4:
            with gr.Column(elem_classes="step-container download-container"):
                gr.HTML('<div class="download-icon">✅</div><h2 class="step-title">Your Report is Ready!</h2><p class="step-description">Download the PDF below. This structured summary will help you have a more effective conversation with your doctor.</p>')

                # --- MODIFICATION START ---
                # Use a hidden gr.File to handle serving the file and a gr.HTML to display our custom link.
                pdf_file_handler = gr.File(visible=False)
                pdf_download_display = gr.HTML(label="Download Your SecureMed Report")
                # --- MODIFICATION END ---

                gr.HTML('<div class="next-steps"><strong>Next Steps:</strong><br>1. Save the PDF to your phone or computer.<br>2. Share it with your doctor during your visit.</div>')
                reset_btn = gr.Button("Start a New Report", variant="primary", elem_classes="button-row")

        # --- Event Logic ---
        all_steps = [step1, step2, step3, step4]
        all_inputs = [complaint_input, age_input, gender_input, initial_answers_input, follow_up_answers_input]

        # Step 1 -> 2
        next_btn_1.click(
            handle_initial_questions,
            inputs=[complaint_input, age_input, gender_input],
            outputs=[step1, step2, status_step1, initial_questions_display, progress_bar]
        ).then(
            lambda x, y, z: (x, y, z),
            inputs=[complaint_input, age_input, gender_input],
            outputs=[state_complaint, state_age, state_gender]
        )

        # Step 2 -> 3
        next_btn_2.click(
            handle_follow_up_questions,
            inputs=[state_complaint, state_age, state_gender, initial_answers_input],
            outputs=[step2, step3, status_step2, follow_up_questions_display, progress_bar]
        ).then(
            lambda x: x,
            inputs=initial_answers_input,
            outputs=state_initial_answers
        )

        # Step 2 -> 1 (Back)
        back_btn_2.click(lambda: go_to_step(1), None, all_steps + [progress_bar])

        # Step 3 -> 4
        # --- MODIFICATION START ---
        # Update the outputs to match the new components for the PDF download
        next_btn_3.click(
            handle_generate_pdf,
            inputs=[state_complaint, state_age, state_gender, state_initial_answers, follow_up_answers_input],
            outputs=[step3, step4, status_step3, pdf_file_handler, pdf_download_display, progress_bar]
        )
        # --- MODIFICATION END ---


        # Step 3 -> 2 (Back)
        back_btn_3.click(lambda: go_to_step(2), None, all_steps + [progress_bar])

        # Reset after finish
        reset_btn.click(lambda: full_reset(), None, all_steps + [progress_bar] + all_inputs)

    return interface

if __name__ == "__main__":
    app_interface = create_interface()
    app_interface.launch(server_name="0.0.0.0", server_port=7865, share=True)
