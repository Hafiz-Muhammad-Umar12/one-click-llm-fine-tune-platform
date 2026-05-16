import pytest
from unittest.mock import MagicMock, patch
from src.datasets.preview.engine import DatasetPreviewEngine
from src.datasets.validators.readiness import TrainingReadinessValidator, ReadinessDecision

@pytest.fixture(autouse=True)
def mock_tokenizer():
    with patch("src.datasets.tokenizers.hf.AutoTokenizer.from_pretrained") as mock:
        mock_instance = MagicMock()
        # Mock encode to return a list of tokens based on string length
        mock_instance.encode.side_effect = lambda x, **kwargs: [1] * (len(x) // 4 + 1)
        mock_instance.decode.return_value = "decoded text"
        mock.return_value = mock_instance
        yield mock

def test_preview_engine_alpaca():
    engine = DatasetPreviewEngine(tokenizer_name="meta-llama/Llama-3-8b", max_seq_length=512, format_type="alpaca")
    data = [{"instruction": "Explain quantum physics.", "output": "Quantum physics is..."}]
    
    previews = engine.generate_preview(iter(data))
    
    assert len(previews) == 1
    assert "### Instruction:" in previews[0].formatted_text
    assert previews[0].total_tokens > 0

def test_readiness_validator_block():
    # Simulate a dataset where average tokens exceed max context
    validator = TrainingReadinessValidator(tokenizer_name="meta-llama/Llama-3-8b", max_seq_length=128)
    stats = {
        "count": 100,
        "mean": 512, # Mean > max_seq_length (128) -> BLOCK
        "max": 1024,
        "lineage": {"total_dropped": 0}
    }
    
    report = validator.validate(stats)
    assert report.overall_decision == ReadinessDecision.BLOCK
    assert any("truncation_risk" in c.name for c in report.checks)

def test_readiness_validator_allow():
    validator = TrainingReadinessValidator(tokenizer_name="meta-llama/Llama-3-8b", max_seq_length=1024)
    stats = {
        "count": 500,
        "mean": 256,
        "max": 512,
        "lineage": {"total_dropped": 0}
    }
    
    report = validator.validate(stats)
    assert report.overall_decision == ReadinessDecision.ALLOW
