#!/usr/bin/env python3

# Standalone GitHub service test
import requests
import base64
import json
from typing import Dict, Any, Optional, List
import time


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class GitHubService:
    """GitHub API client for repository management and file operations."""
    
    def __init__(self, token: Optional[str] = None, username: Optional[str] = None):
        """Initialize GitHub service with authentication."""
        self.token = token or "dummy_token"
        self.username = username or "dummy_user"
        self.base_url = 'https://api.github.com'
        
        if not self.token or not self.username:
            raise GitHubAPIError("GitHub token and username are required")
        
        print(f"GitHubService initialized with username: {self.username}")
    
    def get_repository_url(self, repo_name: str) -> str:
        """Get repository URL."""
        return f"https://github.com/{self.username}/{repo_name}"


# Test the classes
if __name__ == "__main__":
    try:
        print("Testing GitHubService...")
        
        # Test GitHubAPIError
        error = GitHubAPIError("Test error", 404)
        print(f"✓ GitHubAPIError created: {error}")
        
        # Test GitHubService
        service = GitHubService("test_token", "test_user")
        print("✓ GitHubService created successfully")
        
        # Test method
        url = service.get_repository_url("test-repo")
        print(f"✓ Repository URL: {url}")
        
        print("All tests passed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()