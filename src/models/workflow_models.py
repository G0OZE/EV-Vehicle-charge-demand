"""
Data models for workflow state and project data.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json
import re
from urllib.parse import urlparse
from .interfaces import StepStatus


@dataclass
class ProjectData:
    """Data model for project information."""
    project_id: str
    dataset_url: str
    code_template_url: str
    project_description: str
    requirements: List[str]
    deadline: datetime
    
    def __post_init__(self):
        """Validate data after initialization."""
        self.validate()
    
    def validate(self) -> bool:
        """Validate all project data fields."""
        errors = []
        
        # Validate project_id
        if not self.project_id or not isinstance(self.project_id, str):
            errors.append("project_id must be a non-empty string")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', self.project_id):
            errors.append("project_id must contain only alphanumeric characters, underscores, and hyphens")
        
        # Validate URLs
        if not self._is_valid_url(self.dataset_url):
            errors.append("dataset_url must be a valid URL")
        if not self._is_valid_url(self.code_template_url):
            errors.append("code_template_url must be a valid URL")
        
        # Validate project_description
        if not self.project_description or not isinstance(self.project_description, str):
            errors.append("project_description must be a non-empty string")
        elif len(self.project_description.strip()) < 10:
            errors.append("project_description must be at least 10 characters long")
        
        # Validate requirements
        if not isinstance(self.requirements, list):
            errors.append("requirements must be a list")
        elif not self.requirements:
            errors.append("requirements list cannot be empty")
        elif not all(isinstance(req, str) and req.strip() for req in self.requirements):
            errors.append("all requirements must be non-empty strings")
        
        # Validate deadline
        if not isinstance(self.deadline, datetime):
            errors.append("deadline must be a datetime object")
        elif self.deadline < datetime.now():
            errors.append("deadline cannot be in the past")
        
        if errors:
            raise ValueError(f"ProjectData validation failed: {'; '.join(errors)}")
        
        return True
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        if not url or not isinstance(url, str):
            return False
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['deadline'] = self.deadline.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectData':
        """Create instance from dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        # Convert deadline string back to datetime
        if 'deadline' in data and isinstance(data['deadline'], str):
            data['deadline'] = datetime.fromisoformat(data['deadline'])
        
        return cls(**data)


@dataclass
class StepResult:
    """Result data for workflow step execution."""
    step_id: int
    status: StepStatus
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate data after initialization."""
        self.validate()
    
    def validate(self) -> bool:
        """Validate step result data."""
        errors = []
        
        # Validate step_id
        if not isinstance(self.step_id, int):
            errors.append("step_id must be an integer")
        elif self.step_id < 0:
            errors.append("step_id must be non-negative")
        
        # Validate status
        if not isinstance(self.status, StepStatus):
            errors.append("status must be a StepStatus enum value")
        
        # Validate result_data
        if not isinstance(self.result_data, dict):
            errors.append("result_data must be a dictionary")
        
        # Validate error_message
        if self.error_message is not None and not isinstance(self.error_message, str):
            errors.append("error_message must be a string or None")
        
        # Validate timestamp
        if not isinstance(self.timestamp, datetime):
            errors.append("timestamp must be a datetime object")
        
        # Business logic validation
        if self.status == StepStatus.FAILED and not self.error_message:
            errors.append("error_message is required when status is FAILED")
        
        if errors:
            raise ValueError(f"StepResult validation failed: {'; '.join(errors)}")
        
        return True
    
    def is_successful(self) -> bool:
        """Check if the step was successful."""
        return self.status == StepStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if the step failed."""
        return self.status == StepStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepResult':
        """Create instance from dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        # Convert status string back to enum
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = StepStatus(data['status'])
        
        # Convert timestamp string back to datetime
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)


@dataclass
class WorkflowState:
    """Complete workflow state for persistence."""
    project_name: str
    current_step: int
    completed_steps: List[int] = field(default_factory=list)
    project_data: Optional[ProjectData] = None
    github_repo: Optional[str] = None
    submission_link: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate data after initialization."""
        self.validate()
    
    def validate(self) -> bool:
        """Validate workflow state data."""
        errors = []
        
        # Validate project_name
        if not self.project_name or not isinstance(self.project_name, str):
            errors.append("project_name must be a non-empty string")
        elif len(self.project_name.strip()) < 3:
            errors.append("project_name must be at least 3 characters long")
        
        # Validate current_step
        if not isinstance(self.current_step, int):
            errors.append("current_step must be an integer")
        elif self.current_step < 0:
            errors.append("current_step must be non-negative")
        
        # Validate completed_steps
        if not isinstance(self.completed_steps, list):
            errors.append("completed_steps must be a list")
        elif not all(isinstance(step, int) and step >= 0 for step in self.completed_steps):
            errors.append("all completed_steps must be non-negative integers")
        
        # Validate project_data
        if self.project_data is not None and not isinstance(self.project_data, ProjectData):
            errors.append("project_data must be a ProjectData instance or None")
        
        # Validate github_repo
        if self.github_repo is not None:
            if not isinstance(self.github_repo, str):
                errors.append("github_repo must be a string or None")
            elif not re.match(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$', self.github_repo):
                errors.append("github_repo must be in format 'owner/repo'")
        
        # Validate submission_link
        if self.submission_link is not None:
            if not isinstance(self.submission_link, str):
                errors.append("submission_link must be a string or None")
            elif not self._is_valid_url(self.submission_link):
                errors.append("submission_link must be a valid URL")
        
        # Validate timestamps
        if not isinstance(self.created_at, datetime):
            errors.append("created_at must be a datetime object")
        if not isinstance(self.updated_at, datetime):
            errors.append("updated_at must be a datetime object")
        
        # Business logic validation
        if self.current_step in self.completed_steps:
            errors.append("current_step should not be in completed_steps")
        
        if errors:
            raise ValueError(f"WorkflowState validation failed: {'; '.join(errors)}")
        
        return True
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        if not url or not isinstance(url, str):
            return False
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def update_timestamp(self):
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()
    
    def is_step_completed(self, step_id: int) -> bool:
        """Check if a specific step is completed."""
        return step_id in self.completed_steps
    
    def mark_step_complete(self, step_id: int):
        """Mark a step as completed."""
        if step_id not in self.completed_steps:
            self.completed_steps.append(step_id)
            self.completed_steps.sort()  # Keep sorted for consistency
        self.update_timestamp()
    
    def get_progress_percentage(self, total_steps: int) -> float:
        """Calculate completion percentage."""
        if total_steps == 0:
            return 0.0
        return (len(self.completed_steps) / total_steps) * 100
    
    def get_next_step(self) -> int:
        """Get the next step to execute."""
        return self.current_step
    
    def advance_to_next_step(self):
        """Advance to the next step in the workflow."""
        self.mark_step_complete(self.current_step)
        self.current_step += 1
        self.update_timestamp()
    
    def is_workflow_complete(self, total_steps: int) -> bool:
        """Check if the entire workflow is complete."""
        return len(self.completed_steps) >= total_steps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            'project_name': self.project_name,
            'current_step': self.current_step,
            'completed_steps': self.completed_steps.copy(),
            'project_data': self.project_data.to_dict() if self.project_data else None,
            'github_repo': self.github_repo,
            'submission_link': self.submission_link,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """Create instance from dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        # Convert project_data dict back to ProjectData instance
        if data.get('project_data'):
            data['project_data'] = ProjectData.from_dict(data['project_data'])
        
        # Convert timestamp strings back to datetime
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string for persistence."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WorkflowState':
        """Create instance from JSON string."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Failed to create WorkflowState from JSON: {e}")