from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import api_router
from src.core.config import settings
from src.logging.logger import setup_logging

# Setup structured logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Central control plane for managing AI infrastructure, datasets, and training jobs.",
    version="1.0.0",
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
...
async def root():
    return {"message": "Welcome to the One-Click AI Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
