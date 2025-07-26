"""
File-based progress store implementation for workflow state persistence.
"""
import os
import json
import shutil
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..models.interfaces import ProgressStore, StepStatus
from ..models.workflow_models import WorkflowState, StepResult
from ..utils.config import config


class FileProgressStore(ProgressStore):
    """File-based implementation of progress store."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the progress store with storage directory."""
        self.storage_dir = Path(storage_dir or config.get('progress_storage_dir', '.workflow_progress'))
        self.state_file = self.storage_dir / 'workflow_state.json'
        self.steps_dir = self.storage_dir / 'steps'
        self.backup_dir = self.storage_dir / 'backups'
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self.steps_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create storage directories: {e}")
    
    def save_progress(self, step_id: int, status: StepStatus, data: Dict[str, Any], error_message: Optional[str] = None) -> bool:
        """Save progress for a specific step."""
        try:
            # Create step result
            step_result = StepResult(
                step_id=step_id,
                status=status,
                result_data=data,
                error_message=error_message,
                timestamp=datetime.now()
            )
            
            # Save step result to individual file
            step_file = self.steps_dir / f'step_{step_id}.json'
            with open(step_file, 'w', encoding='utf-8') as f:
                json.dump(step_result.to_dict(), f, indent=2)
            
            # Update workflow state if it exists
            workflow_state = self.load_progress()
            if workflow_state:
                if status == StepStatus.COMPLETED:
                    workflow_state.mark_step_complete(step_id)
                    workflow_state.current_step = step_id + 1
                
                # Save updated workflow state
                self._save_workflow_state(workflow_state)
            
            return True
            
        except Exception as e:
            print(f"Error saving progress for step {step_id}: {e}")
            return False
    
    def load_progress(self) -> Optional[WorkflowState]:
        """Load the current workflow state."""
        try:
            if not self.state_file.exists():
                return None
            
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return WorkflowState.from_dict(data)
            
        except Exception as e:
            print(f"Error loading progress: {e}")
            return None
    
    def mark_complete(self, step_id: int) -> bool:
        """Mark a step as completed."""
        return self.save_progress(step_id, StepStatus.COMPLETED, {})
    
    def get_completion_summary(self) -> Dict[str, Any]:
        """Get a summary of completed steps."""
        try:
            workflow_state = self.load_progress()
            if not workflow_state:
                return {
                    'total_steps': 0,
                    'completed_steps': 0,
                    'progress_percentage': 0.0,
                    'current_step': 0,
                    'project_name': None,
                    'last_updated': None
                }
            
            # Count total available steps
            total_steps = len(list(self.steps_dir.glob('step_*.json')))
            
            return {
                'total_steps': total_steps,
                'completed_steps': len(workflow_state.completed_steps),
                'progress_percentage': workflow_state.get_progress_percentage(total_steps),
                'current_step': workflow_state.current_step,
                'project_name': workflow_state.project_name,
                'last_updated': workflow_state.updated_at.isoformat(),
                'completed_step_ids': workflow_state.completed_steps.copy()
            }
            
        except Exception as e:
            print(f"Error getting completion summary: {e}")
            return {'error': str(e)}
    
    def _save_workflow_state(self, workflow_state: WorkflowState) -> bool:
        """Save workflow state to file."""
        try:
            # Create backup before saving
            self._create_backup()
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_state.to_dict(), f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving workflow state: {e}")
            return False
    
    def initialize_workflow(self, project_name: str, project_data: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize a new workflow state."""
        try:
            # Create new workflow state
            workflow_state = WorkflowState(
                project_name=project_name,
                current_step=1
            )
            
            # Add project data if provided
            if project_data:
                from ..models.workflow_models import ProjectData
                workflow_state.project_data = ProjectData.from_dict(project_data)
            
            return self._save_workflow_state(workflow_state)
            
        except Exception as e:
            print(f"Error initializing workflow: {e}")
            return False
    
    def rollback_step(self, step_id: int) -> bool:
        """Rollback a specific step."""
        try:
            # Remove step file
            step_file = self.steps_dir / f'step_{step_id}.json'
            if step_file.exists():
                step_file.unlink()
            
            # Update workflow state
            workflow_state = self.load_progress()
            if workflow_state:
                # Remove from completed steps
                if step_id in workflow_state.completed_steps:
                    workflow_state.completed_steps.remove(step_id)
                
                # Reset current step if needed
                if workflow_state.current_step > step_id:
                    workflow_state.current_step = step_id
                
                workflow_state.update_timestamp()
                return self._save_workflow_state(workflow_state)
            
            return True
            
        except Exception as e:
            print(f"Error rolling back step {step_id}: {e}")
            return False
    
    def get_step_result(self, step_id: int) -> Optional[StepResult]:
        """Get result for a specific step."""
        try:
            step_file = self.steps_dir / f'step_{step_id}.json'
            if not step_file.exists():
                return None
            
            with open(step_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return StepResult.from_dict(data)
            
        except Exception as e:
            print(f"Error loading step {step_id} result: {e}")
            return None
    
    def _create_backup(self) -> bool:
        """Create a backup of the current state."""
        try:
            if not self.state_file.exists():
                return True
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f'workflow_state_{timestamp}.json'
            
            shutil.copy2(self.state_file, backup_file)
            
            # Keep only last 10 backups
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_files = list(self.backup_dir.glob('workflow_state_*.json'))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for backup_file in backup_files[keep_count:]:
                backup_file.unlink()
                
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
    
    def restore_from_backup(self, backup_timestamp: Optional[str] = None) -> bool:
        """Restore workflow state from backup."""
        try:
            if backup_timestamp:
                backup_file = self.backup_dir / f'workflow_state_{backup_timestamp}.json'
            else:
                # Get most recent backup
                backup_files = list(self.backup_dir.glob('workflow_state_*.json'))
                if not backup_files:
                    print("No backup files found")
                    return False
                
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                backup_file = backup_files[0]
            
            if not backup_file.exists():
                print(f"Backup file not found: {backup_file}")
                return False
            
            # Copy backup to current state file
            shutil.copy2(backup_file, self.state_file)
            print(f"Restored from backup: {backup_file.name}")
            
            return True
            
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False
    
    def clear_all_progress(self) -> bool:
        """Clear all progress data (use with caution)."""
        try:
            # Create final backup before clearing
            self._create_backup()
            
            # Remove all step files
            for step_file in self.steps_dir.glob('step_*.json'):
                step_file.unlink()
            
            # Remove state file
            if self.state_file.exists():
                self.state_file.unlink()
            
            print("All progress data cleared")
            return True
            
        except Exception as e:
            print(f"Error clearing progress: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about storage usage."""
        try:
            total_size = 0
            file_count = 0
            
            # Calculate storage usage
            for file_path in self.storage_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                'storage_dir': str(self.storage_dir),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'has_active_workflow': self.state_file.exists(),
                'backup_count': len(list(self.backup_dir.glob('workflow_state_*.json')))
            }
            
        except Exception as e:
            return {'error': str(e)}