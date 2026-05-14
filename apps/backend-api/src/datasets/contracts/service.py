import uuid
import hashlib
import json
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.dataset import DatasetVersion, DatasetTrainingContract, Dataset
from src.datasets.validators.readiness import TrainingReadinessValidator
from src.datasets.economics.estimator import GPUCostEstimator

class DatasetContractService:
    """
    Service responsible for finalizing a dataset and creating the Training Contract.
    """
    async def finalize_version(
        self, 
        db: AsyncSession, 
        *, 
        dataset_version_id: uuid.UUID,
        tokenizer_name: str,
        max_seq_length: int
    ) -> DatasetTrainingContract:
        # 1. Fetch data
        version = await db.get(DatasetVersion, dataset_version_id)
        dataset = await db.get(Dataset, version.dataset_id)
        
        # 2. Run Readiness Validation
        validator = TrainingReadinessValidator(tokenizer_name, max_seq_length)
        readiness_report = validator.validate(version.statistics)
        
        # 3. Run Economic Estimation
        estimator = GPUCostEstimator()
        total_tokens = version.statistics.get("count", 0) * version.statistics.get("mean", 0)
        economic_estimates = estimator.estimate(
            total_tokens=int(total_tokens),
            max_seq_length=max_seq_length
        )
        
        # 4. Create Immutable Hash of preprocessing lineage
        lineage_str = json.dumps(version.statistics.get("lineage", {}), sort_keys=True)
        config_hash = hashlib.sha256(lineage_str.encode()).hexdigest()
        
        # 5. Save Contract
        contract = DatasetTrainingContract(
            dataset_version_id=dataset_version_id,
            tokenizer_name=tokenizer_name,
            max_seq_length=max_seq_length,
            format_type=dataset.base_format,
            preprocessing_hash=config_hash,
            is_ready=readiness_report.is_ready,
            validation_report=readiness_report.model_dump(),
            economic_estimates=economic_estimates
        )
        
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        return contract

dataset_contract_service = DatasetContractService()
