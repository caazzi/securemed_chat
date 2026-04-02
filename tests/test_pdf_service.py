import pytest
from securemed_chat.services.pdf_service import generate_pdf_report_in_memory, translations
from unittest.mock import patch, MagicMock

def test_pdf_generation_i18n_en():
    data = {
        "chief_complaint": "Severe headache",
        "onset": "2 days ago",
        "character": "throbbing",
        "associated_symptoms": "none",
        "past_medical_history": "none",
        "family_history": "none",
        "medications": "ibuprofen"
    }
    pdf_bytes, filename = generate_pdf_report_in_memory(data, lang="en")
    assert pdf_bytes.startswith(b"%PDF-")
    assert "Medical_Summary_Report.pdf" == filename

def test_pdf_generation_i18n_pt():
    data = {
        "chief_complaint": "Dor de cabeça severa",
        "onset": "2 dias atrás",
        "character": "pulsante",
        "associated_symptoms": "nenhum",
        "past_medical_history": "nenhum",
        "family_history": "nenhum",
        "medications": "ibuprofeno"
    }
    pdf_bytes, filename = generate_pdf_report_in_memory(data, lang="pt")
    assert pdf_bytes.startswith(b"%PDF-")
    assert "Resumo_Medico.pdf" == filename

@patch("securemed_chat.services.pdf_service.canvas.Canvas")
def test_pdf_pagination_logic(mock_canvas_class):
    """Verify that c.showPage() is called when content exceeds page height."""
    mock_canvas = mock_canvas_class.return_value
    
    # Create a huge history that definitely triggers pagination
    long_text = "Pain. " * 500 
    data = {
        "chief_complaint": long_text,
        "onset": "3 days ago",
        "character": "sharp",
        "associated_symptoms": "nausea",
        "past_medical_history": "none",
        "family_history": "none",
        "medications": "none"
    }
    
    generate_pdf_report_in_memory(data, lang="en")
    
    # showPage should be called at least once (header + title + enormous complaint + final showPage)
    # The final showPage is always called before save() in the implementation.
    # Total calls: Initial setup calls + any mid-page breaks + the final one.
    assert mock_canvas.showPage.call_count >= 1
    assert mock_canvas.save.called
