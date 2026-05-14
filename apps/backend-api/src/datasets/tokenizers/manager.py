import threading
from functools import lru_cache
import logging
from src.datasets.tokenizers.base import BaseTokenizer
from src.datasets.tokenizers.hf import HFTokenizer

logger = logging.getLogger(__name__)

class TokenizerManager:
    """
    Enterprise Tokenizer Registry & Manager.
    Implements a thread-safe LRU cache to prevent worker OOM errors when processing
    datasets meant for different base models on the same worker.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TokenizerManager, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self._cache_lock = threading.Lock()
        # Bound cache to top 5 models to preserve worker RAM.
        # Evicted tokenizers are garbage collected.
        self._max_cache_size = 5 

    @lru_cache(maxsize=5)
    def _load_tokenizer(self, model_name: str) -> BaseTokenizer:
        """
        Inner cached method. Python's functools.lru_cache is thread-safe natively.
        """
        logger.info(f"Loading tokenizer into memory: {model_name}")
        
        # Dispatch logic: if it's an OpenAI model use tiktoken, else assume HF.
        if model_name.startswith("gpt-") or model_name.startswith("text-embedding"):
            # Would be OpenAITokenizer(model_name)
            pass 
        
        return HFTokenizer(model_name)

    def get_tokenizer(self, model_name: str) -> BaseTokenizer:
        """
        Thread-safe lazy loading of tokenizers.
        """
        with self._cache_lock:
            return self._load_tokenizer(model_name)

    def warmup(self, models: list[str]):
        """Pre-loads common tokenizers during worker startup."""
        for model in models:
            self.get_tokenizer(model)

tokenizer_manager = TokenizerManager()
