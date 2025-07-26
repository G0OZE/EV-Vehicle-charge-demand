"""
EV Charge Demand Analysis Tool

A comprehensive ML tool for analyzing and predicting EV vehicle charge demand patterns.
"""

__version__ = "1.0.0"
__author__ = "G0OZE"
__email__ = "killerfantom23@gmail.com"
__description__ = "ML tool for EV vehicle charge demand analysis and prediction"

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