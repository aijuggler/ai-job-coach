from fastapi import FastAPI
from app.config.settings import settings
from app.config.logging import setup_logging

setup_logging(settings.log_level)
app = FastAPI(title="Interview Coach API (M0)")

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}
