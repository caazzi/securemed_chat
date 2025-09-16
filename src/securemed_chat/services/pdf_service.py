"""
PDF Generation Service.
"""
from datetime import datetime
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

# Correct, absolute import
from securemed_chat.core.config import PDF_REPORTS_DIR

def generate_pdf_report(data: dict) -> Path:
    """
    Generates a medical summary PDF report from the final structured data.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    file_name = f"Medical_Summary_Report_{timestamp}.pdf"
    pdf_path = PDF_REPORTS_DIR / file_name

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter
    styles = getSampleStyleSheet()

    # --- Header ---
    c.setFont("Helvetica", 9)
    c.drawRightString(width - inch, height - 0.9*inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(inch, height - 0.9 * inch, "Disclaimer: For informational purposes only. Not medical advice.")

    # --- Title ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, height - 1.2*inch, "Pre-Visit Medical Summary")
    c.line(inch, height - 1.3*inch, width - inch, height - 1.3*inch)

    # --- Content ---
    y_pos = height - 1.7*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_pos, "Chief Complaint:")
    c.setFont("Helvetica", 11)
    c.drawString(inch * 2.5, y_pos, data.get("chief_complaint", "N/A"))

    y_pos -= 0.5 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_pos, "History of Present Illness & Medical History:")

    style_body = styles['BodyText']
    style_body.fontName = 'Helvetica'
    style_body.fontSize = 11
    style_body.leading = 15

    history_text = f"""
    <b>Onset:</b> {data.get('onset', 'N/A')}<br/>
    <b>Character:</b> {data.get('character', 'N/A')}<br/>
    <b>Associated Symptoms:</b> {data.get('associated_symptoms', 'N/A')}<br/>
    <b>Past Medical History:</b> {data.get('past_medical_history', 'N/A')}<br/>
    <b>Family History:</b> {data.get('family_history', 'N/A')}<br/>
    <b>Medications:</b> {data.get('medications', 'N/A')}
    """

    p = Paragraph(history_text, style_body)
    p_width, p_height = p.wrapOn(c, width - 2*inch, height)
    p.drawOn(c, inch, y_pos - p_height - 0.1 * inch)

    c.save()
    print(f"📄 PDF report successfully saved to: {pdf_path}")
    return pdf_path
