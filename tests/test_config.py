import pytest
import os
import yaml
from unittest.mock import patch, mock_open

@pytest.fixture
def mock_yaml_content():
    return yaml.dump({
        "ai_middleware_admin_phones": "999999999,888888888",
        "moncash_client_id": "YAML_ID",
        "ai_middleware_google_api_key": "YAML_KEY"
    })

def test_config_loading_with_yaml(mock_yaml_content):
    from app.core import config
    import importlib
    
    # Mock FS calls
    # We use side_effect for open to handle the specific file, or just return mock for all opens
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)) as mock_file:
        with patch("os.path.exists", return_value=True):
             # clear env to ensure we test injection
             with patch.dict(os.environ, {}, clear=True):
                 # Patch dotenv to avoid stack frame issues during reload
                 with patch("dotenv.load_dotenv"):
                     importlib.reload(config)
                 
                 assert os.environ.get("ADMIN_PHONES") == "999999999,888888888"
                 assert os.environ.get("MONCASH_CLIENT_ID") == "YAML_ID"
                 # Test override priority (YAML > Env? config.py code says it overwrites)
                 assert os.environ.get("GOOGLE_API_KEY") == "YAML_KEY"

def test_config_loading_no_yaml():
    from app.core import config
    import importlib
    
    # Mock exists = False
    with patch("os.path.exists", return_value=False):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "ENV_KEY"}, clear=True):
            with patch("dotenv.load_dotenv"):
                importlib.reload(config)
            # Should NOT change (since file not found)
            assert os.environ.get("GOOGLE_API_KEY") == "ENV_KEY"
