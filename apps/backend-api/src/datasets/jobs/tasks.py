import asyncio
import json
import logging
from typing import Any
from src.core.celery_app import celery_app
from src.datasets.services.dataset import dataset_service
from src.db.session import SessionLocal
from src.models.dataset import DatasetVersion, DatasetStatus, Dataset

# Import Enterprise Modules
from src.datasets.tokenizers.manager import tokenizer_manager
from src.datasets.statistics.streaming import StreamingStatisticsEngine
from src.datasets.processors.pipeline import PipelineManager
from src.datasets.processors.deduplicator import MinHashDeduplicator
from src.websocket.manager import manager

logger = logging.getLogger(__name__)

# To use broadcaster in Celery, we need our own event loop or just use a sync Redis client.
# For simplicity in this demo, we'll mock the broadcast in the worker if broadcaster fails outside ASGI.
import redis
redis_client = redis.from_url("redis://localhost:6379/0")

def broadcast_progress(room_name: str, event_type: str, data: dict):
    payload = json.dumps({"type": event_type, "data": data})
    redis_client.publish(room_name, payload)

@celery_app.task(name="process_dataset_task", bind=True, max_retries=3)
def process_dataset_task(self, dataset_version_id: str):
    """
    Enterprise Async Task:
    1. Streams dataset line-by-line (O(1) memory).
    2. Runs through PipelineManager (Deduplication, etc).
    3. Tokenizes on-the-fly using cached TokenizerManager.
    4. Computes streaming statistics.
    5. Broadcasts progress via Redis WebSockets.
    """
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(_process_dataset(dataset_version_id))
    except Exception as exc:
        logger.error(f"Dataset processing failed: {exc}")
        self.retry(exc=exc, countdown=60) # Exponential backoff in production

async def _process_dataset(dataset_version_id: str):
    async with SessionLocal() as db:
        from src.datasets.repositories.dataset import dataset_version_repo
        version = await dataset_version_repo.get(db, id=dataset_version_id)
        if not version:
            return

        dataset = await db.get(Dataset, version.dataset_id)
        room_name = f"org:{dataset.organization_id}:dataset:{dataset.id}"
        
        broadcast_progress(room_name, "status_update", {"status": "Initializing Engine..."})

        # 1. Setup Tokenizer
        # In a real app, base_model would be chosen by user. Defaulting to Llama-3 here.
        tokenizer = tokenizer_manager.get_tokenizer("meta-llama/Llama-3-8b")
        
        # 2. Setup Statistics & Pipeline
        stats_engine = StreamingStatisticsEngine()
        
        # Determine target keys based on format
        target_keys = ["instruction", "output"] if dataset.base_format == "alpaca" else ["messages"]
        pipeline = PipelineManager([
            MinHashDeduplicator(target_keys=target_keys)
        ])

        # 3. Stream File (O(1) Memory)
        storage = dataset_service.storage
        file_stream = await storage.download_file(version.s3_uri)
        
        def line_generator():
            for line in file_stream:
                if line.strip():
                    yield json.loads(line)

        broadcast_progress(room_name, "status_update", {"status": "Processing Stream..."})

        processed_count = 0
        
        # Process through pipeline
        for valid_record in pipeline.process_stream(line_generator()):
            # Tokenize & Stats
            # For simplicity, just convert record to string. Real app formats properly first.
            text_content = json.dumps(valid_record)
            token_count = tokenizer.count_tokens(text_content)
            stats_engine.update(token_count)
            
            processed_count += 1
            if processed_count % 1000 == 0:
                # Heartbeat progress
                broadcast_progress(room_name, "progress", {
                    "processed": processed_count,
                    "dropped": pipeline.records_dropped,
                    "current_mean_tokens": stats_engine.mean
                })

        # 4. Finalize
        report = stats_engine.get_report()
        report["lineage"] = pipeline.get_lineage_report()
        
        version.status = DatasetStatus.READY
        version.statistics = report
        await db.commit()
        
        broadcast_progress(room_name, "status_update", {
            "status": "Completed", 
            "final_stats": report
        })
