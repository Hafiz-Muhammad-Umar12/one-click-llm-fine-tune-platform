import json
import logging
from typing import List, Dict, Any, Optional, Iterator
from opentelemetry import trace
from src.datasets.tokenizers.manager import tokenizer_manager
from src.datasets.processors.pipeline import PipelineManager
from src.datasets.schemas.preview import PreviewItem, TokenDetail

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

class DatasetPreviewEngine:
    """
    Production-grade Dataset Preview Engine.
    Handles token-level analysis, truncation simulation, and pipeline transformation diffs.
    Memory footprint remains O(1) by operating on streams.
    """
    def __init__(self, tokenizer_name: str, max_seq_length: int, format_type: str, pipeline: Optional[PipelineManager] = None):
        self.tokenizer = tokenizer_manager.get_tokenizer(tokenizer_name)
        self.max_seq_length = max_seq_length
        self.format_type = format_type
        self.pipeline = pipeline

    def generate_preview(self, stream: Iterator[Dict[str, Any]], max_samples: int = 10) -> List[PreviewItem]:
        previews = []
        
        with tracer.start_as_current_span("generate_preview") as span:
            span.set_attribute("max_samples", max_samples)
            span.set_attribute("format_type", self.format_type)
            
            for index, raw_record in enumerate(stream):
                if index >= max_samples:
                    break
                    
                preview_item = self._process_single_record(index, raw_record)
                previews.append(preview_item)
                
        return previews

    def _process_single_record(self, index: int, raw_record: Dict[str, Any]) -> PreviewItem:
        with tracer.start_as_current_span("process_single_record"):
            try:
                # Apply pipeline if provided
                preprocessed_data = None
                target_record = raw_record
                
                if self.pipeline:
                    # Pipeline expects an iterator and yields. We wrap the single record.
                    results = list(self.pipeline.process_stream(iter([raw_record])))
                    if not results:
                        return PreviewItem(
                            index=index,
                            raw_data=raw_record,
                            formatted_text="",
                            tokens=[],
                            total_tokens=0,
                            truncated_tokens=0,
                            error="Record was dropped by preprocessing pipeline."
                        )
                    target_record = results[0]
                    preprocessed_data = target_record

                # Format
                formatted_text = self._format_record(target_record)
                
                # Tokenize
                token_ids = self.tokenizer.encode(formatted_text)
                total_tokens = len(token_ids)
                truncated_tokens = max(0, total_tokens - self.max_seq_length)
                
                # We limit the returned tokens to prevent massive JSON payloads (e.g. max 500 tokens for UI)
                display_tokens = []
                limit = min(total_tokens, 500)
                
                # Fast decoding map
                for i in range(limit):
                    tid = token_ids[i]
                    is_truncated = i >= self.max_seq_length
                    # Warning: decoding single tokens can be slightly off for some BPE edge cases, 
                    # but is generally sufficient for visual debugging.
                    text_val = self.tokenizer.decode([tid]) 
                    display_tokens.append(TokenDetail(id=tid, text=text_val, is_truncated=is_truncated))

                return PreviewItem(
                    index=index,
                    raw_data=raw_record,
                    preprocessed_data=preprocessed_data,
                    formatted_text=formatted_text,
                    tokens=display_tokens,
                    total_tokens=total_tokens,
                    truncated_tokens=truncated_tokens
                )

            except Exception as e:
                logger.error(f"Error previewing record {index}: {str(e)}", exc_info=True)
                return PreviewItem(
                    index=index,
                    raw_data=raw_record,
                    formatted_text=str(raw_record),
                    tokens=[],
                    total_tokens=0,
                    truncated_tokens=0,
                    error=f"Preview generation failed: {str(e)}"
                )

    def _format_record(self, record: Dict[str, Any]) -> str:
        """Transforms structured data into the flat string the model will actually see."""
        if self.format_type == "alpaca":
            instruction = record.get("instruction", "")
            input_text = record.get("input", "")
            output = record.get("output", "")
            if input_text:
                return f"Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.\n\n### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
            else:
                return f"Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\n{instruction}\n\n### Response:\n{output}"
        
        elif self.format_type == "chatml":
            messages = record.get("messages", [])
            formatted_chat = ""
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                formatted_chat += f"<|im_start|>{role}\n{content}<|im_end|>\n"
            return formatted_chat
            
        return json.dumps(record)
