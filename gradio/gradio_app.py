"""
Gradio frontend for the SecureMed Anamnesis workflow API.
This script creates a functional, mobile-first, step-by-step user interface 
that consumes the FastAPI endpoints to generate a medical summary.
It now supports both English and Portuguese, based on browser language.
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
SECUREMED_API_KEY = os.getenv("SECUREMED_API_KEY")
if not SECUREMED_API_KEY:
    raise ValueError("FATAL: SECUREMED_API_KEY environment variable not set. Aborting startup.")
HEADERS = {"X-API-KEY": SECUREMED_API_KEY}

# --- Internationalization (i18n) Setup ---
I18N_DICTIONARY = {
    "en": {
        "app_title_md": "<h1 class='app-title'>🩺 SecureMed Assistant</h1>",
        "app_subtitle_md": "<p class='app-subtitle'>Feeling ready for your doctor's visit is the first step to getting better care. We'll help you organize your thoughts, and never keep any information.</p>",
        "step1_markdown": "<h2 class='step-title'>Step 1 of 3: Your Concern</h2><p class='step-description'>First, please tell us a bit about yourself and what's bothering you.</p>",
        "main_concern_label": "What's your main health concern?", "main_concern_placeholder": "E.g., Severe headache for 2 days",
        "age_label": "Age", "gender_label": "Gender", "gender_male": "Male", "gender_female": "Female", "gender_other": "Other",
        "btn_next": "Next",
        "step2_markdown": "<h2 class='step-title'>Step 2 of 3: About Your Symptoms</h2><p class='step-description'>Please describe your symptoms based on the questions below.</p>",
        "your_answers_label": "Your Answers", "answers_placeholder": "Provide detailed answers here...",
        "btn_back": "Back", "btn_next_history": "Next: Medical History",
        "step3_markdown": "<h2 class='step-title'>Step 3 of 3: Medical History</h2><p class='step-description'>These final questions help provide a complete picture for your doctor.</p>",
        "medical_history_label": "Your Medical History", "btn_generate": "Generate Summary",
        "step4_markdown": "<h2>✅ Your Summary is Ready!</h2><p>Get the PDF below to share with your doctor.</p>",
        "btn_download": "⬇️ Download Health Summary", "btn_reset": "Start Over",
        "feedback_html": "<div class='feedback-link'>Help us improve! <a href='https://tally.so/r/wbaPvo' target='_blank' rel='noopener noreferrer'>Give Anonymous Feedback</a></div>",
        "pdf_filename": "Medical_Health_Summary.pdf",
        "status_loading": "*Loading questions...*",
        "error_all_fields_html": "<p class='status-error'>Please fill out all fields to continue.</p>",
        "error_fetch_questions_html": "<p class='status-error'>An error occurred while fetching questions. Please check your connection and try again.</p>",
        "error_provide_symptoms_html": "<p class='status-error'>Please provide answers about your symptoms before proceeding.</p>",
        "error_provide_history_html": "<p class='status-error'>Please answer the medical history questions to continue.</p>",
        "error_generate_summary_html": "<p class='status-error'>Sorry, we couldn't generate your summary due to a technical issue. Please try again.</p>",
    },
    "pt": {
        "app_title_md": "<h1 class='app-title'>🩺 Assistente SecureMed</h1>",
        "app_subtitle_md": "<p class='app-subtitle'>Ir para a consulta médica com tudo organizado é o primeiro passo para um melhor cuidado. Vamos te ajudar a organizar suas informações, e garantimos: nenhum dado seu é armazenado.</p>",
        "step1_markdown": "<h2 class='step-title'>Passo 1 de 3: Sua Queixa</h2><p class='step-description'>Primeiro, conte-nos um pouco sobre você e o que está te incomodando.</p>",
        "main_concern_label": "Qual é a sua principal queixa de saúde?", "main_concern_placeholder": "Ex: Forte dor de cabeça há 2 dias",
        "age_label": "Faixa Etária", "gender_label": "Gênero", "gender_male": "Masculino", "gender_female": "Feminino", "gender_other": "Outro",
        "btn_next": "Avançar",
        "step2_markdown": "<h2 class='step-title'>Passo 2 de 3: Sobre Seus Sintomas</h2><p class='step-description'>Por favor, descreva seus sintomas com base nas perguntas abaixo.</p>",
        "your_answers_label": "Suas Respostas", "answers_placeholder": "Forneça respostas detalhadas aqui...",
        "btn_back": "Voltar", "btn_next_history": "Avançar: Histórico Médico",
        "step3_markdown": "<h2 class='step-title'>Passo 3 de 3: Histórico Médico</h2><p class='step-description'>Estas perguntas finais ajudam a fornecer um quadro completo para o seu médico.</p>",
        "medical_history_label": "Seu Histórico Médico", "btn_generate": "Gerar Resumo",
        "step4_markdown": "<h2>✅ Seu Resumo está Pronto!</h2><p>Baixe o PDF abaixo para compartilhar com seu médico.</p>",
        "btn_download": "⬇️ Baixar Resumo de Saúde", "btn_reset": "Começar de Novo",
        "feedback_html": "<div class='feedback-link'>Ajude-nos a melhorar! <a href='https://tally.so/r/wbaPvo' target='_blank' rel='noopener noreferrer'>Deixar Feedback Anônimo</a></div>",
        "pdf_filename": "Resumo_de_Saude.pdf",
        "status_loading": "*Carregando perguntas...*",
        "error_all_fields_html": "<p class='status-error'>Por favor, preencha todos os campos para continuar.</p>",
        "error_fetch_questions_html": "<p class='status-error'>Ocorreu um erro ao buscar as perguntas. Por favor, verifique sua conexão e tente novamente.</p>",
        "error_provide_symptoms_html": "<p class='status-error'>Por favor, forneça respostas sobre seus sintomas antes de prosseguir.</p>",
        "error_provide_history_html": "<p class='status-error'>Por favor, responda às perguntas sobre seu histórico médico para continuar.</p>",
        "error_generate_summary_html": "<p class='status-error'>Desculpe, não foi possível gerar seu resumo devido a um problema técnico. Por favor, tente novamente.</p>",
    }
}
i18n = gr.I18n(**I18N_DICTIONARY)

# --- Enhanced CSS ---
PROFESSIONAL_CSS = """
.gradio-container { max-width: 650px !important; margin: auto !important; padding-top: 2rem; background-color: var(--background-fill-secondary) !important; }
.app-title { font-size: 2.2rem; font-weight: 700; text-align: center; color: var(--neutral-900); }
.app-subtitle { font-size: 1.1rem; color: var(--neutral-600); text-align: center; margin-bottom: 2.5rem; max-width: 500px; margin-left: auto; margin-right: auto; }
.step-container { padding: 2rem; margin: 1rem 0; border-radius: var(--radius-xl); box-shadow: var(--shadow-drop-lg); background-color: var(--background-fill-primary); border: 1px solid var(--border-color-primary); }
.step-title { font-size: 1.6rem; font-weight: 600; color: var(--primary-500); margin-bottom: 0.5rem; }
.step-description { font-size: 1rem; color: var(--neutral-700); margin-bottom: 1.5rem; }
.gr-button { padding: 0.9rem !important; font-size: 1rem !important; font-weight: 600 !important; border-radius: var(--radius-lg) !important; }
.download-container { text-align: center; padding: 2rem; }
.download-container h2 { font-size: 1.8rem; color: var(--primary-500); }
.feedback-link { margin-top: 2rem; font-size: 0.9rem; color: var(--neutral-500); }
.status-error { color: var(--color-accent-soft); font-weight: 500; margin-top: 1rem; text-align: center; background-color: var(--color-accent-soft-background); border: 1px solid var(--color-accent); padding: 10px; border-radius: var(--radius-lg); }
"""

# --- Helper Functions ---
def parse_age_bucket(age_bucket: str) -> int:
    if not age_bucket: return 0
    numbers = re.findall(r'\d+', age_bucket)
    return int(numbers[0]) if numbers else 0

async def process_streaming_response(response: httpx.Response) -> AsyncGenerator[str, None]:
    full_text = ""
    async for line in response.aiter_lines():
        if line.startswith("data:"):
            try:
                content = line[len("data:"):].strip()
                if content:
                    full_text += json.loads(content)
                    yield full_text
            except json.JSONDecodeError: continue

def get_lang_from_request(request: gr.Request) -> str:
    """Helper to determine language from request headers."""
    accept_language = request.headers.get('accept-language', '').lower()
    return 'pt' if accept_language.startswith('pt') else 'en'


# --- API Interaction and Interface Logic ---
async def handle_initial_questions(chief_complaint: str, age_bucket: str, gender: str, request: gr.Request) -> AsyncGenerator:
    if not all([chief_complaint, age_bucket, gender]):
        yield gr.update(), gr.update(visible=False), gr.HTML(i18n("error_all_fields_html")), ""
        return
    yield gr.update(visible=False), gr.update(visible=True), gr.HTML(), i18n("status_loading")
    age_int = parse_age_bucket(age_bucket)
    lang = get_lang_from_request(request)
    payload = {"chief_complaint": chief_complaint, "age": age_int, "gender": gender, "lang": lang}
    
    print(f"DEBUG: Attempting to call INITIAL_QUESTIONS_URL with payload: {json.dumps(payload)}")
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", INITIAL_QUESTIONS_URL, json=payload, headers=HEADERS, timeout=30.0) as response:
                response.raise_for_status()
                async for clean_chunk in process_streaming_response(response):
                    yield gr.update(visible=False), gr.update(visible=True), gr.HTML(), clean_chunk
    except httpx.HTTPStatusError as e:
        print(f"ERROR: HTTPStatusError from API: {e.response.status_code}")
        print(f"ERROR: API Response Body: {e.response.text}")
        yield gr.update(visible=True), gr.update(visible=False), gr.HTML(i18n("error_fetch_questions_html")), ""
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        yield gr.update(visible=True), gr.update(visible=False), gr.HTML(i18n("error_fetch_questions_html")), ""


async def handle_follow_up_questions(chief_complaint: str, age_bucket: str, gender: str, initial_answers: str, request: gr.Request) -> AsyncGenerator:
    if not initial_answers.strip():
        yield gr.update(), gr.update(visible=False), gr.HTML(i18n("error_provide_symptoms_html")), ""
        return
    yield gr.update(visible=False), gr.update(visible=True), gr.HTML(), i18n("status_loading")
    age_int = parse_age_bucket(age_bucket)
    lang = get_lang_from_request(request)
    payload = {"chief_complaint": chief_complaint, "age": age_int, "gender": gender, "initial_answers": initial_answers, "lang": lang}
    
    print(f"DEBUG: Attempting to call FOLLOW_UP_QUESTIONS_URL with payload: {json.dumps(payload)}")

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", FOLLOW_UP_QUESTIONS_URL, json=payload, headers=HEADERS, timeout=30.0) as response:
                response.raise_for_status()
                async for clean_chunk in process_streaming_response(response):
                     yield gr.update(visible=False), gr.update(visible=True), gr.HTML(), clean_chunk
    except httpx.HTTPStatusError as e:
        print(f"ERROR: HTTPStatusError from API: {e.response.status_code}")
        print(f"ERROR: API Response Body: {e.response.text}")
        yield gr.update(visible=True), gr.update(visible=False), gr.HTML(i18n("error_fetch_questions_html")), ""
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        yield gr.update(visible=True), gr.update(visible=False), gr.HTML(i18n("error_fetch_questions_html")), ""

async def handle_generate_pdf(chief_complaint: str, age_bucket: str, gender: str, initial_answers: str, follow_up_answers: str, request: gr.Request) -> AsyncGenerator:
    if not follow_up_answers.strip():
        yield gr.update(), gr.update(visible=False), gr.HTML(i18n("error_provide_history_html")), gr.DownloadButton(visible=False)
        return
    
    yield gr.update(visible=False), gr.update(visible=True), gr.HTML(), gr.DownloadButton(visible=False)

    age_int = parse_age_bucket(age_bucket)
    lang = get_lang_from_request(request)
    payload = {
        "chief_complaint": chief_complaint, "age": age_int, "gender": gender, 
        "initial_answers": initial_answers, "follow_up_answers": follow_up_answers, 
        "lang": lang
    }
    
    print(f"DEBUG: Attempting to call PDF_URL with payload: {json.dumps(payload)}")
    
    temp_dir = tempfile.mkdtemp()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(PDF_URL, json=payload, headers=HEADERS, timeout=60.0)
            response.raise_for_status()
            pdf_bytes = response.content
        
        pdf_filename = I18N_DICTIONARY[lang]["pdf_filename"]
        file_path = os.path.join(temp_dir, pdf_filename)
        
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
            
        yield gr.update(), gr.update(), gr.HTML(), gr.DownloadButton(value=file_path, visible=True)

    except httpx.HTTPStatusError as e:
        print(f"ERROR: HTTPStatusError from API: {e.response.status_code}")
        print(f"ERROR: API Response Body: {e.response.text}")
        yield gr.update(visible=True), gr.update(visible=False), gr.HTML(i18n("error_generate_summary_html")), gr.DownloadButton(visible=False)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred in PDF generation: {e}")
        yield gr.update(visible=True), gr.update(visible=False), gr.HTML(i18n("error_generate_summary_html")), gr.DownloadButton(visible=False)
    # NOTE: The finally block with shutil.rmtree(temp_dir) was removed
    # because it can create a race condition, deleting the temporary PDF 
    # before the user has a chance to click the download button. 
    # Gradio or the OS will handle the cleanup of this temporary file.

# --- UI Creation ---
def create_interface():
    theme = gr.themes.Soft(primary_hue=gr.themes.colors.blue, font=[gr.themes.GoogleFont("Roboto"), "ui-sans-serif", "system-ui", "sans-serif"])
    with gr.Blocks(title="SecureMed Assistant", theme=theme, css=PROFESSIONAL_CSS) as interface:
        state_complaint, state_age, state_gender, state_initial_answers = gr.State(), gr.State(), gr.State(), gr.State()
        gr.Markdown(i18n("app_title_md")); gr.Markdown(i18n("app_subtitle_md"))
        with gr.Group(visible=True) as step1:
            with gr.Column(elem_classes="step-container"):
                gr.Markdown(i18n("step1_markdown"))
                complaint_input = gr.Textbox(label=i18n("main_concern_label"), placeholder=i18n("main_concern_placeholder"))
                age_input = gr.Radio(label=i18n("age_label"), choices=["18-29", "30-44", "45-64", "65-79", "80+"])
                gender_input = gr.Radio(label=i18n("gender_label"), choices=["Male", "Female", "Other"])
                status_step1 = gr.HTML()
                next_btn_1 = gr.Button(i18n("btn_next"), variant="primary")
        with gr.Group(visible=False) as step2:
            with gr.Column(elem_classes="step-container"):
                gr.Markdown(i18n("step2_markdown"))
                initial_questions_display = gr.Markdown()
                initial_answers_input = gr.Textbox(label=i18n("your_answers_label"), lines=8, placeholder=i18n("answers_placeholder"))
                status_step2 = gr.HTML()
                with gr.Row():
                    back_btn_2 = gr.Button(i18n("btn_back"))
                    next_btn_2 = gr.Button(i18n("btn_next_history"), variant="primary")
        with gr.Group(visible=False) as step3:
            with gr.Column(elem_classes="step-container"):
                gr.Markdown(i18n("step3_markdown"))
                follow_up_questions_display = gr.Markdown()
                follow_up_answers_input = gr.Textbox(label=i18n("medical_history_label"), lines=8, placeholder=i18n("answers_placeholder"))
                status_step3 = gr.HTML()
                with gr.Row():
                    back_btn_3 = gr.Button(i18n("btn_back"))
                    next_btn_3 = gr.Button(i18n("btn_generate"), variant="primary")
        with gr.Group(visible=False) as step4:
            with gr.Column(elem_classes="step-container download-container"):
                gr.Markdown(i18n("step4_markdown"))
                pdf_download_button = gr.DownloadButton(i18n("btn_download"), variant="primary", visible=False)
                reset_btn = gr.Button(i18n("btn_reset"))
                gr.HTML(i18n("feedback_html"))

        def localize_gender_choices(request: gr.Request):
            lang = get_lang_from_request(request)
            gender_choices = [(I18N_DICTIONARY[lang]["gender_male"], "Male"), (I18N_DICTIONARY[lang]["gender_female"], "Female"), (I18N_DICTIONARY[lang]["gender_other"], "Other")]
            return gr.update(choices=gender_choices)
        
        interface.load(fn=localize_gender_choices, inputs=None, outputs=[gender_input])
        
        next_btn_1.click(
            lambda c, a, g: (c, a, g), 
            [complaint_input, age_input, gender_input], 
            [state_complaint, state_age, state_gender]
        ).then(
            handle_initial_questions, 
            [state_complaint, state_age, state_gender], 
            [step1, step2, status_step1, initial_questions_display]
        )
        
        next_btn_2.click(
            lambda ans: ans, 
            [initial_answers_input], 
            [state_initial_answers]
        ).then(
            handle_follow_up_questions, 
            [state_complaint, state_age, state_gender, state_initial_answers], 
            [step2, step3, status_step2, follow_up_questions_display]
        )
        
        next_btn_3.click(
            handle_generate_pdf, 
            [state_complaint, state_age, state_gender, state_initial_answers, follow_up_answers_input], 
            [step3, step4, status_step3, pdf_download_button]
        )
        
        back_btn_2.click(lambda: (gr.update(visible=True), gr.update(visible=False)), None, [step1, step2])
        back_btn_3.click(lambda: (gr.update(visible=True), gr.update(visible=False)), None, [step2, step3])
        
        all_steps = [step1, step2, step3, step4]
        all_inputs = [complaint_input, age_input, gender_input, initial_answers_input, follow_up_answers_input]
        all_outputs = [status_step1, status_step2, status_step3, initial_questions_display, follow_up_questions_display, pdf_download_button]
        
        reset_btn.click(
            lambda: (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), "", None, None, "", "", gr.HTML(), gr.HTML(), gr.HTML(), "", "", gr.DownloadButton(visible=False)), 
            outputs=all_steps + all_inputs + all_outputs
        )
        
    return interface

if __name__ == "__main__":
    app_interface = create_interface()
    if os.path.exists("gradio_cached_examples"): 
        shutil.rmtree("gradio_cached_examples")
    app_interface.queue().launch(i18n=i18n)
