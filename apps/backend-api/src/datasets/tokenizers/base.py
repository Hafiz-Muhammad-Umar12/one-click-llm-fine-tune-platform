from abc import ABC, abstractmethod
from typing import List, Union

class BaseTokenizer(ABC):
    @abstractmethod
    def encode(self, text: str) -> List[int]:
        """Encodes text into a list of token IDs."""
        pass

    @abstractmethod
    def decode(self, tokens: List[int]) -> str:
        """Decodes token IDs back into text."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Efficiently counts tokens without returning the full list if possible."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name/identifier of the tokenizer."""
        pass
