"""
AICTE Workflow Tool

A comprehensive automation tool for AICTE internship project workflows.
"""

__version__ = "1.0.0"
__author__ = "G0OZE"
__email__ = "killerfantom23@gmail.com"
__description__ = "Automation tool for AICTE internship project workflows"

# Import main components for easy access
from .services.workflow_core import WorkflowCore
from .services.github_service import GitHubService
from .services.file_manager import FileManager
from .cli.workflow_cli import main as cli_main

__all__ = [
    "WorkflowCore",
    "GitHubService", 
    "FileManager",
    "cli_main",
    "__version__",
]