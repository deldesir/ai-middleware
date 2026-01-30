import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.rapidpro import RapidProService

@pytest.fixture
def mock_temba_client():
    # RESET SINGLETON
    RapidProService._instance = None
    
    with patch("app.services.rapidpro.TembaClient") as MockClient:
        client_instance = MockClient.return_value
        yield client_instance
        # Teardown
        RapidProService._instance = None

@pytest.mark.asyncio
async def test_get_contact(mock_temba_client):
    service = RapidProService.get_instance()
    
    # Mock the chain: client.get_contacts(urns=[...]).first()
    mock_query = MagicMock()
    mock_query.first.return_value = {"uuid": "123", "name": "Test User"}
    mock_temba_client.get_contacts.return_value = mock_query

    # Execute
    result = await service.get_contact("tel:+12345")
    
    # Verify
    assert result == {"uuid": "123", "name": "Test User"}
    mock_temba_client.get_contacts.assert_called_with(urns=["tel:+12345"])

@pytest.mark.asyncio
async def test_update_contact(mock_temba_client):
    service = RapidProService.get_instance()
    
    mock_temba_client.update_contact.return_value = {"uuid": "123", "name": "Updated"}
    
    result = await service.update_contact("123", {"name": "Updated"})
    
    assert result["name"] == "Updated"
    mock_temba_client.update_contact.assert_called_with("123", fields={"name": "Updated"})

@pytest.mark.asyncio
async def test_start_flow_error(mock_temba_client):
    service = RapidProService.get_instance()
    
    # Simulate error
    mock_temba_client.create_flow_start.side_effect = Exception("API Error")
    
    success = await service.start_flow("tel:+123", "flow-uuid")
    
    assert success is False
