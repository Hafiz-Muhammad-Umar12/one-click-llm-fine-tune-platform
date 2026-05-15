from pydantic import BaseModel
from typing import Dict, Any

class EconomicEstimate(BaseModel):
    estimated_vram_gb: float
    recommended_gpu: str
    estimated_duration_hours: float
    estimated_cost_usd: float
    suggested_batch_size: int
    gradient_accumulation_steps: int
    multi_gpu_required: bool
    assumptions: Dict[str, Any]
