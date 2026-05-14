from typing import List, Dict, Any, Iterator
from src.datasets.processors.base import BasePreprocessor
import logging

logger = logging.getLogger(__name__)

class PipelineManager:
    """
    Manages a sequence of preprocessors. 
    Processes data as a stream to maintain O(1) memory complexity.
    """
    def __init__(self, steps: List[BasePreprocessor]):
        self.steps = steps
        self.stats = {step.name: 0 for step in steps}
        self.records_processed = 0
        self.records_dropped = 0

    def process_stream(self, stream: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """
        Takes a generator of records, passes each through the pipeline.
        Yields records that survive all steps.
        """
        for record in stream:
            self.records_processed += 1
            current_record = record
            
            for step in self.steps:
                try:
                    current_record = step.process(current_record)
                    if current_record is None:
                        self.stats[step.name] += 1
                        self.records_dropped += 1
                        break # Record filtered out, skip remaining steps
                except Exception as e:
                    logger.error(f"Error in pipeline step {step.name}: {str(e)}")
                    current_record = None
                    self.records_dropped += 1
                    break
            
            if current_record is not None:
                yield current_record

    def get_lineage_report(self) -> Dict[str, Any]:
        return {
            "pipeline_steps": [step.name for step in self.steps],
            "total_processed": self.records_processed,
            "total_dropped": self.records_dropped,
            "dropped_by_step": self.stats
        }
