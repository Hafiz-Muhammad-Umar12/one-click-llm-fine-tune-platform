import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.deployment import InferenceMetrics
from src.repositories.base import BaseRepository

class InferenceMetricsRepository(BaseRepository[InferenceMetrics, Any, Any]):
    async def get_recent_metrics(
        self, db: AsyncSession, endpoint_id: uuid.UUID, minutes: int = 60
    ) -> List[InferenceMetrics]:
        since = datetime.utcnow() - timedelta(minutes=minutes)
        query = (
            select(self.model)
            .where(self.model.endpoint_id == endpoint_id)
            .where(self.model.timestamp >= since)
            .order_by(self.model.timestamp.asc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_aggregated_stats(
        self, db: AsyncSession, endpoint_id: uuid.UUID, minutes: int = 60
    ) -> Dict[str, Any]:
        since = datetime.utcnow() - timedelta(minutes=minutes)
        query = (
            select(
                func.sum(self.model.total_requests).label("total_requests"),
                func.avg(self.model.avg_latency_ms).label("avg_latency"),
                func.avg(self.model.avg_ttft_ms).label("avg_ttft"),
                func.sum(self.model.error_count).label("total_errors")
            )
            .where(self.model.endpoint_id == endpoint_id)
            .where(self.model.timestamp >= since)
        )
        result = await db.execute(query)
        row = result.first()
        return {
            "total_requests": row.total_requests or 0,
            "avg_latency_ms": float(row.avg_latency or 0),
            "avg_ttft_ms": float(row.avg_ttft or 0),
            "total_errors": row.total_errors or 0,
            "success_rate": 1.0 - (row.total_errors / row.total_requests) if row.total_requests and row.total_requests > 0 else 1.0
        }

metrics_repo = InferenceMetricsRepository(InferenceMetrics)

class MetricsService:
    async def record_metrics(
        self, db: AsyncSession, endpoint_id: uuid.UUID, metrics_data: Dict[str, Any]
    ) -> InferenceMetrics:
        db_obj = InferenceMetrics(
            endpoint_id=endpoint_id,
            timestamp=datetime.utcnow(),
            total_requests=metrics_data.get("total_requests", 1),
            avg_latency_ms=metrics_data.get("avg_latency_ms", 0.0),
            avg_ttft_ms=metrics_data.get("avg_ttft_ms", 0.0),
            avg_tpot_ms=metrics_data.get("avg_tpot_ms", 0.0),
            error_count=metrics_data.get("error_count", 0)
        )
        db.add(db_obj)
        await db.commit()
        return db_obj

    async def get_endpoint_stats(
        self, db: AsyncSession, endpoint_id: uuid.UUID, minutes: int = 60
    ) -> Dict[str, Any]:
        return await metrics_repo.get_aggregated_stats(db, endpoint_id, minutes=minutes)

metrics_service = MetricsService()
