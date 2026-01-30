import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_openai_completion_success():
    # Mock the internal manager to avoid DB/LLM calls
    with patch("app.routers.openai_compat.process_chat_request", new_callable=MagicMock) as mock_process:
        mock_process.return_value = "Hello from AI" # Mocked Sync return or Async?
        # process_chat_request is async, so we need an AsyncMock or configure return_value
        
        # Correctly patching async function
        with patch("app.routers.openai_compat.process_chat_request") as mock_process_async:
            mock_process_async.return_value = "Hello from AI"
        
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "Hi there"},
                ],
                "user": "tel:+12345"
            }
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post("/v1/chat/completions", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["object"] == "chat.completion"
            assert data["choices"][0]["message"]["content"] == "Hello from AI"
