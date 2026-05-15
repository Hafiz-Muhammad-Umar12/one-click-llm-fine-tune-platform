import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.dataset import Dataset, DatasetVersion, DatasetTrainingContract
from src.models.training import TrainingRun

class LineageService:
    """
    Reconstructs the immutable lineage of AI assets.
    Provides the audit trail for data-to-model transformations.
    """
    async def get_run_lineage(self, db: AsyncSession, run_id: uuid.UUID) -> Dict[str, Any]:
        # 1. Start at Training Run
        run = await db.get(TrainingRun, run_id)
        if not run:
            return {"error": "Run not found"}

        # 2. Resolve Contract
        contract = await db.get(DatasetTrainingContract, run.contract_id)
        
        # 3. Resolve Version
        version = await db.get(DatasetVersion, contract.dataset_version_id)
        
        # 4. Resolve Dataset
        dataset = await db.get(Dataset, version.dataset_id)

        # 5. Build Graph
        return {
            "run": {
                "id": str(run.id),
                "name": run.name,
                "status": run.status,
                "config": run.training_config
            },
            "contract": {
                "id": str(contract.id),
                "hash": contract.preprocessing_hash,
                "tokenizer": contract.tokenizer_name,
                "max_seq_length": contract.max_seq_length,
                "readiness": contract.validation_report
            },
            "version": {
                "id": str(version.id),
                "number": version.version_number,
                "uri": version.s3_uri,
                "stats": version.statistics
            },
            "dataset": {
                "id": str(dataset.id),
                "name": dataset.name,
                "format": dataset.base_format
            },
            "lineage_hash": contract.preprocessing_hash # The anchor of truth
        }

lineage_service = LineageService()
