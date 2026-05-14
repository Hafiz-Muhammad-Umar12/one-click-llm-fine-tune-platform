import pytest
from src.datasets.processors.pipeline import PipelineManager
from src.datasets.processors.deduplicator import ExactDeduplicator, MinHashDeduplicator

def test_exact_deduplicator():
    records = [
        {"instruction": "What is AI?", "output": "AI is artificial intelligence."},
        {"instruction": "What is AI?", "output": "AI is artificial intelligence."}, # Exact duplicate
        {"instruction": "What is ML?", "output": "Machine learning."}
    ]
    
    deduper = ExactDeduplicator(target_keys=["instruction", "output"])
    pipeline = PipelineManager([deduper])
    
    # Needs to be a generator
    result = list(pipeline.process_stream(iter(records)))
    
    assert len(result) == 2
    assert pipeline.records_processed == 3
    assert pipeline.records_dropped == 1

def test_streaming_stats():
    from src.datasets.statistics.streaming import StreamingStatisticsEngine
    stats = StreamingStatisticsEngine()
    
    for val in [10, 20, 30, 40, 50]:
        stats.update(val)
        
    report = stats.get_report()
    assert report["count"] == 5
    assert report["mean"] == 30.0
    assert report["min"] == 10
    assert report["max"] == 50
