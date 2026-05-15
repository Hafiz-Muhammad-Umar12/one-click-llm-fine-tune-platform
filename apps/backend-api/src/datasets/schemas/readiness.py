from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ReadinessDecision(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"

class ReadinessCheck(BaseModel):
    name: str
    decision: ReadinessDecision
    reason: str
    metrics: Dict[str, Any] = Field(default_factory=dict)

class ReadinessReport(BaseModel):
    is_ready: bool
    overall_decision: ReadinessDecision
    checks: List[ReadinessCheck]
    recommendations: List[str]
    
    @property
    def blocks(self) -> List[ReadinessCheck]:
        return [c for c in self.checks if c.decision == ReadinessDecision.BLOCK]
        
    @property
    def warnings(self) -> List[ReadinessCheck]:
        return [c for c in self.checks if c.decision == ReadinessDecision.WARN]
