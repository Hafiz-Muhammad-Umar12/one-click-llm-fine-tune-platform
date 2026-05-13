import json
from typing import Any, List, Dict
from src.datasets.parsers.base import BaseParser

class JSONLParser(BaseParser):
    def parse(self, file_content: Any) -> List[Dict[str, Any]]:
        data = []
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8')
            
        for line in file_content.splitlines():
            if line.strip():
                data.append(json.loads(line))
        return data

    def get_supported_extensions(self) -> List[str]:
        return [".jsonl"]
