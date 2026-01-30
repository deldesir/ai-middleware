import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_create_wuzapi_session():
    """
    Verifies that create_wuzapi_session sends the correct POST request.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success", "id": "123"}
    
    # Mock httpx.AsyncClient context manager
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        # We need to ensure __aenter__ returns the mock_client
        mock_client.__aenter__.return_value = mock_client
        
        from app.services.rapidpro import create_wuzapi_session
        result = await create_wuzapi_session("test_user")
        
        assert result["status"] == "success"
        mock_client.post.assert_called_once()
        args = mock_client.post.call_args
        assert "http://localhost:8080/session/create" in args[0]
        assert args[1]["json"] == {"sessionid": "test_user"}

@pytest.mark.asyncio
async def test_get_wuzapi_qr():
    """
    Verifies that get_wuzapi_qr GETs the correct endpoint and returns bytes.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake_qr_png"
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        mock_client.__aenter__.return_value = mock_client
        
        from app.services.rapidpro import get_wuzapi_qr
        qr_bytes = await get_wuzapi_qr("test_user")
        
        assert qr_bytes == b"fake_qr_png"
        mock_client.get.assert_called_once()
        assert "http://localhost:8080/session/qr/test_user" in mock_client.get.call_args[0][0]

@pytest.mark.asyncio
async def test_get_pairing_code_success():
    """
    Verifies that get_wuzapi_pairing_code sends the correct POST request.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"LinkingCode": "ABC-123"}
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        mock_client.__aenter__.return_value = mock_client
        
        from app.services.rapidpro import get_wuzapi_pairing_code
        code = await get_wuzapi_pairing_code("user123", "509123456")
        
        assert code == "ABC-123"
        mock_client.post.assert_called_once()
        args = mock_client.post.call_args
        assert "http://localhost:8080/session/pairphone" in args[0]
        assert args[1]["json"] == {"phone": "509123456", "sessionid": "user123"}

@pytest.mark.asyncio
async def test_provision_channel_success():
    """
    Verifies that provision_channel_programmatically calls subprocess correctly.
    """
    # Mock subprocess result
    mock_process = MagicMock()
    mock_process.returncode = 0
    # The script prints JSON at the end
    mock_process.stdout = 'Debug log...\n{"status": "success", "wuzapi_username": "12345"}' 
    
    with patch("subprocess.run", return_value=mock_process) as mock_run:
        from app.services.rapidpro import provision_channel_programmatically
        result = await provision_channel_programmatically("50912345678")
        
        assert result["status"] == "success"
        assert result["wuzapi_username"] == "12345"
        
        # Verify Command
        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        assert "manage_channels.py" in cmd_args[1]
        assert "50912345678" in cmd_args
