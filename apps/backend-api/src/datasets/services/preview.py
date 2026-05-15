import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.models.dataset import DatasetVersion, Dataset
from src.datasets.services.dataset import dataset_service
from src.datasets.parsers.jsonl import JSONLParser
from src.datasets.preview.engine import DatasetPreviewEngine
from src.datasets.schemas.preview import PreviewResponse

class PreviewService:
    async def get_preview(
        self,
        db: AsyncSession,
        version_id: uuid.UUID,
        tokenizer_name: str,
        max_seq_length: int,
        max_samples: int = 10
    ) -> PreviewResponse:
        version = await db.get(DatasetVersion, version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Dataset version not found")
        
        dataset = await db.get(Dataset, version.dataset_id)
        
        # Stream file instead of full read
        storage = dataset_service.storage
        file_stream = await storage.download_file(version.s3_uri)
        
        # Create an iterator over the stream
        def record_generator():
            for line in file_stream:
                if line.strip():
                    # If parser handles lines, use it, or just parse json directly here
                    yield json.loads(line)
        
        engine = DatasetPreviewEngine(
            tokenizer_name=tokenizer_name,
            max_seq_length=max_seq_length,
            format_type=dataset.base_format
            # Optional: instantiate pipeline based on lineage config
        )
        
        previews = engine.generate_preview(record_generator(), max_samples=max_samples)
        
        return PreviewResponse(
            dataset_id=str(dataset.id),
            version_id=str(version.id),
            tokenizer_name=tokenizer_name,
            max_seq_length=max_seq_length,
            samples=previews,
            pipeline_hash=None
        )

preview_service = PreviewService()
