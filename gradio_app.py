"""
Frontend Gradio para a API SecureMed com fluxo de Anamnese.
Este script cria uma interface de usuário passo a passo que consome
os endpoints da API FastAPI para gerar um relatório médico.
"""
import gradio as gr
import os
import httpx
import tempfile
from typing import List, Tuple
from dotenv import load_dotenv

# --- Configuração Inicial ---
load_dotenv()

# Obter URLs da API a partir do arquivo .env
QUESTIONS_URL = os.getenv("GENERATE_QUESTIONS_URL")
PDF_URL = os.getenv("CREATE_PDF_URL")

if not QUESTIONS_URL or not PDF_URL:
    raise ValueError("As URLs da API (GENERATE_QUESTIONS_URL, CREATE_PDF_URL) não foram definidas no arquivo .env.")

# Estilo visual da interface
BEAUTIFUL_CSS = """
/* Seu CSS original aqui... (versão compacta) */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root { --primary-dark: #005f73; --secondary-dark: #0a9396; --background-light: #ffffff; --border-light: #e9ecef; --text-primary: #212529; --border-radius: 8px; }
.gradio-container { max-width: 900px !important; margin: 0 auto !important; font-family: 'Inter', sans-serif !important; }
.hero-section { text-align: center; padding: 40px 20px; } .hero-title { font-size: 2rem !important; font-weight: 700 !important; color: var(--primary-dark) !important; margin-bottom: 12px !important; } .hero-subtitle { font-size: 1.1rem !important; color: #495057; }
.step-container { border: 1px solid var(--border-light); border-radius: var(--border-radius); padding: 32px; margin: 24px 0; }
.step-header { display: flex; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border-light); }
.step-number { background: var(--primary-dark); color: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin-right: 16px; font-weight: 600; }
.step-title { font-size: 1.25rem !important; font-weight: 600 !important; color: var(--text-primary) !important; }
.status-error { color: #d00000; background-color: #fff0f0; padding: 10px; border-radius: 5px; margin-top: 10px; }
.status-success { color: #007f5f; background-color: #f0fff0; padding: 15px; border-radius: 5px; text-align: center; }
.btn-primary { background: var(--primary-dark) !important; color: white !important; }
"""

# --- Funções de Lógica da Interface ---

async def handle_generate_questions(chief_complaint: str) -> Tuple[gr.update, gr.update, gr.update, gr.update, str]:
    """Chama a API para gerar perguntas com base na queixa principal."""
    if not chief_complaint.strip():
        return gr.update(), gr.update(), gr.update(), gr.HTML("<p class='status-error'>Por favor, insira uma queixa principal.</p>"), ""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(QUESTIONS_URL, json={"chief_complaint": chief_complaint}, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            questions = data.get("questions", [])

        # Formata as perguntas como uma lista Markdown
        questions_markdown = "### Perguntas Geradas\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))

        return (
            gr.update(visible=False),  # Esconde o Passo 1
            gr.update(visible=True),   # Mostra o Passo 2
            gr.update(visible=False),  # Mantém o Passo 3 escondido
            gr.HTML(""),               # Limpa status de erro
            questions_markdown         # Insere as perguntas
        )
    except httpx.RequestError as e:
        error_html = f"<p class='status-error'>Erro de conexão com a API: {e}</p>"
        return gr.update(), gr.update(), gr.update(), gr.HTML(error_html), ""
    except Exception as e:
        error_html = f"<p class='status-error'>Ocorreu um erro: {e}</p>"
        return gr.update(), gr.update(), gr.update(), gr.HTML(error_html), ""


async def handle_generate_pdf(chief_complaint: str, patient_answers: str) -> Tuple[gr.update, gr.update, gr.update, gr.update, str]:
    """Envia as respostas para a API e obtém o relatório em PDF."""
    if not patient_answers.strip():
        status_html = "<p class='status-error'>Por favor, forneça as respostas às perguntas.</p>"
        return gr.update(), gr.update(), gr.update(), gr.HTML(status_html), None

    try:
        payload = {"chief_complaint": chief_complaint, "patient_answers": patient_answers}
        async with httpx.AsyncClient() as client:
            response = await client.post(PDF_URL, json=payload, timeout=60.0)
            response.raise_for_status()

            # Salva o conteúdo do PDF em um arquivo temporário
            pdf_bytes = await response.aread()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_bytes)
                temp_pdf_path = tmp.name

        success_html = "<div class='status-success'><h3>✅ Relatório Gerado com Sucesso!</h3><p>Clique no arquivo abaixo para fazer o download.</p></div>"

        return (
            gr.update(visible=False), # Esconde Passo 2
            gr.update(visible=True),  # Mostra Passo 3
            gr.HTML(success_html),    # Mostra mensagem de sucesso
            gr.update(value=temp_pdf_path, visible=True), # Mostra o arquivo PDF
            gr.update(visible=True)   # Mostra o botão de reiniciar
        )
    except Exception as e:
        error_html = f"<p class='status-error'>Falha ao gerar o PDF: {e}</p>"
        return gr.update(), gr.update(), gr.update(), gr.HTML(error_html), None


