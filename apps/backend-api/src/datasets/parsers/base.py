from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_content: Any) -> List[Dict[str, Any]]:
        """Parses file content into a list of dictionaries."""
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        pass
