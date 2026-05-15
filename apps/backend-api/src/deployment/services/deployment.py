import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from opentelemetry import trace

from src.models.deployment import DeploymentEndpoint, DeploymentRevision, ModelVersion
from src.deployment.repositories.deployment import (
    deployment_endpoint_repo,
    deployment_revision_repo
)
from src.deployment.services.registry import registry_service
from src.deployment.schemas.deployment import DeploymentCreate, DeploymentResponse

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class DeploymentService:
    """
    Orchestrates the lifecycle of deployment endpoints.
    Handles creation, updates, and rollbacks.
    """
    async def create_deployment(
        self, db: AsyncSession, organization_id: uuid.UUID, deployment_in: DeploymentCreate
    ) -> DeploymentEndpoint:
        with tracer.start_as_current_span("create_deployment"):
            # 1. Verify Model Version exists
            version = await registry_service.get_model_version(db, deployment_in.model_version_id)
            if not version:
                raise ValueError("Model Version not found")

            # 2. Create Endpoint
            endpoint = DeploymentEndpoint(
                organization_id=organization_id,
                model_version_id=deployment_in.model_version_id,
                name=deployment_in.name,
                hardware_tier=deployment_in.hardware_tier,
                target_replica_count=deployment_in.target_replica_count,
                autoscaling_config=deployment_in.autoscaling_config,
                status="deploying"
            )
            db.add(endpoint)
            await db.flush() # Get ID

            # 3. Create initial Revision
            revision = DeploymentRevision(
                endpoint_id=endpoint.id,
                revision_number=1,
                model_version_id=endpoint.model_version_id,
                config_snapshot={
                    "hardware_tier": endpoint.hardware_tier,
                    "target_replica_count": endpoint.target_replica_count,
                    "autoscaling_config": endpoint.autoscaling_config
                }
            )
            db.add(revision)
            
            await db.commit()
            await db.refresh(endpoint)

            # 4. Trigger K8s Orchestration (to be implemented)
            # await k8s_orchestrator.deploy_endpoint(endpoint)
            
            logger.info(f"Created Deployment Endpoint {endpoint.id} for organization {organization_id}")
            return endpoint

    async def get_deployments(
        self, db: AsyncSession, organization_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[DeploymentEndpoint]:
        return await deployment_endpoint_repo.get_by_org(db, organization_id, skip=skip, limit=limit)

    async def get_deployment(
        self, db: AsyncSession, endpoint_id: uuid.UUID
    ) -> Optional[DeploymentEndpoint]:
        return await deployment_endpoint_repo.get(db, endpoint_id)

    async def rollback_deployment(
        self, db: AsyncSession, endpoint_id: uuid.UUID, to_revision_id: uuid.UUID, reason: str
    ) -> DeploymentEndpoint:
        """
        Rolls back an endpoint to a specific historical revision.
        """
        with tracer.start_as_current_span("rollback_deployment"):
            endpoint = await self.get_deployment(db, endpoint_id)
            if not endpoint:
                raise ValueError("Endpoint not found")
                
            revision = await deployment_revision_repo.get(db, to_revision_id)
            if not revision or revision.endpoint_id != endpoint_id:
                raise ValueError("Revision not found or mismatch")

            # Update endpoint with revision config
            endpoint.model_version_id = revision.model_version_id
            endpoint.hardware_tier = revision.config_snapshot.get("hardware_tier", endpoint.hardware_tier)
            endpoint.target_replica_count = revision.config_snapshot.get("target_replica_count", endpoint.target_replica_count)
            endpoint.autoscaling_config = revision.config_snapshot.get("autoscaling_config", endpoint.autoscaling_config)
            endpoint.status = "deploying"
            
            db.add(endpoint)
            await db.commit()
            await db.refresh(endpoint)
            
            # Trigger K8s Rollout
            # await k8s_orchestrator.deploy_endpoint(endpoint)
            
            return endpoint

deployment_service = DeploymentService()
