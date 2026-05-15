from fastapi import APIRouter
from src.api.v1 import auth, datasets, training, inference, deployments

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(training.router, prefix="/training", tags=["training"])
api_router.include_router(inference.router, prefix="/inference", tags=["inference"])
api_router.include_router(deployments.router, prefix="/deployments", tags=["deployments"])
