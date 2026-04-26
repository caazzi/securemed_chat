import pytest
from unittest.mock import patch
from securemed_chat.services.pdf_service import generate_pdf_report_in_memory, translations

MINIMAL_FORM = {
    "specialist": "Gastroenterologist",
    "age_bracket": "26-35",
    "sex": "Female",
    "chief_complaint": "Stomach pain",
    "duration": "Weeks",
    "complaint_detail": "",
    "conditions": [],
    "medications": [],
    "allergies": "",
    "family_history": [],
    "smoking": "Never smoked",
    "alcohol": "Rarely",
}

MINIMAL_QA = [{"question": "Any nausea?", "answer": "Yes, sometimes."}]

def test_pdf_valid_bytes_en():
    pdf_bytes, filename = generate_pdf_report_in_memory(MINIMAL_FORM, MINIMAL_QA, lang="en")
    assert pdf_bytes.startswith(b"%PDF-")
    assert filename.startswith("Medical_Summary_Report")
    assert filename.endswith(".pdf")

def test_pdf_valid_bytes_pt():
    pdf_bytes, filename = generate_pdf_report_in_memory(MINIMAL_FORM, MINIMAL_QA, lang="pt")
    assert pdf_bytes.startswith(b"%PDF-")
    assert filename.startswith("Resumo_Medico")
    assert filename.endswith(".pdf")

@patch("securemed_chat.services.pdf_service.Paragraph")
@patch("securemed_chat.services.pdf_service.canvas.Canvas")
def test_pdf_renders_form_section(mock_canvas_class, mock_paragraph):
    mock_paragraph.return_value.wrapOn.return_value = (100, 20)
    form = {**MINIMAL_FORM, "specialist": "Cardio", "chief_complaint": "chest pain"}
    generate_pdf_report_in_memory(form, MINIMAL_QA, lang="en")
    all_text = " ".join(str(call) for call in mock_paragraph.call_args_list)
    all_text += " ".join(str(call) for call in mock_canvas_class.return_value.drawString.call_args_list)
    assert "Cardio" in all_text
    assert "chest pain" in all_text

@patch("securemed_chat.services.pdf_service.Paragraph")
@patch("securemed_chat.services.pdf_service.canvas.Canvas")
def test_pdf_renders_qa_section(mock_canvas_class, mock_paragraph):
    mock_paragraph.return_value.wrapOn.return_value = (100, 20)
    qa = [{"question": "How severe?", "answer": "Very bad"}]
    generate_pdf_report_in_memory(MINIMAL_FORM, qa, lang="en")
    all_text = " ".join(str(call) for call in mock_paragraph.call_args_list)
    assert "How severe?" in all_text
    assert "Very bad" in all_text

@patch("securemed_chat.services.pdf_service.Paragraph")
@patch("securemed_chat.services.pdf_service.canvas.Canvas")
def test_pdf_none_reported_for_empty_lists(mock_canvas_class, mock_paragraph):
    mock_paragraph.return_value.wrapOn.return_value = (100, 20)
    form = {**MINIMAL_FORM, "conditions": [], "medications": [], "family_history": []}
    generate_pdf_report_in_memory(form, MINIMAL_QA, lang="en")
    all_text = " ".join(str(call) for call in mock_paragraph.call_args_list)
    assert "None reported" in all_text

def test_pdf_empty_qa_pairs_does_not_crash():
    pdf_bytes, _ = generate_pdf_report_in_memory(MINIMAL_FORM, [], lang="en")
    assert pdf_bytes.startswith(b"%PDF-")

@patch("securemed_chat.services.pdf_service.Paragraph")
@patch("securemed_chat.services.pdf_service.canvas.Canvas")
def test_pdf_pagination_long_answer(mock_canvas_class, mock_paragraph):
    mock_paragraph.return_value.wrapOn.return_value = (100, 600)
    qa = [{"question": "Describe your symptoms", "answer": "word " * 500}]
    generate_pdf_report_in_memory(MINIMAL_FORM, qa, lang="en")
    assert mock_canvas_class.return_value.showPage.call_count >= 1

def test_pdf_unknown_lang_defaults_to_en():
    pdf_bytes, filename = generate_pdf_report_in_memory(MINIMAL_FORM, MINIMAL_QA, lang="xx")
    assert pdf_bytes.startswith(b"%PDF-")
    assert filename.startswith("Medical_Summary_Report")
    assert filename.endswith(".pdf")
