from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePreprocessor(ABC):
    """
    Interface for a single dataset preprocessing step.
    Must operate on a single record to support generator-based streaming pipelines.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def process(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a single record. 
        Returns the modified record, or None if the record should be dropped/filtered.
        """
        pass
