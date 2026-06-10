from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime

class BatchIsolateStatus(BaseModel):
    sample_id: UUID
    filename: str
    status: str
    current_stage: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class BatchResponse(BaseModel):
    batch_id: UUID
    project_id: UUID
    batch_name: Optional[str] = None
    total_isolates: int
    status: str
    completed: int
    failed: int
    running: int
    cohort_analysis_status: str
    isolates: List[BatchIsolateStatus]
    
    model_config = ConfigDict(from_attributes=True)

class CohortAnalysisResponse(BaseModel):
    batch_id: UUID
    cohort_analysis_status: str
    isolates_analyzed: int
    isolates_failed: int
    analyses: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)
