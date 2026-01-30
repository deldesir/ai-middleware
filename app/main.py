import app.core.config # Load IIAB Config (local_vars.yml) first
from fastapi import FastAPI, BackgroundTasks, Request
from app.database.schema import init_db
from app.routers import webhooks
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="KonexPro AI Middleware", version="2.0")

@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Middleware Starting...")
    await init_db()

@app.get("/health")
async def health_check():
    from app.database.connection import check_health as db_health
    # from app.services.cache import check_health as cache_health # Optional if we moved it
    # For now, let's just do DB
    db_ok = await db_health()
    return {
        "status": "ok" if db_ok else "error",
        "checks": {
            "database": "ok" if db_ok else "error"
        }
    }

from app.routers import webhooks, moncash, auth
# ...
app.include_router(webhooks.router)
app.include_router(moncash.router)
app.include_router(auth.router)

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "KonexPro AI Middleware v2.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
