# Tool Definitions for LiteLLM / OpenAI
# These define the capabilities available to the AI

tools_schema = [

    {
        "type": "function",
        "function": {
            "name": "stop_messages",
            "description": "Opt-out the user from receiving future automated messages. Use when user says 'Stop', 'Unsubscribe', or 'Cancel'.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "terminate_account",
            "description": "Permanently delete the user's account and data. Use ONLY when user explicitly asks to 'Delete Account' or 'Erase Data'.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Flags the conversation for immediate human review. Use ONLY when the user is angry, frustrated, explicitly asks for a 'real person', or the request is too complex for you.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "The reason for escalation (e.g., 'User Angry', 'Complex Query')."
                    }
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verify_payment",
            "description": "Verifies a payment transaction code (e.g. MonCash, Natcash) provided by the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_code": {
                        "type": "string",
                        "description": "The alphanumeric transaction code (e.g. MP240129.1234)."
                    }
                },
                "required": ["transaction_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_payment_link",
            "description": "Generates a MonCash payment link for the user to click and pay.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_type": {
                        "type": "string",
                        "enum": ["starter", "pro"],
                        "description": "The plan the user wants to buy."
                    }
                },
                "required": ["plan_type"]
            }
        }
    }
]

admin_tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Checks the health of the Database and Cache.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_user",
            "description": "Retrieves details about a specific user (Token status, History summary).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_phone": {
                        "type": "string",
                        "description": "The phone number to look up (e.g. 509...)."
                    }
                },
                "required": ["target_phone"]
            }
        }
    }
]
