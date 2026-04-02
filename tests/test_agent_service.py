import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.language_models import FakeListChatModel
from securemed_chat.services.agent_service import (
    get_language_instructions,
    get_initial_agent_chain,
    get_follow_up_agent_chain,
    get_structuring_chain,
    stream_initial_questions,
    stream_follow_up_questions,
    summarize_and_structure_anamnesis
)

def test_language_instructions_en():
    instr = get_language_instructions("en")
    assert "English" in instr["initial_q_instruction"]
    assert "not mentioned" in instr["not_mentioned"].lower()

def test_language_instructions_pt():
    instr = get_language_instructions("pt")
    assert "Português" in instr["initial_q_instruction"]
    assert "não mencionado" in instr["not_mentioned"].lower()

@pytest.mark.asyncio
@patch("securemed_chat.services.agent_service.get_llm")
async def test_initial_questions_chain_workflow(mock_get_llm):
    fake_llm = FakeListChatModel(responses=["1. Question 1", "2. Question 2"])
    mock_get_llm.return_value = fake_llm
    
    chain = get_initial_agent_chain()
    questions = []
    async for chunk in stream_initial_questions("Headache", "en", chain):
        questions.append(chunk)
    
    full_text = "".join(questions)
    assert "Question 1" in full_text
    assert mock_get_llm.called

@pytest.mark.asyncio
@patch("securemed_chat.services.agent_service.get_llm")
async def test_follow_up_questions_chain_workflow(mock_get_llm):
    fake_llm = FakeListChatModel(responses=["1. History?"])
    mock_get_llm.return_value = fake_llm
    
    chain = get_follow_up_agent_chain()
    questions = []
    async for chunk in stream_follow_up_questions("Headache", "It started yesterday.", "en", chain):
        questions.append(chunk)
    
    full_text = "".join(questions)
    assert "History" in full_text
    assert mock_get_llm.called

@pytest.mark.asyncio
@patch("securemed_chat.services.agent_service.get_llm")
async def test_structuring_chain_workflow(mock_get_llm):
    # Mocking JsonOutputParser's expectation of JSON string
    fake_json = '{"onset": "yesterday", "character": "sharp", "associated_symptoms": "none", "past_medical_history": "none", "family_history": "none", "medications": "none"}'
    fake_llm = FakeListChatModel(responses=[fake_json])
    mock_get_llm.return_value = fake_llm
    
    chain = get_structuring_chain()
    result = await summarize_and_structure_anamnesis("Headache", "yesterday", "none", "en", chain)
    
    assert result["onset"] == "yesterday"
    assert "character" in result
    assert mock_get_llm.called
