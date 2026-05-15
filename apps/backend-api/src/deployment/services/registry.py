import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from opentelemetry import trace

from src.models.deployment import RegisteredModel, ModelVersion, ModelArtifact
from src.deployment.repositories.registry import registered_model_repo, model_version_repo
from src.deployment.schemas.registry import RegisteredModelCreate, ModelVersionCreate

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class ModelRegistryService:
    """
    Service for managing the Model Registry and Versioning.
    Links models to Training Runs.
    """
    async def create_registered_model(
        self, db: AsyncSession, organization_id: uuid.UUID, model_in: RegisteredModelCreate
    ) -> RegisteredModel:
        with tracer.start_as_current_span("create_registered_model"):
            db_obj = RegisteredModel(
                organization_id=organization_id,
                name=model_in.name,
                description=model_in.description
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj

    async def register_model_version(
        self, db: AsyncSession, version_in: ModelVersionCreate, artifacts: List[Dict[str, Any]]
    ) -> ModelVersion:
        """
        Creates an immutable model version tied to a specific training run.
        """
        with tracer.start_as_current_span("register_model_version"):
            # 1. Create Version
            db_obj = ModelVersion(
                registered_model_id=version_in.registered_model_id,
                training_run_id=version_in.training_run_id,
                version_tag=version_in.version_tag,
                base_model=version_in.base_model,
                model_format=version_in.model_format,
                metadata_info=version_in.metadata_info,
                is_ready=True
            )
            db.add(db_obj)
            await db.flush() # Get ID
            
            # 2. Link Artifacts
            for art in artifacts:
                artifact_obj = ModelArtifact(
                    model_version_id=db_obj.id,
                    artifact_type=art.get("artifact_type"),
                    s3_uri=art.get("s3_uri"),
                    file_size_bytes=art.get("file_size_bytes", 0),
                    sha256_hash=art.get("sha256_hash")
                )
                db.add(artifact_obj)
                
            await db.commit()
            await db.refresh(db_obj)
            
            logger.info(f"Registered Model Version {db_obj.version_tag} for model {db_obj.registered_model_id}")
            return db_obj

registry_service = ModelRegistryService()
