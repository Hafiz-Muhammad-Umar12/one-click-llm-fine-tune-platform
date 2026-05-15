from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TokenDetail(BaseModel):
    id: int
    text: str
    is_truncated: bool

class PreviewItem(BaseModel):
    index: int
    raw_data: Dict[str, Any]
    preprocessed_data: Optional[Dict[str, Any]] = None
    formatted_text: str
    tokens: List[TokenDetail]
    total_tokens: int
    truncated_tokens: int
    error: Optional[str] = None

class PreviewResponse(BaseModel):
    dataset_id: str
    version_id: str
    tokenizer_name: str
    max_seq_length: int
    samples: List[PreviewItem]
    pipeline_hash: Optional[str] = None
