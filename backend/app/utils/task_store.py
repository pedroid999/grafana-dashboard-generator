"""
In-memory task store for dashboard generation tasks.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from app.schemas.dashboard import DashboardTaskResponse, TaskResult

# Configure logging
logger = logging.getLogger(__name__)


class TaskStore:
    """
    Simple in-memory store for task status and results.
    """
    
    def __init__(self):
        self.tasks: Dict[str, DashboardTaskResponse] = {}
    
    def create_task(self) -> str:
        """
        Create a new task and return its ID.
        
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = DashboardTaskResponse(
            task_id=task_id,
            status="pending",
            error=None,
            result=None
        )
        logger.info(f"Created new task with ID: {task_id}")
        return task_id
    
    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> DashboardTaskResponse:
        """
        Update task status and result.
        
        Args:
            task_id: The ID of the task to update
            status: New status (pending, completed, failed)
            error: Error message if task failed
            result: Task result if completed
            
        Returns:
            Updated task
            
        Raises:
            KeyError: If task with given ID does not exist
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task with ID {task_id} not found")
            
        task = self.tasks[task_id]
        
        if status:
            task.status = status
            
        if error:
            task.error = error
            
        if result:
            task_result = TaskResult(**result)
            task.result = task_result
            
        logger.info(f"Updated task {task_id}: status={task.status}")
        return task
    
    def get(self, task_id: str) -> Optional[DashboardTaskResponse]:
        """
        Get task by ID.
        
        Args:
            task_id: The ID of the task to retrieve
            
        Returns:
            Task if found, None otherwise
        """
        return self.tasks.get(task_id)
    
    def delete(self, task_id: str) -> bool:
        """
        Delete task by ID.
        
        Args:
            task_id: The ID of the task to delete
            
        Returns:
            True if task was deleted, False if task was not found
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Deleted task {task_id}")
            return True
        return False


# Singleton instance
task_store = TaskStore() 