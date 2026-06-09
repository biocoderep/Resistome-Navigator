"""Standard algorithm result model"""

from dataclasses import dataclass, field
from typing import Any, Dict
from datetime import datetime

@dataclass
class AlgorithmResult:
    algorithm: str
    algorithm_version: str
    inputs: Dict[str, Any]
    metrics: Dict[str, Any]
    score: float
    confidence: float
    executed_at: datetime = field(default_factory=datetime.utcnow)
    execution_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
