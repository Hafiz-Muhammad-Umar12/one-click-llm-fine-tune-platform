import uuid
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from opentelemetry import trace

from src.models.dataset import DatasetVersion, DatasetTrainingContract, Dataset
from src.datasets.validators.readiness import TrainingReadinessValidator
from src.datasets.economics.estimator import GPUCostEstimator
from src.datasets.schemas.readiness import ReadinessDecision
from src.exceptions.base import BaseAPIException

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class FailurePreventionException(BaseAPIException):
    def __init__(self, detail: str, report: Dict[str, Any]):
        super().__init__(status_code=400, detail=detail)
        self.report = report

class DatasetContractService:
    """
    Enterprise Contract Service.
    Enforces the strict boundary between Data and Training.
    Implements Failure Prevention by blocking unsafe contracts.
    """
    def __init__(self):
        self.estimator = GPUCostEstimator()

    async def create_contract(
        self, 
        db: AsyncSession, 
        *, 
        dataset_version_id: uuid.UUID,
        tokenizer_name: str,
        max_seq_length: int,
        training_method: str = "qlora"
    ) -> DatasetTrainingContract:
        
        with tracer.start_as_current_span("create_training_contract") as span:
            # 1. Load Data
            version = await db.get(DatasetVersion, dataset_version_id)
            if not version:
                raise ValueError("Dataset version not found")
            dataset = await db.get(Dataset, version.dataset_id)

            # 2. Failure Prevention: Readiness Validation
            validator = TrainingReadinessValidator(tokenizer_name, max_seq_length)
            report = validator.validate(version.statistics)
            
            if report.overall_decision == ReadinessDecision.BLOCK:
                logger.error(f"Contract blocked for version {dataset_version_id}: {report.recommendations}")
                raise FailurePreventionException(
                    detail="Dataset is not training-ready. High risk of failure detected.",
                    report=report.model_dump()
                )

            # 3. Compute Economic Guardrails
            total_tokens = version.statistics.get("count", 0) * version.statistics.get("mean", 0)
            estimates = self.estimator.estimate(
                total_tokens=int(total_tokens),
                max_seq_length=max_seq_length,
                base_model=tokenizer_name,
                method=training_method
            )

            # 4. Generate Immutable Lineage Hash
            # We hash the data source + the tokenizer + the max_length + preprocessing steps
            lineage_payload = {
                "version_id": str(version.id),
                "tokenizer": tokenizer_name,
                "max_seq_length": max_seq_length,
                "pipeline": version.statistics.get("lineage", {})
            }
            config_hash = hashlib.sha256(
                json.dumps(lineage_payload, sort_keys=True).encode()
            ).hexdigest()

            # 5. Commit Immutable Contract
            contract = DatasetTrainingContract(
                dataset_version_id=dataset_version_id,
                tokenizer_name=tokenizer_name,
                max_seq_length=max_seq_length,
                format_type=dataset.base_format,
                preprocessing_hash=config_hash,
                is_ready=True,
                validation_report=report.model_dump(),
                economic_estimates=estimates.model_dump()
            )
            
            db.add(contract)
            await db.commit()
            await db.refresh(contract)
            
            logger.info(f"Contract {contract.id} created successfully with hash {config_hash[:8]}")
            return contract

dataset_contract_service = DatasetContractService()
