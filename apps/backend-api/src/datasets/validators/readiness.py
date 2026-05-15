import logging
from typing import Dict, Any, List
from opentelemetry import trace

from src.datasets.tokenizers.manager import tokenizer_manager
from src.datasets.schemas.readiness import ReadinessReport, ReadinessCheck, ReadinessDecision

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class TrainingReadinessValidator:
    """
    Enterprise strict validator for ensuring a dataset is safe and optimized for GPU training.
    Evaluates O(1) streaming statistics to make a BLOCK/WARN/ALLOW decision.
    """
    def __init__(self, tokenizer_name: str, max_seq_length: int):
        self.tokenizer = tokenizer_manager.get_tokenizer(tokenizer_name)
        self.max_seq_length = max_seq_length

    def validate(self, statistics: Dict[str, Any]) -> ReadinessReport:
        with tracer.start_as_current_span("training_readiness_validation") as span:
            span.set_attribute("max_seq_length", self.max_seq_length)
            
            checks: List[ReadinessCheck] = []
            recommendations: List[str] = []
            
            # If stats are empty, block immediately.
            if not statistics or "count" not in statistics:
                return ReadinessReport(
                    is_ready=False,
                    overall_decision=ReadinessDecision.BLOCK,
                    checks=[ReadinessCheck(
                        name="statistics_presence", 
                        decision=ReadinessDecision.BLOCK, 
                        reason="Dataset statistics are missing or malformed."
                    )],
                    recommendations=["Ensure the dataset was fully processed and try again."]
                )

            # 1. Dataset Size Sanity
            self._check_dataset_size(statistics, checks, recommendations)
            
            # 2. Preprocessing Data Quality
            self._check_data_quality(statistics, checks, recommendations)
            
            # 3. Truncation and Token Explosion Risk
            self._check_truncation_risk(statistics, checks, recommendations)

            # Evaluate final status
            overall_decision = ReadinessDecision.ALLOW
            is_ready = True
            
            for check in checks:
                if check.decision == ReadinessDecision.BLOCK:
                    overall_decision = ReadinessDecision.BLOCK
                    is_ready = False
                    break
                elif check.decision == ReadinessDecision.WARN and overall_decision != ReadinessDecision.BLOCK:
                    overall_decision = ReadinessDecision.WARN

            span.set_attribute("readiness_decision", overall_decision.value)
            
            return ReadinessReport(
                is_ready=is_ready,
                overall_decision=overall_decision,
                checks=checks,
                recommendations=recommendations
            )

    def _check_dataset_size(self, stats: Dict[str, Any], checks: List[ReadinessCheck], recommendations: List[str]):
        count = stats.get("count", 0)
        if count < 50:
            checks.append(ReadinessCheck(
                name="dataset_size",
                decision=ReadinessDecision.WARN,
                reason=f"Dataset is critically small ({count} samples).",
                metrics={"count": count}
            ))
            recommendations.append("A dataset with fewer than 50 samples risks severe overfitting. Consider adding more data.")
        elif count > 5_000_000:
             checks.append(ReadinessCheck(
                name="dataset_size",
                decision=ReadinessDecision.WARN,
                reason=f"Dataset is extremely large ({count} samples).",
                metrics={"count": count}
            ))
             recommendations.append("For massive datasets, ensure you have sufficient budget allocated. Consider evaluating on a 10% split first.")
        else:
            checks.append(ReadinessCheck(
                name="dataset_size",
                decision=ReadinessDecision.ALLOW,
                reason="Dataset size is optimal.",
                metrics={"count": count}
            ))

    def _check_data_quality(self, stats: Dict[str, Any], checks: List[ReadinessCheck], recommendations: List[str]):
        total = stats.get("count", 0)
        dropped = stats.get("lineage", {}).get("total_dropped", 0)
        
        if total == 0 and dropped > 0:
            checks.append(ReadinessCheck(
                name="data_quality",
                decision=ReadinessDecision.BLOCK,
                reason="All records were dropped during preprocessing.",
                metrics={"dropped": dropped, "total": total}
            ))
            recommendations.append("Check your dataset format. The preprocessing pipeline filtered out 100% of the rows.")
            return

        drop_rate = dropped / (total + dropped) if (total + dropped) > 0 else 0
        if drop_rate > 0.20:
            checks.append(ReadinessCheck(
                name="data_quality",
                decision=ReadinessDecision.BLOCK,
                reason=f"High drop rate detected: {drop_rate:.1%}. More than 20% of data was invalid or duplicated.",
                metrics={"drop_rate": drop_rate}
            ))
            recommendations.append("Investigate the raw dataset. Large amounts of data are failing schema validation or deduplication.")
        else:
             checks.append(ReadinessCheck(
                name="data_quality",
                decision=ReadinessDecision.ALLOW,
                reason=f"Drop rate is acceptable ({drop_rate:.1%}).",
                metrics={"drop_rate": drop_rate}
            ))

    def _check_truncation_risk(self, stats: Dict[str, Any], checks: List[ReadinessCheck], recommendations: List[str]):
        max_tokens = stats.get("max", 0)
        mean_tokens = stats.get("mean", 0)
        
        if mean_tokens > self.max_seq_length:
            checks.append(ReadinessCheck(
                name="truncation_risk",
                decision=ReadinessDecision.BLOCK,
                reason=f"Average token length ({mean_tokens:.0f}) exceeds the configured max_seq_length ({self.max_seq_length}).",
                metrics={"mean_tokens": mean_tokens, "max_seq_length": self.max_seq_length}
            ))
            recommendations.append(f"Increase max_seq_length to at least {mean_tokens:.0f} to prevent severe structural corruption during training.")
        elif max_tokens > self.max_seq_length:
            # Check histogram to see *how much* is truncated
            histogram = stats.get("histogram", {})
            # A rough estimate using the buckets
            high_buckets = [v for k, v in histogram.items() if "+" in k or int(k.split("-")[1]) > self.max_seq_length if "-" in k]
            truncated_samples = sum(high_buckets)
            
            checks.append(ReadinessCheck(
                name="truncation_risk",
                decision=ReadinessDecision.WARN,
                reason=f"Max tokens ({max_tokens}) exceeds context length. Some samples will be truncated.",
                metrics={"max_tokens": max_tokens, "truncated_estimate": truncated_samples}
            ))
            recommendations.append(f"Ensure that truncation does not remove critical response labels at the end of the sequences.")
        else:
            checks.append(ReadinessCheck(
                name="truncation_risk",
                decision=ReadinessDecision.ALLOW,
                reason="No truncation risk detected. All samples fit within context length.",
                metrics={"max_tokens": max_tokens}
            ))
