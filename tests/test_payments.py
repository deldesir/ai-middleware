import pytest
from unittest.mock import MagicMock
from app.services.parsers import parse_payment_sms

def test_manual_sms_parsing():
    # MonCash Case
    body = "Transfert de 500 HTG recu de 50937000000. Ref: MP240129.1234. Solde: 1500"
    parsed = parse_payment_sms(body, "MonCash")
    assert parsed["code"] == "MP240129.1234"
    assert parsed["amount"] == 500.0
    assert parsed["currency"] == "HTG"
    
    # Natcash Case
    body = "Trans ID: NC123456. You have received 10.00 USD from 509..."
    parsed = parse_payment_sms(body, "Natcash")
    assert parsed["code"] == "NC123456"
    assert parsed["amount"] == 10.0
    assert parsed["currency"] == "USD"

@pytest.mark.asyncio
async def test_db_payment_flow(): 
    # We need to mock the DB connection for record/claim
    from app.database.repository import record_payment, claim_payment
    from unittest.mock import patch, AsyncMock, MagicMock
    
    # Mocking Record
    # db.get_db_connection is an async function, so the mock replacing it must be awaitable
    # calling it returns a coroutine that yields the connection.
    
    msg_mock = AsyncMock() # The Connection object
    msg_mock.execute.return_value = "UPDATE 1"
    msg_mock.fetchrow.return_value = {"status": "PENDING", "amount": 500, "currency": "HTG", "claimed_by": None}
    msg_mock.close.return_value = None
    
    # When we await get_db_connection(), we get msg_mock
    async_get_db = AsyncMock(return_value=msg_mock)
    
    with patch("app.database.repository.get_db_connection", side_effect=async_get_db):
        
        # 1. Record
        await record_payment("CODE123", 500, "HTG", "509111", "raw")
        msg_mock.execute.assert_called()
        
        # 2. Claim Success
        success, msg, amt = await claim_payment("CODE123", "user_A")
        assert success is True
        assert amt == 500.0
        
        # 3. Claim Fail (Already Claimed)
        msg_mock.fetchrow.return_value = {"status": "CLAIMED", "amount": 500, "currency": "HTG", "claimed_by": "user_B"}
        
        success, msg, amt = await claim_payment("CODE123", "user_A")
        assert success is False
        assert "used by someone else" in msg
