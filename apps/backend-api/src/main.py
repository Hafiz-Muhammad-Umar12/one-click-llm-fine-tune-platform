from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import redis.asyncio as redis
from fastapi_limiter.depends import FastAPILimiter
from src.api.routers import api_router
from src.core.config import settings
from src.logging.logger import setup_logging
from src.websocket.manager import manager
from src.middleware.audit import AuditMiddleware

# Setup structured logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Central control plane for managing AI infrastructure, datasets, and training jobs.",
    version="1.0.0",
)

# Instrument the app for Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Add Audit Logging Middleware
app.add_middleware(AuditMiddleware)

@app.on_event("startup")
async def startup_event():
    await manager.broadcast.connect()
    redis_instance = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_instance)

@app.on_event("shutdown")
async def shutdown_event():
    await manager.broadcast.disconnect()
    await FastAPILimiter.close()

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
async def root():
    return {"message": "Welcome to the One-Click AI Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
