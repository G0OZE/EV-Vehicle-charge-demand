"""
User guidance system for AICTE project workflow.
Provides detailed error messages, help system, and troubleshooting guides.
"""
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import re
from pathlib import Path


class ErrorCategory(Enum):
    """Categories of errors that can occur in the workflow."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    USER_INPUT = "user_input"
    FILE_SYSTEM = "file_system"
    GITHUB_API = "github_api"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuidanceMessage:
    """Structured guidance message with error details and resolution steps."""
    
    def __init__(
        self,
        error_code: str,
        title: str,
        description: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        resolution_steps: List[str],
        related_links: Optional[List[str]] = None,
        troubleshooting_tips: Optional[List[str]] = None
    ):
        self.error_code = error_code
        self.title = title
        self.description = description
        self.category = category
        self.severity = severity
        self.resolution_steps = resolution_steps
        self.related_links = related_links or []
        self.troubleshooting_tips = troubleshooting_tips or []


class UserGuidanceService:
    """Service for providing user guidance, error messages, and troubleshooting help."""
    
    def __init__(self):
        """Initialize the user guidance service."""
        self.error_catalog = self._build_error_catalog()
        self.help_topics = self._build_help_topics()
        self.troubleshooting_guides = self._build_troubleshooting_guides()
    
    def get_error_guidance(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> GuidanceMessage:
        """Get detailed guidance for an error message."""
        # Try to match error message to known patterns
        error_code = self._classify_error(error_message, context)
        
        if error_code in self.error_catalog:
            guidance = self.error_catalog[error_code]
            # Customize guidance based on context
            return self._customize_guidance(guidance, context)
        
        # Return generic guidance for unknown errors
        return self._get_generic_error_guidance(error_message, context)
    
    def get_help_for_topic(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get help information for a specific topic."""
        return self.help_topics.get(topic.lower())
    
    def get_troubleshooting_guide(self, issue: str) -> Optional[Dict[str, Any]]:
        """Get troubleshooting guide for a specific issue."""
        return self.troubleshooting_guides.get(issue.lower())
    
    def list_help_topics(self) -> List[str]:
        """List all available help topics."""
        return list(self.help_topics.keys())
    
    def list_troubleshooting_guides(self) -> List[str]:
        """List all available troubleshooting guides."""
        return list(self.troubleshooting_guides.keys())
    
    def format_guidance_message(self, guidance: GuidanceMessage) -> str:
        """Format a guidance message for display."""
        severity_icons = {
            ErrorSeverity.LOW: "ℹ️",
            ErrorSeverity.MEDIUM: "⚠️",
            ErrorSeverity.HIGH: "❌",
            ErrorSeverity.CRITICAL: "🚨"
        }
        
        icon = severity_icons.get(guidance.severity, "❓")
        
        formatted = f"{icon} {guidance.title}\n"
        formatted += f"Error Code: {guidance.error_code}\n"
        formatted += f"Category: {guidance.category.value.title()}\n\n"
        formatted += f"Description:\n{guidance.description}\n\n"
        
        if guidance.resolution_steps:
            formatted += "Resolution Steps:\n"
            for i, step in enumerate(guidance.resolution_steps, 1):
                formatted += f"  {i}. {step}\n"
            formatted += "\n"
        
        if guidance.troubleshooting_tips:
            formatted += "Troubleshooting Tips:\n"
            for tip in guidance.troubleshooting_tips:
                formatted += f"  • {tip}\n"
            formatted += "\n"
        
        if guidance.related_links:
            formatted += "Related Links:\n"
            for link in guidance.related_links:
                formatted += f"  • {link}\n"
        
        return formatted
    
    def _build_error_catalog(self) -> Dict[str, GuidanceMessage]:
        """Build catalog of known errors and their guidance."""
        catalog = {}
        
        # Network errors
        catalog["NET001"] = GuidanceMessage(
            error_code="NET001",
            title="Internet Connection Failed",
            description="Unable to establish internet connection. This prevents downloading datasets, accessing GitHub, and other online operations.",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            resolution_steps=[
                "Check your internet connection",
                "Try accessing a website in your browser",
                "Restart your network adapter",
                "Contact your network administrator if on corporate network",
                "Try using a different network connection"
            ],
            troubleshooting_tips=[
                "Use 'ping google.com' to test basic connectivity",
                "Check if firewall is blocking the application",
                "Try using mobile hotspot as alternative connection"
            ]
        )
        
        catalog["NET002"] = GuidanceMessage(
            error_code="NET002",
            title="GitHub API Rate Limit Exceeded",
            description="GitHub API rate limit has been exceeded. This temporarily prevents GitHub operations.",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=[
                "Wait for rate limit to reset (usually 1 hour)",
                "Use authenticated requests with GitHub token",
                "Reduce frequency of GitHub API calls",
                "Check GitHub API status page"
            ],
            related_links=[
                "https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting"
            ]
        )
        
        # Authentication errors
        catalog["AUTH001"] = GuidanceMessage(
            error_code="AUTH001",
            title="GitHub Token Missing or Invalid",
            description="GitHub personal access token is missing or invalid. This prevents repository operations.",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            resolution_steps=[
                "Create a GitHub personal access token",
                "Set GITHUB_TOKEN environment variable",
                "Ensure token has required permissions (repo, user)",
                "Check token expiration date",
                "Regenerate token if necessary"
            ],
            related_links=[
                "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
            ],
            troubleshooting_tips=[
                "Token should start with 'ghp_' for new tokens",
                "Classic tokens start with 'ghp_' or older format",
                "Fine-grained tokens have different format and permissions"
            ]
        )
        
        # Validation errors
        catalog["VAL001"] = GuidanceMessage(
            error_code="VAL001",
            title="Notebook Validation Failed",
            description="Jupyter notebook does not meet project requirements or has structural issues.",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=[
                "Ensure notebook has required sections (data loading, preprocessing, analysis)",
                "Execute all code cells to generate outputs",
                "Remove placeholder code and TODO comments",
                "Add markdown cells with section headers",
                "Save notebook after making changes"
            ],
            troubleshooting_tips=[
                "Use 'Restart & Run All' to execute entire notebook",
                "Check for syntax errors in code cells",
                "Ensure all imports are at the top of notebook"
            ]
        )
        
        catalog["VAL002"] = GuidanceMessage(
            error_code="VAL002",
            title="Dataset File Invalid",
            description="Dataset file is missing, empty, or in incorrect format.",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=[
                "Verify dataset file exists in project directory",
                "Check file is not empty (size > 0 bytes)",
                "Ensure file is in CSV format with proper headers",
                "Validate data has at least 2 columns",
                "Re-download dataset if corrupted"
            ],
            troubleshooting_tips=[
                "Open CSV file in text editor to check format",
                "Use pandas.read_csv() to test file validity",
                "Check for special characters in file path"
            ]
        )
        
        # File system errors
        catalog["FS001"] = GuidanceMessage(
            error_code="FS001",
            title="File Permission Denied",
            description="Insufficient permissions to read or write files in the specified location.",
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=[
                "Check file and directory permissions",
                "Run application with appropriate user privileges",
                "Ensure target directory is writable",
                "Close any applications that might be locking the file",
                "Try using a different directory"
            ],
            troubleshooting_tips=[
                "On Windows, try running as Administrator",
                "On Unix systems, check file ownership and permissions",
                "Ensure antivirus is not blocking file access"
            ]
        )
        
        # GitHub API errors
        catalog["GH001"] = GuidanceMessage(
            error_code="GH001",
            title="Repository Creation Failed",
            description="Unable to create GitHub repository due to API error or permission issues.",
            category=ErrorCategory.GITHUB_API,
            severity=ErrorSeverity.HIGH,
            resolution_steps=[
                "Verify GitHub token has 'repo' permission",
                "Check if repository name already exists",
                "Ensure repository name follows GitHub naming rules",
                "Check GitHub API status",
                "Try creating repository manually first"
            ],
            troubleshooting_tips=[
                "Repository names must be unique within your account",
                "Avoid special characters in repository names",
                "Check GitHub status page for service issues"
            ]
        )
        
        # Configuration errors
        catalog["CFG001"] = GuidanceMessage(
            error_code="CFG001",
            title="Configuration File Missing or Invalid",
            description="Application configuration file is missing or contains invalid settings.",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=[
                "Create config.json file from template",
                "Verify JSON syntax is valid",
                "Check all required configuration keys are present",
                "Validate configuration values are correct type",
                "Reset to default configuration if needed"
            ],
            troubleshooting_tips=[
                "Use JSON validator to check syntax",
                "Compare with config.template.json",
                "Check for trailing commas in JSON"
            ]
        )
        
        # Dependency errors
        catalog["DEP001"] = GuidanceMessage(
            error_code="DEP001",
            title="Required Package Missing",
            description="Required Python package is not installed or not accessible.",
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=[
                "Install missing package using pip",
                "Activate correct Python virtual environment",
                "Check Python path and environment variables",
                "Update package to latest version if needed",
                "Install from requirements.txt file"
            ],
            troubleshooting_tips=[
                "Use 'pip list' to see installed packages",
                "Check if using correct Python interpreter",
                "Try installing in user directory with --user flag"
            ]
        )
        
        # Workflow-specific errors
        catalog["WF001"] = GuidanceMessage(
            error_code="WF001",
            title="Workflow Step Failed",
            description="A workflow step failed to complete successfully, preventing progression to the next step.",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            resolution_steps=[
                "Check the specific error message for the failed step",
                "Verify all prerequisites for the step are met",
                "Retry the step after addressing any issues",
                "Use 'resume' command to continue from last successful step",
                "Check progress with 'progress' command"
            ],
            troubleshooting_tips=[
                "Each step builds on previous ones - ensure earlier steps completed",
                "Check file permissions and network connectivity",
                "Verify configuration settings are correct"
            ]
        )
        
        catalog["WF002"] = GuidanceMessage(
            error_code="WF002",
            title="Progress State Corrupted",
            description="The workflow progress state file is corrupted or unreadable.",
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=[
                "Delete the progress state file and restart workflow",
                "Check file permissions on progress directory",
                "Ensure sufficient disk space is available",
                "Restart workflow with 'start' command",
                "Manually recreate progress if needed"
            ],
            troubleshooting_tips=[
                "Progress files are stored in .workflow_progress directory",
                "Backup important work before deleting progress files",
                "Check for disk corruption if problem persists"
            ]
        )
        
        catalog["WF003"] = GuidanceMessage(
            error_code="WF003",
            title="Submission Validation Failed",
            description="Final submission validation failed due to missing or invalid components.",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            resolution_steps=[
                "Review the validation checklist for missing items",
                "Ensure notebook has all required sections completed",
                "Verify dataset file is properly uploaded",
                "Check GitHub repository has all required files",
                "Re-run validation after fixing issues"
            ],
            troubleshooting_tips=[
                "Use 'validate' command to check submission status",
                "Each project has specific requirements - check project guidelines",
                "Ensure all code cells in notebook have been executed"
            ]
        )
        
        # LMS integration errors
        catalog["LMS001"] = GuidanceMessage(
            error_code="LMS001",
            title="LMS Submission Failed",
            description="Failed to submit project to Learning Management System.",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            resolution_steps=[
                "Check internet connection and LMS availability",
                "Verify LMS credentials are correct",
                "Ensure submission deadline has not passed",
                "Try submitting manually through LMS portal",
                "Contact LMS support if technical issues persist"
            ],
            troubleshooting_tips=[
                "Save repository URL for manual submission",
                "Check LMS system status page",
                "Try submitting during off-peak hours"
            ]
        )
        
        # Project-specific errors
        catalog["PRJ001"] = GuidanceMessage(
            error_code="PRJ001",
            title="Project Selection Invalid",
            description="Selected project is not available or has invalid configuration.",
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=[
                "Check available projects with 'list' command",
                "Verify project number is within valid range",
                "Ensure project configuration files are present",
                "Try selecting a different project",
                "Update project list if needed"
            ],
            troubleshooting_tips=[
                "Project numbers start from 1",
                "Some projects may have prerequisites",
                "Check project availability dates"
            ]
        )
        
        return catalog
    
    def _build_help_topics(self) -> Dict[str, Dict[str, Any]]:
        """Build help topics catalog."""
        topics = {}
        
        topics["getting-started"] = {
            "title": "Getting Started with AICTE Workflow",
            "description": "Learn how to set up and use the AICTE project workflow automation tool.",
            "sections": [
                {
                    "title": "Prerequisites",
                    "content": [
                        "Python 3.7 or higher installed",
                        "GitHub account with personal access token",
                        "Internet connection for downloading datasets",
                        "Text editor or IDE for code development"
                    ]
                },
                {
                    "title": "First Steps",
                    "content": [
                        "Run 'start' command to begin new project",
                        "Select project from available options",
                        "Follow step-by-step workflow guidance",
                        "Use 'progress' command to check status"
                    ]
                },
                {
                    "title": "Common Commands",
                    "content": [
                        "start --project <name>: Start new workflow",
                        "resume --project <name>: Continue existing workflow",
                        "progress --project <name>: Check progress",
                        "validate --project <name>: Validate submission"
                    ]
                }
            ]
        }
        
        topics["github-setup"] = {
            "title": "GitHub Setup and Configuration",
            "description": "How to configure GitHub integration for the workflow.",
            "sections": [
                {
                    "title": "Creating Personal Access Token",
                    "content": [
                        "Go to GitHub Settings > Developer settings > Personal access tokens",
                        "Click 'Generate new token (classic)'",
                        "Select 'repo' and 'user' scopes",
                        "Copy token and store securely",
                        "Set GITHUB_TOKEN environment variable"
                    ]
                },
                {
                    "title": "Environment Variable Setup",
                    "content": [
                        "Windows: set GITHUB_TOKEN=your_token_here",
                        "Linux/Mac: export GITHUB_TOKEN=your_token_here",
                        "Add to .bashrc or .zshrc for persistence",
                        "Restart terminal after setting variable"
                    ]
                }
            ]
        }
        
        topics["troubleshooting"] = {
            "title": "Common Issues and Solutions",
            "description": "Solutions for frequently encountered problems.",
            "sections": [
                {
                    "title": "Network Issues",
                    "content": [
                        "Check internet connection",
                        "Verify firewall settings",
                        "Try different network if available",
                        "Check proxy settings if applicable"
                    ]
                },
                {
                    "title": "File Issues",
                    "content": [
                        "Ensure files are not locked by other applications",
                        "Check file permissions and ownership",
                        "Verify file paths are correct",
                        "Try using absolute paths instead of relative"
                    ]
                }
            ]
        }
        
        topics["workflow-commands"] = {
            "title": "Workflow Commands Reference",
            "description": "Complete reference for all workflow commands and their usage.",
            "sections": [
                {
                    "title": "Basic Commands",
                    "content": [
                        "start: Begin new project workflow",
                        "resume: Continue interrupted workflow",
                        "progress: Check current workflow status",
                        "validate: Verify submission completeness",
                        "help: Show help information"
                    ]
                },
                {
                    "title": "Command Options",
                    "content": [
                        "--project <n>: Specify project number",
                        "--force: Force restart of workflow",
                        "--verbose: Show detailed output",
                        "--config <file>: Use custom configuration"
                    ]
                },
                {
                    "title": "Examples",
                    "content": [
                        "start --project 1: Start project 1",
                        "resume --project 1: Resume project 1",
                        "progress --project 1: Check project 1 status",
                        "validate --project 1: Validate project 1 submission"
                    ]
                }
            ]
        }
        
        topics["project-requirements"] = {
            "title": "Project Requirements and Validation",
            "description": "Understanding project requirements and validation criteria.",
            "sections": [
                {
                    "title": "General Requirements",
                    "content": [
                        "Complete Jupyter notebook with all sections",
                        "Dataset properly loaded and processed",
                        "All code cells executed with outputs",
                        "GitHub repository with proper structure",
                        "README file with project description"
                    ]
                },
                {
                    "title": "Notebook Structure",
                    "content": [
                        "Title and description section",
                        "Data loading and exploration",
                        "Data preprocessing and cleaning",
                        "Analysis and visualization",
                        "Results and conclusions"
                    ]
                },
                {
                    "title": "Validation Checklist",
                    "content": [
                        "All required sections present",
                        "Code executes without errors",
                        "Outputs are meaningful and complete",
                        "Dataset is properly referenced",
                        "Repository is publicly accessible"
                    ]
                }
            ]
        }
        
        topics["error-recovery"] = {
            "title": "Error Recovery and Troubleshooting",
            "description": "How to recover from errors and troubleshoot common issues.",
            "sections": [
                {
                    "title": "Recovery Strategies",
                    "content": [
                        "Use 'resume' command to continue from last successful step",
                        "Check error messages for specific guidance",
                        "Verify prerequisites before retrying",
                        "Clear temporary files if needed",
                        "Restart workflow as last resort"
                    ]
                },
                {
                    "title": "Common Error Patterns",
                    "content": [
                        "Network timeouts: Check connection and retry",
                        "Authentication failures: Verify tokens and credentials",
                        "File permission errors: Check access rights",
                        "Validation failures: Review requirements checklist",
                        "API rate limits: Wait and retry later"
                    ]
                },
                {
                    "title": "Prevention Tips",
                    "content": [
                        "Ensure stable internet connection",
                        "Keep GitHub tokens up to date",
                        "Regularly save work and commit changes",
                        "Follow project guidelines carefully",
                        "Test components before final submission"
                    ]
                }
            ]
        }
        
        return topics
    
    def _build_troubleshooting_guides(self) -> Dict[str, Dict[str, Any]]:
        """Build troubleshooting guides catalog."""
        guides = {}
        
        guides["workflow-stuck"] = {
            "title": "Workflow Appears Stuck or Frozen",
            "description": "What to do when the workflow stops progressing.",
            "symptoms": [
                "Progress not updating after long time",
                "Commands hang without response",
                "Error messages not appearing"
            ],
            "diagnosis_steps": [
                "Check if process is still running",
                "Look for error messages in console",
                "Verify internet connection",
                "Check available disk space"
            ],
            "solutions": [
                "Restart the workflow with 'resume' command",
                "Check system resources (CPU, memory, disk)",
                "Clear temporary files and cache",
                "Try running individual steps manually"
            ]
        }
        
        guides["github-authentication"] = {
            "title": "GitHub Authentication Problems",
            "description": "Resolving GitHub token and permission issues.",
            "symptoms": [
                "401 Unauthorized errors",
                "403 Forbidden errors",
                "Repository creation failures"
            ],
            "diagnosis_steps": [
                "Verify GITHUB_TOKEN environment variable is set",
                "Check token hasn't expired",
                "Confirm token has required permissions",
                "Test token with GitHub API directly"
            ],
            "solutions": [
                "Regenerate GitHub personal access token",
                "Ensure token has 'repo' and 'user' scopes",
                "Set environment variable correctly",
                "Restart terminal/application after setting token"
            ]
        }
        
        guides["notebook-validation"] = {
            "title": "Notebook Validation Failures",
            "description": "Fixing common notebook validation issues.",
            "symptoms": [
                "Notebook validation fails",
                "Missing required sections error",
                "Empty or placeholder code warnings"
            ],
            "diagnosis_steps": [
                "Open notebook and check structure",
                "Look for TODO comments or placeholder code",
                "Verify all cells have been executed",
                "Check for required markdown sections"
            ],
            "solutions": [
                "Add proper section headers in markdown cells",
                "Execute all code cells to generate outputs",
                "Replace placeholder code with actual implementation",
                "Ensure notebook follows project template structure"
            ]
        }
        
        guides["dataset-issues"] = {
            "title": "Dataset Loading and Processing Problems",
            "description": "Resolving issues with dataset files and processing.",
            "symptoms": [
                "Dataset file not found or corrupted",
                "CSV parsing errors",
                "Data type conversion failures",
                "Missing or invalid data columns"
            ],
            "diagnosis_steps": [
                "Check if dataset file exists in correct location",
                "Verify file format and encoding",
                "Test file opening with text editor",
                "Check file size and content structure"
            ],
            "solutions": [
                "Re-download dataset from original source",
                "Verify file path and naming conventions",
                "Check CSV delimiter and encoding settings",
                "Handle missing values appropriately in code",
                "Validate data types after loading"
            ]
        }
        
        guides["submission-deadline"] = {
            "title": "Submission Deadline and Timing Issues",
            "description": "Managing submission deadlines and timing constraints.",
            "symptoms": [
                "Submission deadline passed",
                "Late submission warnings",
                "Time zone confusion",
                "System clock synchronization issues"
            ],
            "diagnosis_steps": [
                "Check current date and time",
                "Verify submission deadline in project requirements",
                "Confirm time zone settings",
                "Check system clock accuracy"
            ],
            "solutions": [
                "Submit as soon as possible if deadline passed",
                "Contact instructor about late submission policy",
                "Synchronize system clock with network time",
                "Plan submissions well before deadline",
                "Set up reminder notifications"
            ]
        }
        
        guides["repository-access"] = {
            "title": "GitHub Repository Access and Permissions",
            "description": "Fixing GitHub repository access and permission problems.",
            "symptoms": [
                "Repository not accessible",
                "Permission denied errors",
                "Repository not found",
                "Clone or push failures"
            ],
            "diagnosis_steps": [
                "Check repository URL and name",
                "Verify repository visibility settings",
                "Test GitHub token permissions",
                "Check network connectivity to GitHub"
            ],
            "solutions": [
                "Make repository public for submission",
                "Regenerate GitHub token with correct permissions",
                "Check repository name spelling and case",
                "Verify GitHub account access",
                "Try accessing repository through web browser"
            ]
        }
        
        guides["environment-setup"] = {
            "title": "Development Environment Setup Issues",
            "description": "Resolving Python environment and dependency problems.",
            "symptoms": [
                "Import errors for required packages",
                "Python version compatibility issues",
                "Virtual environment activation problems",
                "Package installation failures"
            ],
            "diagnosis_steps": [
                "Check Python version and installation",
                "Verify virtual environment is activated",
                "List installed packages",
                "Check package version compatibility"
            ],
            "solutions": [
                "Install required packages using pip",
                "Create and activate virtual environment",
                "Update Python to supported version",
                "Install packages from requirements.txt",
                "Check for conflicting package versions"
            ]
        }
        
        guides["performance-optimization"] = {
            "title": "Performance and Resource Optimization",
            "description": "Optimizing workflow performance and resource usage.",
            "symptoms": [
                "Slow file uploads or downloads",
                "High memory usage",
                "Long processing times",
                "System responsiveness issues"
            ],
            "diagnosis_steps": [
                "Monitor system resource usage",
                "Check network bandwidth and latency",
                "Profile code execution times",
                "Identify resource-intensive operations"
            ],
            "solutions": [
                "Use smaller dataset samples for testing",
                "Optimize code for better performance",
                "Close unnecessary applications",
                "Use faster internet connection if available",
                "Process data in smaller chunks"
            ]
        }
        
        return guides
    
    def _classify_error(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Classify error message to determine appropriate guidance."""
        error_message_lower = error_message.lower()
        
        # Check for more specific patterns first to avoid false matches
        
        # Rate limit (specific network error)
        if "rate limit" in error_message_lower:
            return "NET002"
        
        # LMS errors (check before general submission/validation)
        if any(keyword in error_message_lower for keyword in [
            "lms submission failed", "learning management"
        ]):
            return "LMS001"
        
        # Workflow-specific errors (check before general validation)
        if any(keyword in error_message_lower for keyword in [
            "workflow step failed", "step failed", "workflow error"
        ]):
            return "WF001"
        
        if any(keyword in error_message_lower for keyword in [
            "progress state corrupted", "progress file"
        ]):
            return "WF002"
        
        if "submission validation failed" in error_message_lower:
            return "WF003"
        
        # Project errors
        if any(keyword in error_message_lower for keyword in [
            "project selection", "invalid project", "project not found"
        ]):
            return "PRJ001"
        
        # GitHub API errors (check before general repository errors)
        if any(keyword in error_message_lower for keyword in [
            "repository creation failed", "create repo", "github api"
        ]):
            return "GH001"
        
        # Authentication errors
        if any(keyword in error_message_lower for keyword in [
            "unauthorized", "401", "invalid token", "authentication"
        ]):
            return "AUTH001"
        
        # Validation errors (general)
        if any(keyword in error_message_lower for keyword in [
            "notebook validation", "missing section", "empty cell"
        ]) and "submission" not in error_message_lower:
            return "VAL001"
        
        if any(keyword in error_message_lower for keyword in [
            "dataset", "csv", "file format", "invalid data"
        ]):
            return "VAL002"
        
        # File system errors
        if any(keyword in error_message_lower for keyword in [
            "permission denied", "access denied", "file not found"
        ]):
            return "FS001"
        
        # Configuration errors
        if any(keyword in error_message_lower for keyword in [
            "config", "configuration", "json", "invalid format"
        ]):
            return "CFG001"
        
        # Dependency errors
        if any(keyword in error_message_lower for keyword in [
            "import", "module", "package", "not found", "no module"
        ]):
            return "DEP001"
        
        # General network errors (check after specific network errors)
        if any(keyword in error_message_lower for keyword in [
            "connection", "network", "timeout", "unreachable", "dns"
        ]) and "lms" not in error_message_lower:
            return "NET001"
        
        # General GitHub errors (check after specific GitHub errors)
        if any(keyword in error_message_lower for keyword in [
            "repository", "github", "403"
        ]):
            return "GH001"
        
        # Default to generic error
        return "GENERIC"
    
    def _customize_guidance(self, guidance: GuidanceMessage, context: Optional[Dict[str, Any]]) -> GuidanceMessage:
        """Customize guidance message based on context."""
        if not context:
            return guidance
        
        # Create a copy to avoid modifying original
        customized_steps = guidance.resolution_steps.copy()
        customized_tips = guidance.troubleshooting_tips.copy()
        
        # Add context-specific information
        if context.get("project_name"):
            customized_steps.insert(0, f"For project '{context['project_name']}':")
        
        if context.get("step_id"):
            customized_tips.append(f"This error occurred during step {context['step_id']}")
        
        if context.get("file_path"):
            customized_tips.append(f"File involved: {context['file_path']}")
        
        # Return customized guidance
        return GuidanceMessage(
            error_code=guidance.error_code,
            title=guidance.title,
            description=guidance.description,
            category=guidance.category,
            severity=guidance.severity,
            resolution_steps=customized_steps,
            related_links=guidance.related_links,
            troubleshooting_tips=customized_tips
        )
    
    def _get_generic_error_guidance(self, error_message: str, context: Optional[Dict[str, Any]]) -> GuidanceMessage:
        """Get generic guidance for unknown errors."""
        return GuidanceMessage(
            error_code="GENERIC",
            title="Unexpected Error Occurred",
            description=f"An unexpected error occurred: {error_message}",
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=[
                "Check the error message for specific details",
                "Verify all prerequisites are met",
                "Try restarting the workflow",
                "Check system resources and permissions",
                "Contact support if issue persists"
            ],
            troubleshooting_tips=[
                "Look for more detailed error information in logs",
                "Try running the command again",
                "Check if similar issues are documented"
            ]
        )
    
    def get_interactive_help(self, query: str) -> Dict[str, Any]:
        """Get interactive help based on user query."""
        query_lower = query.lower()
        
        # Search in help topics
        matching_topics = []
        for topic_name, topic_info in self.help_topics.items():
            if (query_lower in topic_name.lower() or 
                query_lower in topic_info['title'].lower() or
                query_lower in topic_info['description'].lower()):
                matching_topics.append({
                    'type': 'help_topic',
                    'name': topic_name,
                    'title': topic_info['title'],
                    'description': topic_info['description']
                })
        
        # Search in troubleshooting guides
        matching_guides = []
        for guide_name, guide_info in self.troubleshooting_guides.items():
            if (query_lower in guide_name.lower() or 
                query_lower in guide_info['title'].lower() or
                query_lower in guide_info['description'].lower()):
                matching_guides.append({
                    'type': 'troubleshooting_guide',
                    'name': guide_name,
                    'title': guide_info['title'],
                    'description': guide_info['description']
                })
        
        # Search in error catalog
        matching_errors = []
        for error_code, guidance in self.error_catalog.items():
            if (query_lower in guidance.title.lower() or 
                query_lower in guidance.description.lower() or
                any(query_lower in step.lower() for step in guidance.resolution_steps)):
                matching_errors.append({
                    'type': 'error_guidance',
                    'code': error_code,
                    'title': guidance.title,
                    'description': guidance.description,
                    'category': guidance.category.value
                })
        
        return {
            'query': query,
            'help_topics': matching_topics,
            'troubleshooting_guides': matching_guides,
            'error_guidance': matching_errors,
            'total_results': len(matching_topics) + len(matching_guides) + len(matching_errors)
        }
    
    def get_quick_help(self, topic: str) -> str:
        """Get quick help summary for a topic."""
        quick_help = {
            'start': 'Begin a new project workflow: start --project <number>',
            'resume': 'Continue an interrupted workflow: resume --project <number>',
            'progress': 'Check workflow progress: progress --project <number>',
            'validate': 'Validate submission: validate --project <number>',
            'github': 'Set GITHUB_TOKEN environment variable with your personal access token',
            'token': 'Create GitHub token at: Settings > Developer settings > Personal access tokens',
            'notebook': 'Ensure notebook has all sections completed and cells executed',
            'dataset': 'Verify dataset file is in CSV format and properly loaded',
            'submission': 'Check all requirements are met before submitting',
            'error': 'Read error messages carefully and follow resolution steps',
            'help': 'Use help <topic> for detailed information on any topic'
        }
        
        return quick_help.get(topic.lower(), f"No quick help available for '{topic}'. Use 'help --list' to see available topics.")
    
    def suggest_next_steps(self, current_step: int, error_occurred: bool = False) -> List[str]:
        """Suggest next steps based on current workflow state."""
        if error_occurred:
            return [
                "Read the error message carefully for specific guidance",
                "Check the troubleshooting guide for your specific issue",
                "Verify all prerequisites are met before retrying",
                "Use 'resume' command to continue from last successful step",
                "Contact support if the issue persists"
            ]
        
        step_suggestions = {
            1: [
                "Ensure you have a stable internet connection",
                "Verify your GitHub token is set correctly",
                "Select the appropriate project for your assignment",
                "Review project requirements before starting"
            ],
            2: [
                "Check that the dataset downloaded successfully",
                "Verify the dataset file format and content",
                "Ensure you have the required Python packages installed",
                "Review the project template structure"
            ],
            3: [
                "Complete all sections of the Jupyter notebook",
                "Execute all code cells to generate outputs",
                "Add meaningful comments and documentation",
                "Test your code with the provided dataset"
            ],
            4: [
                "Verify your GitHub repository was created successfully",
                "Check that all files were uploaded correctly",
                "Ensure repository is publicly accessible",
                "Review the generated README file"
            ],
            5: [
                "Run final validation to check completeness",
                "Review submission checklist",
                "Prepare for LMS submission",
                "Keep repository URL for submission"
            ]
        }
        
        return step_suggestions.get(current_step, [
            "Follow the workflow step-by-step",
            "Check progress regularly",
            "Address any validation issues promptly",
            "Keep backups of your work"
        ])