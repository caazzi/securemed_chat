"""
PDF Generation Service.
Generates PDF reports in memory with internationalization (i18n) support
for labels in English and Portuguese.
"""
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

# --- Translation Dictionary (i18n) ---
translations = {
    "pt": {
        "generated_on": "Gerado em",
        "disclaimer": "Aviso: Apenas para fins informativos. Não é um conselho médico.",
        "title": "Seu Resumo de Saúde",
        "main_concern": "Minha Principal Queixa de Saúde",
        "about_symptoms": "Sobre Meus Sintomas Atuais",
        "onset": "Quando começou",
        "character": "Como é a sensação",
        "associated_symptoms": "Outros sintomas relacionados",
        "health_history": "Meu Histórico de Saúde Geral",
        "past_history": "Condições ou cirurgias passadas",
        "family_history": "Condições de saúde na família",
        "medications": "Medicamentos e alergias atuais",
        "not_mentioned": "Não mencionado",
        "filename": "Resumo_Medico.pdf"
    },
    "en": {
        "generated_on": "Generated on",
        "disclaimer": "Disclaimer: For informational purposes only. Not medical advice.",
        "title": "Your Health Summary",
        "main_concern": "My Main Health Concern",
        "about_symptoms": "About My Current Symptoms",
        "onset": "When it started",
        "character": "How it feels",
        "associated_symptoms": "Other related symptoms",
        "health_history": "My Overall Health History",
        "past_history": "Past conditions or surgeries",
        "family_history": "Family health conditions",
        "medications": "Current medications & allergies",
        "not_mentioned": "Not mentioned",
        "filename": "Medical_Summary_Report.pdf"
    }
}

def generate_pdf_report_in_memory(data: dict, lang: str = 'en') -> tuple[bytes, str]:
    """
    Generates a PDF from a structured dictionary, supporting multiple languages.

    Args:
        data (dict): The structured data from the LLM.
        lang (str): The language code ('pt' or 'en') for the report labels.

    Returns:
        tuple[bytes, str]: A tuple containing the PDF bytes and the recommended filename.
    """
    # Select the correct labels, defaulting to English if lang is invalid
    labels = translations.get(lang, translations['en'])
    not_mentioned_text = labels.get("not_mentioned", "N/A")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    styles = getSampleStyleSheet()

    # --- Header ---
    c.setFont("Helvetica", 9)
    c.drawRightString(width - inch, height - 0.9*inch, f"{labels['generated_on']}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(inch, height - 0.9*inch, labels['disclaimer'])

    # --- Title ---
    c.setFont("Helvetica-Bold", 18)
    c.drawString(inch, height - 1.2*inch, labels['title'])
    c.line(inch, height - 1.3*inch, width - inch, height - 1.3*inch)

    y_pos = height - 1.8*inch

    # --- Helper to draw a labeled section ---
    def draw_labeled_section(y_start, label, text):
        style_body = styles['BodyText']
        style_body.fontName = 'Helvetica'
        style_body.fontSize = 12
        style_body.leading = 16

        full_text = f"<b>{label}:</b> {text}"
        p = Paragraph(full_text, style_body)

        p_width, p_height = p.wrapOn(c, width - 2 * inch, height)
        p.drawOn(c, inch, y_start - p_height)

        return p_height + (0.35 * inch)

    # --- Main Content - Rendered from structured data ---

    # 1. Chief Complaint
    y_pos -= draw_labeled_section(y_pos, labels['main_concern'], data.get("chief_complaint", not_mentioned_text))

    # 2. History of Present Illness
    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y_pos, labels['about_symptoms'])
    y_pos -= 0.4 * inch

    y_pos -= draw_labeled_section(y_pos, labels['onset'], data.get("onset", not_mentioned_text))
    y_pos -= draw_labeled_section(y_pos, labels['character'], data.get("character", not_mentioned_text))
    y_pos -= draw_labeled_section(y_pos, labels['associated_symptoms'], data.get("associated_symptoms", not_mentioned_text))

    y_pos -= 0.2 * inch # Extra padding

    # 3. Medical History
    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y_pos, labels['health_history'])
    y_pos -= 0.4 * inch

    y_pos -= draw_labeled_section(y_pos, labels['past_history'], data.get("past_medical_history", not_mentioned_text))
    y_pos -= draw_labeled_section(y_pos, labels['family_history'], data.get("family_history", not_mentioned_text))
    y_pos -= draw_labeled_section(y_pos, labels['medications'], data.get("medications", not_mentioned_text))

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    print(f"📄 Structured PDF report (lang={lang}) successfully generated in-memory.")
    return pdf_bytes, labels['filename']
