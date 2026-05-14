from typing import List, Dict, Any, Optional
import json
from src.datasets.tokenizers.manager import tokenizer_manager

class DatasetPreviewEngine:
    """
    Enterprise Preview Engine for visual debugging of datasets before training.
    Supports formatted chat views, token-level highlighting, and truncation simulation.
    """
    def __init__(self, tokenizer_name: str = "meta-llama/Llama-3-8b"):
        self.tokenizer = tokenizer_manager.get_tokenizer(tokenizer_name)

    def get_preview(self, data: List[Dict[str, Any]], format_type: str, max_samples: int = 5) -> List[Dict[str, Any]]:
        previews = []
        for i, record in enumerate(data[:max_samples]):
            preview_item = {
                "raw": record,
                "formatted": self._format_for_display(record, format_type),
                "tokens": self._get_token_details(record, format_type),
                "token_count": self._count_tokens(record, format_type)
            }
            previews.append(preview_item)
        return previews

    def _format_for_display(self, record: Dict[str, Any], format_type: str) -> str:
        if format_type == "alpaca":
            instruction = record.get("instruction", "")
            input_text = record.get("input", "")
            output = record.get("output", "")
            return f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
        
        elif format_type == "chatml":
            messages = record.get("messages", [])
            formatted_chat = ""
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                formatted_chat += f"<|im_start|>{role}\n{content}<|im_end|>\n"
            return formatted_chat
        
        return json.dumps(record, indent=2)

    def _get_token_details(self, record: Dict[str, Any], format_type: str) -> List[Dict[str, Any]]:
        """
        Returns a list of token strings and their IDs for UI highlighting.
        """
        text = self._format_for_display(record, format_type)
        token_ids = self.tokenizer.encode(text)
        # Note: True token-to-string mapping can be complex with fast tokenizers, 
        # for preview we simplify.
        return [{"id": tid, "token": self.tokenizer.decode([tid])} for tid in token_ids[:100]] # Limit for UI

    def _count_tokens(self, record: Dict[str, Any], format_type: str) -> int:
        text = self._format_for_display(record, format_type)
        return self.tokenizer.count_tokens(text)
