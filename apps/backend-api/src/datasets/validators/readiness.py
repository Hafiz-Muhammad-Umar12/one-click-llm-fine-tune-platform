from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from src.datasets.tokenizers.manager import tokenizer_manager

class ReadinessReport(BaseModel):
    is_ready: bool
    status: str # ALLOW, WARN, BLOCK
    checks: Dict[str, Any]
    recommendations: List[str]

class TrainingReadinessValidator:
    """
    Strict validator for ensuring a dataset is safe and optimized for GPU training.
    """
    def __init__(self, tokenizer_name: str, max_seq_length: int):
        self.tokenizer = tokenizer_manager.get_tokenizer(tokenizer_name)
        self.max_seq_length = max_seq_length

    def validate(self, statistics: Dict[str, Any]) -> ReadinessReport:
        checks = {}
        recommendations = []
        is_ready = True
        status = "ALLOW"

        # 1. Truncation Risk Check
        max_tokens = statistics.get("max", 0)
        truncation_rate = statistics.get("histogram", {}).get(f"{self.max_seq_length}+", 0)
        
        if max_tokens > self.max_seq_length:
            checks["truncation_risk"] = "HIGH"
            recommendations.append(f"Max tokens ({max_tokens}) exceeds context length ({self.max_seq_length}). {truncation_rate} samples will be truncated.")
            status = "WARN"
        else:
            checks["truncation_risk"] = "LOW"

        # 2. Dataset Size Check
        total_samples = statistics.get("count", 0)
        if total_samples < 50:
            checks["dataset_size"] = "CRITICALLY_SMALL"
            recommendations.append("Dataset is very small (< 50 samples). Fine-tuning may lead to overfitting or poor results.")
            status = "WARN"
        else:
            checks["dataset_size"] = "OK"

        # 3. Format Sanity (from stats)
        if statistics.get("lineage", {}).get("total_dropped", 0) > (total_samples * 0.2):
            checks["data_quality"] = "POOR"
            recommendations.append("More than 20% of records were dropped during preprocessing. Check your raw data quality.")
            is_ready = False
            status = "BLOCK"
        else:
            checks["data_quality"] = "OK"

        return ReadinessReport(
            is_ready=is_ready,
            status=status,
            checks=checks,
            recommendations=recommendations
        )
