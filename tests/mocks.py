class FakeDatabaseService:
    def __init__(self):
        self.tokens = {}
        self.chat_history = {}
        self.profiles = {}
        self.payments = {}

    async def get_token(self, phone_number: str):
        return self.tokens.get(phone_number)

    async def save_token(self, phone_number: str, token_data: dict):
        self.tokens[phone_number] = token_data

    async def get_history(self, user_id: str, limit: int=10):
        # Return last N messages from list
        # We store as list of dicts
        history = self.chat_history.get(user_id, [])
        return history[-limit:]

    async def save_message(self, user_id: str, role: str, content: str):
        if user_id not in self.chat_history:
            self.chat_history[user_id] = []
        self.chat_history[user_id].append({"role": role, "content": content})
        return True
        
    async def get_profile(self, user_id: str):
        return self.profiles.get(user_id, {})

    async def save_profile(self, user_id: str, profile_data: dict):
        if user_id not in self.profiles:
             self.profiles[user_id] = {}
        self.profiles[user_id].update(profile_data)
        
    async def record_payment(self, code, amount, currency, sender, raw_message):
        self.payments[code] = {
            "amount": amount, 
            "currency": currency, 
            "sender": sender, 
            "status": "PENDING"
        }
        # Store raw_message if needed or ignore
        return True
        
    async def claim_payment(self, code, user_id):
        if code not in self.payments:
            return False, "Not Found", 0.0
        
        p = self.payments[code]
        if p["status"] == "CLAIMED":
            return False, "Claimed", 0.0
            
        p["status"] = "CLAIMED"
        p["claimed_by"] = user_id
        return True, "Success", p["amount"]
        
    async def check_health(self):
        return True
