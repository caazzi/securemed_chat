"""
PDF Generation Service.
"""
import io
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

def generate_pdf_report_in_memory(data: dict) -> bytes:
    """
    REVISED: Generates a PDF from a structured dictionary, using empathetic labels and improved layout.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    styles = getSampleStyleSheet()

    # --- Header ---
    c.setFont("Helvetica", 9)
    c.drawRightString(width - inch, height - 0.9*inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(inch, height - 0.9*inch, "Disclaimer: For informational purposes only. Not medical advice.")

    # --- Title ---
    c.setFont("Helvetica-Bold", 18)
    c.drawString(inch, height - 1.2*inch, "Your Health Summary")
    c.line(inch, height - 1.3*inch, width - inch, height - 1.3*inch)

    y_pos = height - 1.8*inch

    # --- Helper to draw a labeled section ---
    def draw_labeled_section(y_start, label, text):
        style_body = styles['BodyText']
        style_body.fontName = 'Helvetica'
        style_body.fontSize = 12
        style_body.leading = 16

        # Combine label (bold) and text into a single paragraph
        full_text = f"<b>{label}:</b> {text}"
        p = Paragraph(full_text, style_body)

        p_width, p_height = p.wrapOn(c, width - 2 * inch, height)
        p.drawOn(c, inch, y_start - p_height)

        # Return height of this section plus padding for the next one
        return p_height + (0.35 * inch)

    # --- Main Content - Rendered from structured data ---

    # 1. Chief Complaint
    y_pos -= draw_labeled_section(y_pos, "My Main Health Concern", data.get("chief_complaint", "N/A"))

    # 2. History of Present Illness (with empathetic labels)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y_pos, "About My Current Symptoms")
    y_pos -= 0.4 * inch

    y_pos -= draw_labeled_section(y_pos, "When it started", data.get("onset", "Not mentioned"))
    y_pos -= draw_labeled_section(y_pos, "How it feels", data.get("character", "Not mentioned"))
    y_pos -= draw_labeled_section(y_pos, "Other related symptoms", data.get("associated_symptoms", "Not mentioned"))

    y_pos -= 0.2 * inch # Extra padding between major sections

    # 3. Medical History (with empathetic labels)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y_pos, "My Overall Health History")
    y_pos -= 0.4 * inch

    y_pos -= draw_labeled_section(y_pos, "Past conditions or surgeries", data.get("past_medical_history", "Not mentioned"))
    y_pos -= draw_labeled_section(y_pos, "Family health conditions", data.get("family_history", "Not mentioned"))
    y_pos -= draw_labeled_section(y_pos, "Current medications & allergies", data.get("medications", "Not mentioned"))

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    print("📄 Structured PDF report successfully generated in-memory.")
    return pdf_bytes