def reset_interface():
    """Reinicia a interface para o estado inicial."""
    return (
        gr.update(visible=True, value=""),  # Mostra Passo 1 e limpa
        gr.update(visible=False, value=""), # Esconde Passo 2 e limpa
        gr.update(visible=False),           # Esconde Passo 3
        gr.HTML(""),                        # Limpa status
        gr.Markdown(""),                    # Limpa perguntas
        gr.File(value=None, visible=False), # Limpa e esconde arquivo
        gr.Button(visible=False)            # Esconde botão de reiniciar
    )


# --- Construção da Interface Gradio ---
def create_interface():
    with gr.Blocks(title="SecureMed Anamnesis", theme=gr.themes.Soft(), css=BEAUTIFUL_CSS) as interface:

        # Estado invisível para armazenar a queixa principal entre os passos
        state_chief_complaint = gr.State("")

        # Cabeçalho
        gr.HTML("""
        <div class="hero-section">
            <h1 class="hero-title">🩺 Assistente de Anamnese SecureMed</h1>
            <p class="hero-subtitle">Um assistente inteligente para ajudar a estruturar as informações do paciente antes da consulta.</p>
        </div>
        """)

        # Passo 1: Inserir Queixa Principal
        with gr.Group(visible=True) as step1_complaint:
            gr.HTML("""
            <div class="step-container"><div class="step-header"><div class="step-number">1</div>
            <div class="step-title">Qual é a queixa principal do paciente?</div></div></div>
            """)
            complaint_input = gr.Textbox(label="Queixa Principal", placeholder="Ex: Dor de cabeça forte há 2 dias")
            generate_questions_btn = gr.Button("Gerar Perguntas", variant="primary")
            status_step1 = gr.HTML()

        # Passo 2: Responder Perguntas
        with gr.Group(visible=False) as step2_questions:
            gr.HTML("""
            <div class="step-container"><div class="step-header"><div class="step-number">2</div>
            <div class="step-title">Responda às perguntas abaixo</div></div></div>
            """)
            questions_display = gr.Markdown()
            answers_input = gr.Textbox(label="Respostas do Paciente", lines=10, placeholder="Responda às perguntas acima de forma descritiva neste campo...")
            generate_pdf_btn = gr.Button("Gerar Relatório PDF", variant="primary")
            status_step2 = gr.HTML()

        # Passo 3: Baixar Relatório
        with gr.Group(visible=False) as step3_report:
            gr.HTML("""
            <div class="step-container"><div class="step-header"><div class="step-number">3</div>
            <div class="step-title">Download do Relatório</div></div></div>
            """)
            status_step3 = gr.HTML()
            pdf_output = gr.File(label="Seu relatório está pronto", visible=False)
            reset_btn = gr.Button("Iniciar Nova Consulta", visible=False)

        # --- Lógica de Eventos ---

        # Botão "Gerar Perguntas"
        generate_questions_btn.click(
            fn=handle_generate_questions,
            inputs=[complaint_input],
            outputs=[step1_complaint, step2_questions, step3_report, status_step1, questions_display]
        ).then(lambda x: x, complaint_input, state_chief_complaint) # Salva a queixa no estado

        # Botão "Gerar Relatório PDF"
        generate_pdf_btn.click(
            fn=handle_generate_pdf,
            inputs=[state_chief_complaint, answers_input],
            outputs=[step2_questions, step3_report, status_step3, pdf_output, reset_btn]
        )

        # Botão "Iniciar Nova Consulta"
        reset_btn.click(
            fn=reset_interface,
            outputs=[complaint_input, answers_input, step3_report, status_step1, questions_display, pdf_output, reset_btn]
        ).then(lambda: (gr.update(visible=True), gr.update(visible=False)), outputs=[step1_complaint, step2_questions])


    return interface

if __name__ == "__main__":
    app_interface = create_interface()
    app_interface.launch(server_name="0.0.0.0", server_port=7865)
