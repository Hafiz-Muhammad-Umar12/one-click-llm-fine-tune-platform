import asyncio
from typing import Any
from src.core.celery_app import celery_app
from src.datasets.services.dataset import dataset_service
from src.datasets.parsers.jsonl import JSONLParser
from src.datasets.validators.dataset_validator import DatasetValidator
from src.db.session import SessionLocal
from src.models.dataset import DatasetVersion, DatasetStatus, Dataset

@celery_app.task(name="validate_dataset_task")
def validate_dataset_task(dataset_version_id: str):
    """
    Async task to validate dataset structure and content.
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_validate_dataset(dataset_version_id))

async def _validate_dataset(dataset_version_id: str):
    async with SessionLocal() as db:
        # 1. Fetch Version
        from src.datasets.repositories.dataset import dataset_version_repo
        version = await dataset_version_repo.get(db, id=dataset_version_id)
        if not version:
            return

        # 2. Download File
        storage = dataset_service.storage
        file_stream = await storage.download_file(version.s3_uri)
        content = file_stream.read()
        
        # 3. Parse
        parser = JSONLParser()
        data = parser.parse(content)
        
        # 4. Validate based on dataset format
        dataset = await db.get(Dataset, version.dataset_id)
        validator = DatasetValidator()
        
        if dataset.base_format == "alpaca":
            report = validator.validate_alpaca(data)
        elif dataset.base_format == "chatml":
            report = validator.validate_chatml(data)
        else:
            report = None # Handle other formats
            
        # 5. Update Status
        if report and report.is_valid:
            version.status = DatasetStatus.READY
            version.statistics = report.stats
        else:
            version.status = DatasetStatus.FAILED
            version.metadata_info["validation_errors"] = report.errors if report else ["Unknown format"]
            
        await db.commit()
