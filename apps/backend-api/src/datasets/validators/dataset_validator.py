from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ValidationReport(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {}

class DatasetValidator:
    def validate_alpaca(self, data: List[Dict[str, Any]]) -> ValidationReport:
        errors = []
        required_keys = {"instruction", "output"}
        
        for i, entry in enumerate(data):
            keys = set(entry.keys())
            if not required_keys.issubset(keys):
                errors.append(f"Row {i} is missing required keys: {required_keys - keys}")
        
        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            stats={"total_rows": len(data)}
        )

    def validate_chatml(self, data: List[Dict[str, Any]]) -> ValidationReport:
        errors = []
        # ChatML structure: {"messages": [{"role": "user", "content": "..."}]}
        for i, entry in enumerate(data):
            if "messages" not in entry:
                errors.append(f"Row {i} is missing 'messages' key")
                continue
            
            messages = entry["messages"]
            if not isinstance(messages, list):
                errors.append(f"Row {i} 'messages' must be a list")
                continue
                
            for j, msg in enumerate(messages):
                if not all(k in msg for k in ("role", "content")):
                    errors.append(f"Row {i}, Message {j} is missing 'role' or 'content'")
        
        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            stats={"total_rows": len(data)}
        )
