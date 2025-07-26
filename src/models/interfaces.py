"""
Base interfaces and abstract classes for workflow components.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class StepStatus(Enum):
    """Status enumeration for workflow steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStep(ABC):
    """Abstract base class for workflow steps."""
    
    @abstractmethod
    def execute(self) -> 'StepResult':
        """Execute the workflow step."""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate step prerequisites and completion."""
        pass
    
    @abstractmethod
    def rollback(self) -> bool:
        """Rollback step changes if needed."""
        pass


class ServiceInterface(ABC):
    """Base interface for external service integrations."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the service with configuration."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available."""
        pass


class ProgressStore(ABC):
    """Abstract interface for progress persistence."""
    
    @abstractmethod
    def save_progress(self, step_id: int, status: StepStatus, data: Dict[str, Any]) -> bool:
        """Save progress for a specific step."""
        pass
    
    @abstractmethod
    def load_progress(self) -> Optional['WorkflowState']:
        """Load the current workflow state."""
        pass
    
    @abstractmethod
    def mark_complete(self, step_id: int) -> bool:
        """Mark a step as completed."""
        pass
    
    @abstractmethod
    def get_completion_summary(self) -> Dict[str, Any]:
        """Get a summary of completed steps."""
        pass


class ValidationService(ABC):
    """Abstract interface for validation operations."""
    
    @abstractmethod
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        pass
    
    @abstractmethod
    def validate_notebook_content(self, notebook_path: str) -> bool:
        """Validate notebook content completeness."""
        pass
    
    @abstractmethod
    def verify_repository_structure(self, repo_path: str) -> bool:
        """Verify repository has proper structure."""
        pass
    
    @abstractmethod
    def confirm_submission_readiness(self) -> bool:
        """Final validation before submission."""
        pass