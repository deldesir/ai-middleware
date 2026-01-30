import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_moncash_mock_flow():
    # 1. Test Client Simulation
    from app.services.moncash import MonCashClient
    import os
    # Ensure env var is set for test (or mocked) context
    # We rely on what's already loaded or default
    
    client = MonCashClient()
    # Assertion: New logic should auto-detect valid/invalid keys
    # Since environment has "YOUR_CLIENT_ID" (or similar placeholders from llm.py/config.py injection), it should be True
    assert client.simulation is True, "Simulation should be auto-detected due to placeholders"
    
    link = client.create_payment("TEST-ORDER-1", 1000)
    assert "v1/moncash/mock/pay" in link
    
    # 2. Test GET Page
    # Handle dynamic PUBLIC_URL
    import os
    public_url = os.getenv("MIDDLEWARE_PUBLIC_URL", "http://localhost:8001")
    relative_path = link.replace(public_url, "")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(relative_path)
        assert res.status_code == 200
        assert "SIMULATION MODE" in res.text
        assert "1000" in res.text
        
    # 3. Test POST Process (Payment Success)
    # Patch the repository function used by the router
    from tests.mocks import FakeDatabaseService
    fake_db = FakeDatabaseService()
    
    # We patch record_payment to use our fake_db's implementation
    with patch("app.routers.moncash.record_payment", side_effect=fake_db.record_payment):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res_post = await ac.post("/v1/moncash/mock/process", data={
                "orderId": "TEST-ORDER-1",
                "amount": "1000"
            })
            assert res_post.status_code == 200
            assert "Payment Successful" in res_post.text
            assert "Transaction Code is" in res_post.text
            
            # Verify Payment in Fake DB
            assert len(fake_db.payments) == 1
            code = list(fake_db.payments.keys())[0]
            assert "MP-SIM-" in code
            assert fake_db.payments[code]["amount"] == 1000.0
