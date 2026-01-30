import pytest

@pytest.mark.asyncio
async def test_health(client):
    from unittest.mock import AsyncMock, patch
    
    with patch("app.database.connection.check_health", new_callable=AsyncMock) as mock_db, \
         patch("app.services.cache.check_health", new_callable=AsyncMock) as mock_cache:
        
        mock_db.return_value = True
        mock_cache.return_value = True
        
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["checks"]["database"] == "ok"
