import uuid
import datetime
from typing import Dict, Optional
from schemas.task import TaskResponse, TaskStatus, TaskCreate

# In-memory store for tasks (Database replacement for local version)
tasks_db: Dict[str, TaskResponse] = {}

class TaskManager:
    @staticmethod
    def create_task(task_in: TaskCreate) -> TaskResponse:
        task_id = str(uuid.uuid4())
        new_task = TaskResponse(
            id=task_id,
            filename=task_in.filename,
            original_language=task_in.original_language,
            target_language=task_in.target_language,
            status=TaskStatus.QUEUED,
            created_at=datetime.datetime.now(),
            progress=0,
            message="Task initialized"
        )
        tasks_db[task_id] = new_task
        return new_task

    @staticmethod
    def get_task(task_id: str) -> Optional[TaskResponse]:
        return tasks_db.get(task_id)

    @staticmethod
    def list_tasks():
        return list(tasks_db.values())

    @staticmethod
    def update_status(task_id: str, status: TaskStatus, progress: int = None, message: str = None):
        if task_id in tasks_db:
            tasks_db[task_id].status = status
            if progress is not None:
                tasks_db[task_id].progress = progress
            if message:
                tasks_db[task_id].message = message
