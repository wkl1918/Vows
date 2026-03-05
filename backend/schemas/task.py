from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
import datetime

class TaskStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(str, Enum):
    TRANSLATE = "translate"
    DUBBING = "dubbing"

class TaskBase(BaseModel):
    filename: str
    original_language: Optional[str] = None
    target_language: str = "zh"

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: str
    status: TaskStatus
    progress: int = 0  # 0 to 100
    message: Optional[str] = None
    created_at: datetime.datetime
    result_path: Optional[str] = None

    class Config:
        from_attributes = True
