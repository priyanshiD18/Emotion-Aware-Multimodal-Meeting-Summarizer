"""
Task management for background processing
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages background task status and results"""
    
    def __init__(self):
        """Initialize task manager"""
        self.tasks: Dict[str, Dict] = {}
        self.results_dir = settings.output_dir / "tasks"
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def create_task(self, file_id: str) -> str:
        """
        Create a new task
        
        Args:
            file_id: Associated file ID
            
        Returns:
            Task ID
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_id[:8]}"
        
        self.tasks[task_id] = {
            "task_id": task_id,
            "file_id": file_id,
            "status": "pending",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "error": None
        }
        
        logger.info(f"Created task: {task_id}")
        return task_id
    
    def update_status(
        self,
        task_id: str,
        status: str,
        progress: Optional[int] = None,
        error: Optional[str] = None
    ):
        """
        Update task status
        
        Args:
            task_id: Task ID
            status: New status
            progress: Optional progress percentage
            error: Optional error message
        """
        if task_id not in self.tasks:
            logger.warning(f"Task not found: {task_id}")
            return
        
        self.tasks[task_id]["status"] = status
        self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        if progress is not None:
            self.tasks[task_id]["progress"] = progress
        
        if error is not None:
            self.tasks[task_id]["error"] = error
        
        logger.debug(f"Updated task {task_id}: status={status}, progress={progress}")
    
    def get_status(self, task_id: str) -> Optional[Dict]:
        """
        Get task status
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status dictionary or None
        """
        return self.tasks.get(task_id)
    
    def save_result(self, task_id: str, result: Dict[str, Any]):
        """
        Save task result to disk
        
        Args:
            task_id: Task ID
            result: Result dictionary
        """
        result_path = self.results_dir / f"{task_id}.json"
        
        try:
            with open(result_path, "w") as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"Saved result for task: {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to save result for {task_id}: {e}")
    
    def get_result(self, task_id: str) -> Optional[Dict]:
        """
        Get task result from disk
        
        Args:
            task_id: Task ID
            
        Returns:
            Result dictionary or None
        """
        result_path = self.results_dir / f"{task_id}.json"
        
        if not result_path.exists():
            logger.warning(f"Result not found for task: {task_id}")
            return None
        
        try:
            with open(result_path, "r") as f:
                result = json.load(f)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to load result for {task_id}: {e}")
            return None
    
    def cleanup_old_tasks(self, max_age_days: int = 7):
        """
        Cleanup old tasks and results
        
        Args:
            max_age_days: Maximum age of tasks to keep
        """
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        
        # Cleanup in-memory tasks
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            created_at = datetime.fromisoformat(task["created_at"]).timestamp()
            if created_at < cutoff_time:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        # Cleanup result files
        for result_file in self.results_dir.glob("*.json"):
            if result_file.stat().st_mtime < cutoff_time:
                result_file.unlink()
        
        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")

