# KonexPro AI Middleware v2.0

## 1. Overview
This is the core intelligence layer for the KonexPro AI system. It acts as the bridge between:
*   **Messaging**: WuzAPI (WhatsApp), RapidPro (Flows)
*   **Intelligence**: Google Gemini (via `google-genai` SDK)
*   **Payments**: MonCash (Simulation & Real)

## 2. Architecture
The application is structured as a modular FastAPI app in `app/`:
```text
app/
├── core/           # Configuration & logging
├── database/       # AsyncPG connection & repositories
├── services/       # Business logic (LLM, RapidPro, MonCash)
├── personas/       # Dynamic persona management ("Sarah", Custom Bots)
├── routers/        # API endpoints (Webhooks, Mock Payments)
└── main.py         # Application Entry Point
```

## 3. Configuration
The system strictly follows the IIAB configuration standard.
Use **/etc/iiab/local_vars.yml** to configure the service.

**Example Configuration:**
```yaml
ai_middleware_google_api_key: "AIzaSy..."
ai_middleware_admin_phones: "50937000000,50938000000"  # Comma-separated list for God Mode
moncash_client_id: "your-id"
moncash_client_secret: "your-secret"
moncash_env: "sandbox" # or live
```

*Note: You can still use a local `.env` file for development, but `local_vars.yml` takes precedence.*

## 4. Admin "God Mode"
Users listed in `ai_middleware_admin_phones` (mapped to `ADMIN_PHONES` env var) get special privileges:
*   **System Tools**: improved prompt overriding normal persona behavior.
*   **Health Checks**: Access to `get_system_status` tool via chat.

## 5. Running the Service
The service is managed via systemd but can be run manually:

```bash
cd /opt/iiab/ai-middleware
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## 6. Endpoints
*   **Health Check**: `GET /health`
*   **Chat Completion**: `POST /chat` (RapidPro compatible)
*   **Webhooks**: `POST /hooks/sms`, `POST /webhooks/wuzapi`
*   **MonCash Mock**: `GET /v1/moncash/mock/pay`

## 7. Migration Notes (v1 -> v2)
*   Legacy files (`llm.py`, `db.py`) are archived in `legacy_backup/`.
*   Entry point changed from `main.py` to `app.main:app`.
