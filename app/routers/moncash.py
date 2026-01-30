from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database.repository import record_payment
import random

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/v1/moncash/mock/pay", response_class=HTMLResponse)
async def moncash_mock_pay(request: Request, amount: float, orderId: str):
    """
    Renders the Fake Payment Page.
    """
    return templates.TemplateResponse(request=request, name="mock_payment.html", context={"amount": amount, "order_id": orderId})

@router.post("/v1/moncash/mock/process")
async def moncash_mock_process(request: Request):
    """
    Processes the Fake Payment Form.
    Generates a transaction code and saves it to DB (PENDING).
    """
    form = await request.form()
    order_id = form.get("orderId")
    amount = float(form.get("amount"))
    
    # Generate Fake Transaction Code
    tx_code = f"MP-SIM-{random.randint(1000, 9999)}"
    
    await record_payment(
        code=tx_code,
        amount=amount,
        currency="HTG",
        sender="Simulation",
        raw_message=f"Simulated Payment for Order {order_id}"
    )
    
    return HTMLResponse(content=f"""
        <h1>Payment Successful! ✅</h1>
        <p>Your Transaction Code is: <strong>{tx_code}</strong></p>
        <p>Please copy this code and send it to the AI Agent on WhatsApp to activate your plan.</p>
    """)
