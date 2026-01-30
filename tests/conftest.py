import pytest
import sys
import os
from httpx import AsyncClient, ASGITransport

# Fix Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from unittest.mock import AsyncMock, patch

@pytest.fixture
async def client():
    # Mock DB Init completely to prevent startup failure
    with patch("app.database.schema.init_db", new_callable=AsyncMock) as mock_init:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

