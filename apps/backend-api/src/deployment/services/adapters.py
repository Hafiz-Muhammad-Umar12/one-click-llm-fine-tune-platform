import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.deployment import ModelArtifact, ModelVersion
from src.deployment.repositories.registry import model_artifact_repo, model_version_repo

logger = logging.getLogger(__name__)

class AdapterService:
    """
    Handles management of LoRA adapters for dynamic serving.
    """
    async def get_adapters_for_version(
        self, db: AsyncSession, version_id: uuid.UUID
    ) -> List[ModelArtifact]:
        artifacts = await model_artifact_repo.get_by_version(db, version_id)
        return [a for a in artifacts if a.artifact_type in ["adapter_model", "adapter_config"]]

    async def prepare_adapter_manifest(
        self, db: AsyncSession, version_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Prepares a manifest that the inference pod can use to load a LoRA adapter.
        """
        version = await model_version_repo.get(db, version_id)
        if not version or version.model_format != "lora":
            return {}
            
        adapters = await self.get_adapters_for_version(db, version_id)
        
        return {
            "version_id": str(version_id),
            "base_model": version.base_model,
            "adapter_type": "lora",
            "artifacts": [
                {"type": a.artifact_type, "uri": a.s3_uri} for a in adapters
            ]
        }

adapter_service = AdapterService()
