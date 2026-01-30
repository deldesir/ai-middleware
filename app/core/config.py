import os
import yaml
from dotenv import load_dotenv

load_dotenv()

IIAB_CONFIG_PATH = "/etc/iiab/local_vars.yml"
CONFIG_MAPPING = {
    "ai_middleware_google_api_key": "GOOGLE_API_KEY",
    "ai_middleware_google_client_id": "GOOGLE_CLIENT_ID",
    "ai_middleware_google_client_secret": "GOOGLE_CLIENT_SECRET",
    "ai_middleware_admin_phones": "ADMIN_PHONES",
    "moncash_client_id": "MONCASH_CLIENT_ID",
    "moncash_client_secret": "MONCASH_CLIENT_SECRET", 
    "moncash_env": "MONCASH_ENV",
    "ai_middleware_database_url": "DATABASE_URL" 
}

def load_config():
    """
    Reads /etc/iiab/local_vars.yml and injects overrides into os.environ.
    """
    if not os.path.exists(IIAB_CONFIG_PATH):
        return

    try:
        with open(IIAB_CONFIG_PATH, 'r') as f:
            iiab_vars = yaml.safe_load(f) or {}
            
        for yaml_key, env_key in CONFIG_MAPPING.items():
            if yaml_key in iiab_vars:
                value = iiab_vars[yaml_key]
                if value is True: value = "true"
                if value is False: value = "false"
                if value is None: continue
                os.environ[env_key] = str(value)
    except Exception as e:
        print(f"Failed to load IIAB config: {e}")

# Load on import
load_config()

def get_api_keys(user_token_record=None):
    """
    Returns list of API keys: User's key (if exists) + System Keys
    """
    keys = []
    if user_token_record:
        keys.append(user_token_record['access_token'])
        
    system_keys = os.getenv("GOOGLE_API_KEY", "").split(",")
    keys.extend([k.strip() for k in system_keys if k.strip()])
    return keys
