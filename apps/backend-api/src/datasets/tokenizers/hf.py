from typing import List
from transformers import AutoTokenizer
from src.datasets.tokenizers.base import BaseTokenizer

class HFTokenizer(BaseTokenizer):
    def __init__(self, model_name: str):
        self._name = model_name
        # use_fast=True leverages Rust implementation for massive speedup
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

    def encode(self, text: str) -> List[int]:
        return self.tokenizer.encode(text, add_special_tokens=False)

    def decode(self, tokens: List[int]) -> str:
        return self.tokenizer.decode(tokens, skip_special_tokens=True)

    def count_tokens(self, text: str) -> int:
        # Fast tokenizer length calculation without generating full lists if optimized
        return len(self.encode(text))

    @property
    def name(self) -> str:
        return self._name
