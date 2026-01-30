import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from app.database.repository import save_token
from app.core.config import load_config

router = APIRouter()

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# This must match the Authorized Redirect URI in Google Console
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8001/auth/callback")

# Scopes needed for Gemini/Vertex AI
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/cloud-platform" # Broad scope for Vertex AI
]

def create_flow():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        # Fallback to local vars if not loaded yet? 
        # But config should be loaded by main.
        if not os.getenv("GOOGLE_CLIENT_ID"):
             raise HTTPException(status_code=500, detail="Missing Google Client Config")
        
    # Re-fetch from env to be safe
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    return Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

@router.get("/auth/login")
async def login(request: Request):
    """
    Initiates the OAuth flow.
    """
    try:
        flow = create_flow()
        # access_type='offline' is CRITICAL for getting a Refresh Token
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return RedirectResponse(authorization_url)
    except Exception as e:
        return {"error": str(e)}

@router.get("/auth/callback")
async def callback(request: Request, code: str):
    """
    Handles the callback from Google.
    Exchanges code for tokens.
    """
    try:
        flow = create_flow()
        flow.fetch_token(code=code)
        
        creds = flow.credentials
        
        user_info = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }
        
        # TODO: Extract phone from state/session
        # For MVP, we use a placeholder or derived ID.
        fake_phone = "1234567890" 
        
        await save_token(fake_phone, user_info)
        
        return {"status": "success", "message": "Authentication successful! Token saved.", "debug_info": "Token acquired & saved."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
