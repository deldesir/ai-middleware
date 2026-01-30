import re

def parse_payment_sms(body: str, sender: str):
    """
    Parses SMS body for Payment Code, Amount, and Currency.
    Supports: MonCash, Natcash (Mock Patterns).
    """
    result = {
        "code": None,
        "amount": 0.0,
        "currency": "HTG",
        "sender": sender
    }
    
    # MonCash Pattern (Example: "You received 500 HTG from 509... Ref: MP240129.1234")
    # Real pattern likely: "Trans ID: MP... You have received..."
    # Let's use a robust regex for the "Ref" or "ID"
    
    # 1. MonCash (Ref: MP...)
    moncash_match = re.search(r"(Ref:|Id:)\s*([A-Za-z0-9]+(?:\.[0-9]+)?)", body, re.IGNORECASE)
    if moncash_match:
        result["code"] = moncash_match.group(2).strip()
        
        # Amount
        amount_match = re.search(r"(\d+(\.\d+)?)\s*(HTG|USD|Gourdes)", body, re.IGNORECASE)
        if amount_match:
             result["amount"] = float(amount_match.group(1))
             result["currency"] = amount_match.group(3).upper() # Normalize? HTG
             if "GOURDES" in result["currency"]: result["currency"] = "HTG"
             
        return result

    # 2. Natcash (Example: "Trans ID: NC...")
    natcash_match = re.search(r"Trans ID:\s*([A-Z0-9]+)", body, re.IGNORECASE)
    if natcash_match:
        result["code"] = natcash_match.group(1).strip()
        
        amount_match = re.search(r"(\d+(\.\d+)?)\s*(HTG|USD)", body, re.IGNORECASE)
        if amount_match:
             result["amount"] = float(amount_match.group(1))
             result["currency"] = amount_match.group(3).upper()
             
        return result
        
    return None
