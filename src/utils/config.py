"""
Configuration management for API keys and application settings.
"""
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path


class ConfigManager:
    """Manages application configuration and API keys."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config_data: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Load from config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
                self.config_data = {}
        
        # Override with environment variables
        self._load_from_environment()
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            'GITHUB_TOKEN': 'github.token',
            'GITHUB_USERNAME': 'github.username',
            'PROGRESS_FILE': 'workflow.progress_file',
            'DEFAULT_PROJECT_DIR': 'workflow.project_directory',
            'LOG_LEVEL': 'logging.level'
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(config_key, value)
    
    def _set_nested_value(self, key_path: str, value: Any) -> None:
        """Set a nested configuration value using dot notation."""
        keys = key_path.split('.')
        current = self.config_data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key_path.split('.')
        current = self.config_data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        self._set_nested_value(key_path, value)
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config_data, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_github_config(self) -> Dict[str, str]:
        """Get GitHub-specific configuration."""
        return {
            'token': self.get('github.token', ''),
            'username': self.get('github.username', ''),
            'base_url': self.get('github.base_url', 'https://api.github.com')
        }
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow-specific configuration."""
        return {
            'progress_file': self.get('workflow.progress_file', 'workflow_progress.json'),
            'project_directory': self.get('workflow.project_directory', './projects'),
            'max_retries': self.get('workflow.max_retries', 3),
            'timeout_seconds': self.get('workflow.timeout_seconds', 30)
        }
    
    def validate_required_config(self) -> List[str]:
        """Validate that required configuration is present."""
        required_keys = [
            'github.token',
            'github.username'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not self.get(key):
                missing_keys.append(key)
        
        return missing_keys


# Global configuration instance
config = ConfigManager()