"""
Configuration validation and setup utilities.
Validates configuration files, environment setup, and system requirements.
"""
import os
import json
import re
import requests
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urlparse

from .config import ConfigManager


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""
    pass


class ConfigValidator:
    """Validates configuration files and system setup."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all configuration aspects.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        # Validate different configuration sections
        self._validate_github_config()
        self._validate_workflow_config()
        self._validate_logging_config()
        self._validate_security_config()
        self._validate_performance_config()
        self._validate_system_requirements()
        self._validate_file_permissions()
        
        return len(self.validation_errors) == 0, self.validation_errors, self.validation_warnings
    
    def _validate_github_config(self) -> None:
        """Validate GitHub configuration."""
        github_config = self.config.get_github_config()
        
        # Check if token is provided
        if not github_config.get('token'):
            self.validation_errors.append("GitHub token is required but not provided")
            return
        
        # Validate token format
        token = github_config['token']
        if not self._is_valid_github_token_format(token):
            self.validation_errors.append("GitHub token format is invalid")
        
        # Check if username is provided
        if not github_config.get('username'):
            self.validation_warnings.append("GitHub username not provided - will be auto-detected")
        
        # Validate GitHub API connectivity
        try:
            self._test_github_connectivity(github_config)
        except Exception as e:
            self.validation_errors.append(f"GitHub API connectivity test failed: {e}")
    
    def _validate_workflow_config(self) -> None:
        """Validate workflow configuration."""
        workflow_config = self.config.get_workflow_config()
        
        # Validate project directory
        project_dir = Path(workflow_config.get('project_directory', './projects'))
        if not project_dir.exists():
            try:
                project_dir.mkdir(parents=True, exist_ok=True)
                self.validation_warnings.append(f"Created project directory: {project_dir}")
            except Exception as e:
                self.validation_errors.append(f"Cannot create project directory {project_dir}: {e}")
        
        # Validate numeric settings
        max_retries = workflow_config.get('max_retries', 3)
        if not isinstance(max_retries, int) or max_retries < 1:
            self.validation_errors.append("max_retries must be a positive integer")
        
        timeout_seconds = workflow_config.get('timeout_seconds', 30)
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            self.validation_errors.append("timeout_seconds must be a positive number")
        
        # Validate progress file location
        progress_file = workflow_config.get('progress_file', 'workflow_progress.json')
        progress_path = Path(progress_file)
        if progress_path.exists() and not os.access(progress_path, os.R_OK | os.W_OK):
            self.validation_errors.append(f"Progress file {progress_file} is not readable/writable")
    
    def _validate_logging_config(self) -> None:
        """Validate logging configuration."""
        log_level = self.config.get('logging.level', 'INFO')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level.upper() not in valid_levels:
            self.validation_errors.append(f"Invalid log level: {log_level}. Must be one of {valid_levels}")
        
        # Validate log file path
        log_file = self.config.get('logging.file', 'logs/workflow.log')
        log_path = Path(log_file)
        
        # Create log directory if it doesn't exist
        if not log_path.parent.exists():
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                self.validation_warnings.append(f"Created log directory: {log_path.parent}")
            except Exception as e:
                self.validation_errors.append(f"Cannot create log directory {log_path.parent}: {e}")
        
        # Check log file permissions
        if log_path.exists() and not os.access(log_path, os.W_OK):
            self.validation_errors.append(f"Log file {log_file} is not writable")
        
        # Validate log file size limits
        max_size_mb = self.config.get('logging.max_file_size_mb', 10)
        if not isinstance(max_size_mb, (int, float)) or max_size_mb <= 0:
            self.validation_errors.append("logging.max_file_size_mb must be a positive number")
        
        backup_count = self.config.get('logging.backup_count', 5)
        if not isinstance(backup_count, int) or backup_count < 0:
            self.validation_errors.append("logging.backup_count must be a non-negative integer")
    
    def _validate_security_config(self) -> None:
        """Validate security configuration."""
        # Check if encryption is enabled for sensitive data
        encrypt_progress = self.config.get('security.encrypt_progress_files', False)
        if encrypt_progress:
            # Validate encryption key is available
            encryption_key = os.getenv('WORKFLOW_ENCRYPTION_KEY')
            if not encryption_key:
                self.validation_errors.append("Encryption enabled but WORKFLOW_ENCRYPTION_KEY not set")
        
        # Validate file type restrictions
        validate_file_types = self.config.get('security.validate_file_types', True)
        if validate_file_types:
            allowed_extensions = self.config.get('security.allowed_file_extensions', 
                                               ['.csv', '.json', '.ipynb', '.py', '.md'])
            if not isinstance(allowed_extensions, list):
                self.validation_errors.append("security.allowed_file_extensions must be a list")
        
        # Validate file size limits
        max_file_size_mb = self.config.get('security.max_file_size_mb', 100)
        if not isinstance(max_file_size_mb, (int, float)) or max_file_size_mb <= 0:
            self.validation_errors.append("security.max_file_size_mb must be a positive number")
    
    def _validate_performance_config(self) -> None:
        """Validate performance configuration."""
        # Validate concurrent operations limits
        concurrent_uploads = self.config.get('performance.concurrent_uploads', 3)
        if not isinstance(concurrent_uploads, int) or concurrent_uploads < 1:
            self.validation_errors.append("performance.concurrent_uploads must be a positive integer")
        
        connection_pool_size = self.config.get('performance.connection_pool_size', 10)
        if not isinstance(connection_pool_size, int) or connection_pool_size < 1:
            self.validation_errors.append("performance.connection_pool_size must be a positive integer")
        
        # Validate cache settings
        cache_enabled = self.config.get('performance.cache_enabled', True)
        if cache_enabled:
            cache_size_mb = self.config.get('performance.cache_size_mb', 50)
            if not isinstance(cache_size_mb, (int, float)) or cache_size_mb <= 0:
                self.validation_errors.append("performance.cache_size_mb must be a positive number")
    
    def _validate_system_requirements(self) -> None:
        """Validate system requirements."""
        import sys
        import platform
        
        # Check Python version
        python_version = sys.version_info
        min_version = (3, 8)
        if python_version < min_version:
            self.validation_errors.append(
                f"Python {min_version[0]}.{min_version[1]}+ required, "
                f"but {python_version.major}.{python_version.minor} found"
            )
        
        # Check available disk space
        import shutil
        try:
            free_space = shutil.disk_usage('.').free
            min_space = 100 * 1024 * 1024  # 100MB
            if free_space < min_space:
                self.validation_warnings.append(
                    f"Low disk space: {free_space // (1024*1024)}MB available, "
                    f"recommend at least {min_space // (1024*1024)}MB"
                )
        except Exception:
            self.validation_warnings.append("Could not check available disk space")
        
        # Check if required packages are available
        required_packages = [
            'requests', 'click', 'colorama', 'python-dotenv', 'cryptography'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                self.validation_errors.append(f"Required package '{package}' not installed")
    
    def _validate_file_permissions(self) -> None:
        """Validate file and directory permissions."""
        # Check write permissions for key directories
        directories_to_check = [
            self.config.get('workflow.project_directory', './projects'),
            'logs',
            'temp',
            'backups'
        ]
        
        for dir_path in directories_to_check:
            path = Path(dir_path)
            if path.exists():
                if not os.access(path, os.W_OK):
                    self.validation_errors.append(f"No write permission for directory: {path}")
            else:
                # Try to create the directory
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self.validation_warnings.append(f"Created directory: {path}")
                except Exception as e:
                    self.validation_errors.append(f"Cannot create directory {path}: {e}")
    
    def _is_valid_github_token_format(self, token: str) -> bool:
        """Check if GitHub token has valid format."""
        # GitHub personal access tokens start with 'ghp_' and are 40 characters
        # GitHub app tokens start with 'ghs_' and are 40 characters
        # Classic tokens are 40 character hex strings
        if token.startswith(('ghp_', 'ghs_')):
            return len(token) == 40
        elif re.match(r'^[a-f0-9]{40}$', token):
            return True
        else:
            return False
    
    def _test_github_connectivity(self, github_config: Dict[str, str]) -> None:
        """Test GitHub API connectivity."""
        headers = {
            'Authorization': f"token {github_config['token']}",
            'Accept': 'application/vnd.github.v3+json'
        }
        
        base_url = github_config.get('base_url', 'https://api.github.com')
        response = requests.get(f"{base_url}/user", headers=headers, timeout=10)
        
        if response.status_code == 401:
            raise ConfigValidationError("GitHub token authentication failed")
        elif response.status_code == 403:
            raise ConfigValidationError("GitHub API rate limit exceeded or insufficient permissions")
        elif response.status_code != 200:
            raise ConfigValidationError(f"GitHub API returned status {response.status_code}")
        
        # Verify token has required scopes
        scopes = response.headers.get('X-OAuth-Scopes', '').split(', ')
        required_scopes = ['repo']
        missing_scopes = [scope for scope in required_scopes if scope not in scopes]
        
        if missing_scopes:
            self.validation_warnings.append(
                f"GitHub token missing recommended scopes: {', '.join(missing_scopes)}"
            )


class ConfigSetup:
    """Handles initial configuration setup and templates."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
    
    def create_config_templates(self) -> None:
        """Create configuration templates for different environments."""
        templates = {
            'development': self._get_development_template(),
            'production': self._get_production_template(),
            'testing': self._get_testing_template()
        }
        
        for env, template in templates.items():
            template_file = self.config_dir / f"config.{env}.json"
            with open(template_file, 'w') as f:
                json.dump(template, f, indent=2)
            print(f"Created {template_file}")
    
    def _get_development_template(self) -> Dict[str, Any]:
        """Get development configuration template."""
        return {
            "github": {
                "token": "",
                "username": "",
                "base_url": "https://api.github.com",
                "timeout_seconds": 30,
                "max_retries": 3
            },
            "workflow": {
                "project_directory": "./projects",
                "progress_file": "workflow_progress.json",
                "backup_enabled": True,
                "backup_interval_hours": 24,
                "auto_cleanup_days": 7
            },
            "logging": {
                "level": "DEBUG",
                "file": "logs/workflow.log",
                "console_output": True,
                "max_file_size_mb": 10,
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "security": {
                "encrypt_progress_files": False,
                "validate_file_types": True,
                "allowed_file_extensions": [".csv", ".json", ".ipynb", ".py", ".md"],
                "max_file_size_mb": 100
            },
            "performance": {
                "concurrent_uploads": 2,
                "connection_pool_size": 5,
                "cache_enabled": True,
                "cache_size_mb": 25
            }
        }
    
    def _get_production_template(self) -> Dict[str, Any]:
        """Get production configuration template."""
        return {
            "github": {
                "token": "",
                "username": "",
                "base_url": "https://api.github.com",
                "timeout_seconds": 60,
                "max_retries": 5,
                "rate_limit_buffer": 100
            },
            "workflow": {
                "project_directory": "./projects",
                "progress_file": "workflow_progress.json",
                "backup_enabled": True,
                "backup_interval_hours": 6,
                "auto_cleanup_days": 30
            },
            "logging": {
                "level": "INFO",
                "file": "logs/workflow.log",
                "console_output": False,
                "max_file_size_mb": 50,
                "backup_count": 10,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            },
            "security": {
                "encrypt_progress_files": True,
                "validate_file_types": True,
                "allowed_file_extensions": [".csv", ".json", ".ipynb"],
                "max_file_size_mb": 50
            },
            "performance": {
                "concurrent_uploads": 5,
                "connection_pool_size": 20,
                "cache_enabled": True,
                "cache_size_mb": 100
            }
        }
    
    def _get_testing_template(self) -> Dict[str, Any]:
        """Get testing configuration template."""
        return {
            "github": {
                "token": "test_token",
                "username": "test_user",
                "base_url": "https://api.github.com",
                "timeout_seconds": 10,
                "max_retries": 1
            },
            "workflow": {
                "project_directory": "./test_projects",
                "progress_file": "test_progress.json",
                "backup_enabled": False,
                "auto_cleanup_days": 1
            },
            "logging": {
                "level": "DEBUG",
                "file": "logs/test.log",
                "console_output": True,
                "max_file_size_mb": 5,
                "backup_count": 2
            },
            "security": {
                "encrypt_progress_files": False,
                "validate_file_types": False,
                "max_file_size_mb": 10
            },
            "performance": {
                "concurrent_uploads": 1,
                "connection_pool_size": 2,
                "cache_enabled": False
            }
        }
    
    def create_environment_file(self) -> None:
        """Create .env template file."""
        env_content = """# EV Charge Demand Analysis Environment Variables
# Copy this file to .env and fill in your values

# GitHub Configuration (Required)
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_USERNAME=your_github_username

# Optional: Override default configuration
# LOG_LEVEL=INFO
# DEFAULT_PROJECT_DIR=./projects
# PROGRESS_FILE=workflow_progress.json
# MAX_RETRIES=3
# TIMEOUT_SECONDS=30

# Security (Optional)
# WORKFLOW_ENCRYPTION_KEY=your_32_character_encryption_key
# VALIDATE_FILE_TYPES=true
# MAX_FILE_SIZE_MB=100

# Performance (Optional)
# CONCURRENT_UPLOADS=3
# CONNECTION_POOL_SIZE=10
# CACHE_ENABLED=true

# Development/Debug (Optional)
# DEBUG_MODE=false
# VERBOSE_LOGGING=false
# MOCK_GITHUB_API=false
"""
        
        env_file = Path(".env.template")
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"Created {env_file}")


def validate_configuration(config_file: str = "config.json") -> bool:
    """
    Validate configuration and print results.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        config_manager = ConfigManager(config_file)
        validator = ConfigValidator(config_manager)
        
        is_valid, errors, warnings = validator.validate_all()
        
        if warnings:
            print("⚠️  Configuration Warnings:")
            for warning in warnings:
                print(f"   • {warning}")
            print()
        
        if errors:
            print("❌ Configuration Errors:")
            for error in errors:
                print(f"   • {error}")
            print()
            print("Please fix the above errors before proceeding.")
            return False
        else:
            print("✅ Configuration validation passed!")
            return True
            
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "config.json"
    
    success = validate_configuration(config_file)
    sys.exit(0 if success else 1)