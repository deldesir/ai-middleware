import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.llm_engine import generate_response_core
from app.personas.manager import process_chat_request
from google.genai import types

# Helper to create a mock GenAI response
def create_mock_response(text=None, tool_calls=None):
    mock_resp = MagicMock()
    mock_candidate = MagicMock()
    mock_content = MagicMock()
    # ... (rest same, just updating imports)
def create_mock_response(text=None, tool_calls=None):
    mock_resp = MagicMock()
    mock_candidate = MagicMock()
    mock_content = MagicMock()
    mock_part = MagicMock()
    
    parts = []
    
    if tool_calls:
        for tc in tool_calls:
            p = MagicMock()
            p.function_call.name = tc["name"]
            p.function_call.args = tc["args"]
            p.text = None
            parts.append(p)
            
    if text:
        p = MagicMock()
        p.text = text
        p.function_call = None
        parts.append(p)
        
    mock_content.parts = parts
    mock_candidate.content = mock_content
    mock_resp.candidates = [mock_candidate]
    return mock_resp

@pytest.mark.asyncio
async def test_generate_started_response():
    """Verify simple text response generation via Manager"""
    
    # Patch the repository functions used by manager
    with patch("app.personas.manager.get_profile", new_callable=AsyncMock) as mock_get_profile, \
         patch("app.personas.manager.get_token", new_callable=AsyncMock) as mock_get_token, \
         patch("app.personas.manager.get_history", new_callable=AsyncMock) as mock_get_history, \
         patch("app.personas.manager.save_message", new_callable=AsyncMock) as mock_save_msg, \
         patch("app.personas.manager.get_api_keys", return_value=["AIzaMockKey"]), \
         patch("app.services.llm_engine.genai.Client") as MockClient:

        mock_get_profile.return_value = {"name": "Test"}
        mock_get_token.return_value = {"access_token": "AIzaUserKey"}
        mock_get_history.return_value = []
        
        # Setup Mock API Return
        mock_instance = MockClient.return_value
        mock_instance.models.generate_content.return_value = create_mock_response(text="Hello Test")
        
        resp = await process_chat_request(None, "50937000000", "Hi", "user_123", [])
        
        assert resp == "Hello Test"
        # Verify save_message was called twice (User + Assistant)
        assert mock_save_msg.call_count == 2

@pytest.mark.asyncio
async def test_update_profile_tool():
    """Verify the AI can update the user profile via Manager"""
    
    with patch("app.personas.manager.get_profile", new_callable=AsyncMock) as mock_get_profile, \
         patch("app.personas.manager.get_token", new_callable=AsyncMock) as mock_get_token, \
         patch("app.personas.manager.get_history", new_callable=AsyncMock) as mock_get_history, \
         patch("app.personas.manager.save_message", new_callable=AsyncMock) as mock_save_msg, \
         patch("app.personas.manager.save_profile", new_callable=AsyncMock) as mock_save_profile, \
         patch("app.personas.manager.get_api_keys", return_value=["AIzaMockKey"]), \
         patch("app.services.llm_engine.genai.Client") as MockClient:

        mock_instance = MockClient.return_value
        # Use a Mutable Dict for profile to verify updates locally if the code holds ref? 
        # Actually manager calls repository update.
        repo_profile = {} 
        mock_get_profile.return_value = repo_profile
        mock_get_history.return_value = []
        
        # Mock Tool Call Response
        mock_instance.models.generate_content.return_value = create_mock_response(
            tool_calls=[{"name": "update_profile", "args": {"data": {"city": "Jacmel"}}}]
        )
        
        resp = await process_chat_request(None, "50937000", "Moved", "user_ABC", [])
        
        # Verify save_profile called
        mock_save_profile.assert_called_once()
        # Verify call args
        args, _ = mock_save_profile.call_args
        assert args[0] == "user_ABC"
        assert args[1]["city"] == "Jacmel"

@pytest.mark.asyncio
async def test_key_rotation_fallback():
    """Verify Engine tries next key if first fails"""
    
    # We test the engine directly here
    with patch("app.services.llm_engine.genai.Client") as MockClient:
        mock_instance_1 = MagicMock()
        mock_instance_1.models.generate_content.side_effect = Exception("429 Resource exhausted")
        
        mock_instance_2 = MagicMock()
        mock_instance_2.models.generate_content.return_value = create_mock_response(text="Success Key 2")
        
        MockClient.side_effect = [mock_instance_1, mock_instance_2]
        
        # Helper call to engine core
        resp = await generate_response_core(
            "System", [], "Hi", [], ["Key1", "Key2"]
        )
        
        assert resp.candidates[0].content.parts[0].text == "Success Key 2"
        assert MockClient.call_count == 2
