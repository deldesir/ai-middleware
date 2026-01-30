import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import MagicMock, patch

@pytest.mark.asyncio
async def test_auth_login_redirect():
    with patch("app.routers.auth.Flow") as MockFlow:
        mock_flow_instance = MockFlow.from_client_config.return_value
        mock_flow_instance.authorization_url.return_value = ("http://auth.google.com", "state")
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/auth/login")
        
        # Should redirect
        assert response.status_code == 307
        assert response.headers["location"] == "http://auth.google.com"

@patch("app.routers.auth.save_token")
@pytest.mark.asyncio
async def test_auth_callback_success(mock_save_token):
    with patch("app.routers.auth.Flow") as MockFlow:
        mock_flow_instance = MockFlow.from_client_config.return_value
        
        # Mock credentials
        mock_creds = MagicMock()
        mock_creds.token = "access_token"
        mock_creds.refresh_token = "refresh_token"
        mock_creds.token_uri = "uri"
        mock_creds.client_id = "cid"
        mock_creds.client_secret = "csecret"
        mock_creds.scopes = ["email"]
        
        mock_flow_instance.credentials = mock_creds
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/auth/callback?code=fake_code")
            
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Check if saved to DB (Mocked)
        mock_save_token.assert_called_once()
