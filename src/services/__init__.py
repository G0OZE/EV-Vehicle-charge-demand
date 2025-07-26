# Services module for external integrations and business logic

from .file_manager import FileManager
from .validation_service import ValidationService
from .workflow_core import WorkflowCore
from .progress_store import ProgressStore

# Import GitHub service with error handling
try:
    from .github_service import GitHubService, GitHubAPIError
    __all__ = [
        'GitHubService',
        'GitHubAPIError',
        'FileManager',
        'ValidationService',
        'WorkflowCore',
        'ProgressStore'
    ]
except ImportError as e:
    print(f"Warning: Could not import GitHubService: {e}")
    __all__ = [
        'FileManager',
        'ValidationService',
        'WorkflowCore',
        'ProgressStore'
    ]