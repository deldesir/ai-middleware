import config
import os
import requests
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class MonCashClient:
    def __init__(self):
        self.client_id = os.getenv("MONCASH_CLIENT_ID")
        self.client_secret = os.getenv("MONCASH_CLIENT_SECRET")
        self.is_production = os.getenv("MONCASH_ENV", "sandbox") == "live"
        
        # Public URL for callbacks
        self.public_url = os.getenv("MIDDLEWARE_PUBLIC_URL", "http://localhost:8001")
        
        # Decide Simulation Mode
        self.simulation = False
        
        # Check for explicit simulation flag
        if os.getenv("MONCASH_SIMULATION", "false").lower() == "true":
             self.simulation = True
             logger.info("⚠️ MonCash Simulation ON (Environment Flag)")
             
        # Check for missing or placeholder credentials
        elif not self.client_id or not self.client_secret or "YOUR_CLIENT_ID" in self.client_id or "ENTER_" in self.client_id:
            logger.warning("⚠️ MonCash Credentials missing or invalid (Placeholder detected). Using SIMULATION MODE.")
            self.simulation = True
            
        # MonCash URLs
        self.base_url = "https://moncashbutton.digicelgroup.com/Moncash-middleware" if self.is_production else "https://sandbox.moncashbutton.digicelgroup.com/Moncash-middleware"

    def get_token(self):
        """
        Gets OAuth Bearer Token (Real Mode Only).
        """
        if self.simulation:
            return "simulated_token"
            
        auth = (self.client_id, self.client_secret)
        try:
            res = requests.post(f"{self.base_url}/oauth/token", auth=auth, data={"scope": "read,write", "grant_type": "client_credentials"}, timeout=10)
            res.raise_for_status()
            return res.json().get("access_token")
        except Exception as e:
            logger.error(f"MonCash Token Error: {e}")
            return None

    def create_payment(self, order_id: str, amount: float):
        """
        Generates a Payment URL.
        """
        if self.simulation:
            # Return our Mock Gateway URL
            # We encode params so the Mock Page can display them
            params = {
                "orderId": order_id,
                "amount": amount,
                "item": "KonexPro Plan"
            }
            return f"{self.public_url}/v1/moncash/mock/pay?{urlencode(params)}"
            
        # REAL MODE (Future Implementation)
        token = self.get_token()
        if not token:
            return None
            
        payload = {
            "amount": amount,
            "orderId": order_id
        }
        try:
            res = requests.post(
                f"{self.base_url}/v1/CreatePayment",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
                timeout=10
            )
            res.raise_for_status()
            # Redirect URL is usually in the response "redirect" or constructed
            # Sandbox: https://sandbox.moncashbutton.digicelgroup.com/Moncash-middleware/Payment/Redirect?token=...
            payment_token = res.json().get("payment_token") # Hypothetical key
            return res.json().get("redirect_url") # Hypothetical key
        except Exception as e:
            logger.error(f"MonCash Create Payment Error: {e}")
            return None
