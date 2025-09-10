"""
PDF Generation Service.

This service is responsible for creating a structured, professional-looking
medical summary PDF from the patient's data. It takes a Python dictionary,
populates a predefined template using the ReportLab library, and saves
the PDF to a specified directory.
"""
from datetime import datetime
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from config import PDF_REPORTS_DIR

def generate_pdf_report(data: dict) -> Path:
    """
    Generates a medical summary PDF report from structured data.

    Args:
        data: A dictionary containing the patient's structured summary.
              Expected keys: 'chief_complaint', 'onset', 'character', etc.

    Returns:
        The Path object pointing to the newly created PDF file.
    """
    # Create a unique filename for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = PDF_REPORTS_DIR / f"Medical_Summary_Report_{timestamp}.pdf"

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter
    styles = getSampleStyleSheet()

    # --- PDF Header ---
    generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - inch, height - 0.9 * inch, f"Generated on: {generation_time}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(inch, height - 0.9 * inch, "Disclaimer: For informational purposes only. Not medical advice.")

    # --- PDF Title ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, height - inch * 1.2, "Pre-Visit Medical Summary")
    c.line(inch, height - inch * 1.3, width - inch, height - inch * 1.3)

    # --- Chief Complaint Section ---
    y_position = height - inch * 1.7
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, "Chief Complaint:")
    c.setFont("Helvetica", 11)
    c.drawString(inch * 2.5, y_position, data.get("chief_complaint", "N/A"))

    # --- History of Present Illness Section ---
    y_position -= inch * 0.5
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y_position, "History of Present Illness:")

    style_body = styles['BodyText']
    style_body.fontName = 'Helvetica'
    style_body.fontSize = 11
    style_body.leading = 14

    history_text = f"""
    <b>Onset:</b> {data.get('onset', 'N/A')}<br/>
    <b>Character:</b> {data.get('character', 'N/A')}<br/>
    <b>Associated Symptoms:</b> {data.get('associated_symptoms', 'N/A')}<br/>
    <b>Relevant History:</b> {data.get('relevant_history', 'N/A')}
    """

    p = Paragraph(history_text, style_body)
    # Calculate height of the paragraph to adjust drawing position
    p_width, p_height = p.wrapOn(c, width - 2 * inch, height)
    p.drawOn(c, inch, y_position - p_height - 0.1 * inch)

    c.save()
    print(f"📄 PDF report successfully saved to: {pdf_path}")
    return pdf_path
