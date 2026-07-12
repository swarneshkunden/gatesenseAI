import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

SERVER_DIR = Path(__file__).resolve().parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from error_handlers import register_error_handlers
from routes import crowd, translation
from config import settings

app = FastAPI(
    title="FIFA World Cup 2026 - gatesenseAI",
    description="Backend API powering live crowd management and multilingual translation support for volunteers.",
    version="1.0.0"
)

# CORS setup for local development and production frontend hosts
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

# Add the deployed frontend URL when provided
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers (Prevents information leakage)
register_error_handlers(app)

# Include Routers
app.include_router(crowd.router)
app.include_router(translation.router)


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "FIFA World Cup 2026 - Volunteer Copilot API",
        "version": "1.0.0",
        "mock_mode": settings.gemini_api_key == ""
    }

if __name__ == "__main__":
    print(f"Starting Volunteer Copilot Backend on {settings.host}:{settings.port}")
    if not settings.gemini_api_key:
        print("[WARNING] GEMINI_API_KEY environment variable is missing. Running in Mock Engine Mode.")
    else:
        print("[SUCCESS] Gemini API Key found. Real AI engine enabled.")

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=(settings.environment == "development"))
