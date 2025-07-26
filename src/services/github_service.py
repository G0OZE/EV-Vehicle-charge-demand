"""GitHub API integration service for repository management and file operations."""

import requests
import base64
import json
from typing import Dict, Any, Optional, List
import time

try:
    from ..utils.config import config
except ImportError:
    # Fallback for direct imports
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.config import config

print("GitHub service module loaded successfully")


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
        self.token = token or config.get('github.token')
        self.username = username or config.get('github.username')
        self.base_url = config.get('github.base_url', 'https://api.github.com')
        
        if not self.token or not self.username:
            raise GitHubAPIError("GitHub token and username are required")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': f'AICTE-Workflow-Tool/{self.username}'
        })
        
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to GitHub API with error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if self.rate_limit_remaining is not None and self.rate_limit_remaining < 10:
            if self.rate_limit_reset and time.time() < self.rate_limit_reset:
                wait_time = self.rate_limit_reset - time.time()
                raise GitHubAPIError(f"Rate limit exceeded. Reset in {wait_time:.0f} seconds")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=config.get('workflow.timeout_seconds', 30)
            )
            
            self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
            
            if response.status_code == 404:
                raise GitHubAPIError(f"Resource not found: {endpoint}", response.status_code)
            elif response.status_code == 403:
                raise GitHubAPIError("Access forbidden - check token permissions", response.status_code)
            elif response.status_code == 401:
                raise GitHubAPIError("Authentication failed - check token validity", response.status_code)
            elif not response.ok:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('message', f'HTTP {response.status_code}')
                raise GitHubAPIError(error_message, response.status_code, error_data)
            
            return response.json() if response.content else {}
            
        except requests.exceptions.Timeout:
            raise GitHubAPIError("Request timeout - GitHub API may be slow")
        except requests.exceptions.ConnectionError:
            raise GitHubAPIError("Connection error - check internet connectivity")
        except requests.exceptions.RequestException as e:
            raise GitHubAPIError(f"Request failed: {str(e)}")
    
    def create_repository(self, name: str, description: str = "", private: bool = False) -> Dict[str, Any]:
        """Create a new GitHub repository."""
        data = {
            'name': name,
            'description': description,
            'private': private,
            'auto_init': False,
            'has_issues': True,
            'has_projects': False,
            'has_wiki': False
        }
        
        try:
            repo_data = self._make_request('POST', '/user/repos', data=data)
            return repo_data
        except GitHubAPIError as e:
            if e.status_code == 422 and 'already exists' in str(e):
                return self.get_repository(name)
            raise GitHubAPIError(f"Failed to create repository '{name}': {str(e)}")
    
    def get_repository(self, name: str) -> Dict[str, Any]:
        """Get repository information."""
        return self._make_request('GET', f'/repos/{self.username}/{name}')
    
    def upload_file(self, repo_name: str, file_path: str, content: str, 
                   commit_message: str = None) -> Dict[str, Any]:
        """Upload a file to GitHub repository."""
        if commit_message is None:
            commit_message = f"Add {file_path}"
        
        content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            'message': commit_message,
            'content': content_encoded
        }
        
        try:
            existing_file = self._make_request('GET', f'/repos/{self.username}/{repo_name}/contents/{file_path}')
            data['sha'] = existing_file['sha']
            data['message'] = f"Update {file_path}"
        except GitHubAPIError:
            pass
        
        return self._make_request('PUT', f'/repos/{self.username}/{repo_name}/contents/{file_path}', data=data)
    
    def initialize_readme(self, repo_name: str, content: str) -> Dict[str, Any]:
        """Create or update README file in repository."""
        return self.upload_file(repo_name, 'README.md', content, 'Initialize README')
    
    def get_repository_url(self, repo_name: str) -> str:
        """Get repository URL."""
        return f"https://github.com/{self.username}/{repo_name}"
    
    def list_repositories(self) -> List[Dict[str, Any]]:
        """List user's repositories."""
        return self._make_request('GET', '/user/repos', params={'per_page': 100})
    
    def delete_repository(self, repo_name: str) -> bool:
        """Delete a repository (use with caution)."""
        try:
            self._make_request('DELETE', f'/repos/{self.username}/{repo_name}')
            return True
        except GitHubAPIError:
            return False
    
    def upload_file_from_path(self, repo_name: str, local_file_path: str, 
                             remote_file_path: str = None, commit_message: str = None) -> Dict[str, Any]:
        """Upload a file from local filesystem to GitHub repository."""
        import os
        
        if not os.path.exists(local_file_path):
            raise GitHubAPIError(f"Local file not found: {local_file_path}")
        
        if remote_file_path is None:
            remote_file_path = os.path.basename(local_file_path)
        
        # Determine if file is binary based on extension
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz', '.exe', '.bin'}
        file_ext = os.path.splitext(local_file_path)[1].lower()
        
        if file_ext in binary_extensions:
            return self._upload_binary_file(repo_name, local_file_path, remote_file_path, commit_message)
        else:
            # Read as text file
            try:
                with open(local_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return self.upload_file(repo_name, remote_file_path, content, commit_message)
            except UnicodeDecodeError:
                # Fallback to binary if text reading fails
                return self._upload_binary_file(repo_name, local_file_path, remote_file_path, commit_message)
    
    def _upload_binary_file(self, repo_name: str, local_file_path: str, 
                           remote_file_path: str, commit_message: str = None) -> Dict[str, Any]:
        """Upload a binary file to GitHub repository."""
        import os
        
        if commit_message is None:
            commit_message = f"Add {remote_file_path}"
        
        with open(local_file_path, 'rb') as f:
            content_bytes = f.read()
        
        content_encoded = base64.b64encode(content_bytes).decode('utf-8')
        
        data = {
            'message': commit_message,
            'content': content_encoded
        }
        
        try:
            existing_file = self._make_request('GET', f'/repos/{self.username}/{repo_name}/contents/{remote_file_path}')
            data['sha'] = existing_file['sha']
            data['message'] = f"Update {remote_file_path}"
        except GitHubAPIError:
            pass
        
        return self._make_request('PUT', f'/repos/{self.username}/{repo_name}/contents/{remote_file_path}', data=data)
    
    def upload_notebook_and_dataset(self, repo_name: str, notebook_path: str, 
                                   dataset_path: str = None) -> Dict[str, Any]:
        """Upload notebook and dataset files to repository with error handling and retries."""
        results = {
            'notebook': None,
            'dataset': None,
            'errors': []
        }
        
        # Upload notebook file
        try:
            results['notebook'] = self._upload_with_retry(
                repo_name, notebook_path, 
                commit_message="Add project notebook"
            )
        except GitHubAPIError as e:
            error_msg = f"Failed to upload notebook: {str(e)}"
            results['errors'].append(error_msg)
            if e.status_code in [403, 401]:
                raise GitHubAPIError(f"Authentication error while uploading notebook: {str(e)}")
        
        # Upload dataset file if provided
        if dataset_path:
            try:
                results['dataset'] = self._upload_with_retry(
                    repo_name, dataset_path,
                    commit_message="Add project dataset"
                )
            except GitHubAPIError as e:
                error_msg = f"Failed to upload dataset: {str(e)}"
                results['errors'].append(error_msg)
                # Don't fail the entire operation if only dataset upload fails
        
        return results
    
    def _upload_with_retry(self, repo_name: str, file_path: str, 
                          commit_message: str = None, max_retries: int = 3) -> Dict[str, Any]:
        """Upload file with retry logic for rate limits and transient failures."""
        import time
        import random
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self.upload_file_from_path(repo_name, file_path, None, commit_message)
            except GitHubAPIError as e:
                last_error = e
                
                # Check if this is a retryable error
                is_rate_limit = e.status_code == 403 and "rate limit" in str(e).lower()
                is_server_error = e.status_code in [500, 502, 503, 504]
                
                if (is_rate_limit or is_server_error) and attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
                    continue
                else:
                    # Non-retryable error or max retries reached
                    break
        
        # If we get here, all retries failed
        if last_error:
            if last_error.status_code in [403, 500, 502, 503, 504]:
                raise GitHubAPIError(f"Failed to upload {file_path} after {max_retries} attempts")
            else:
                # Re-raise original error for non-retryable cases
                raise last_error
        
        raise GitHubAPIError(f"Failed to upload {file_path} after {max_retries} attempts")
    
    def generate_submission_url(self, repo_name: str, include_files: bool = True) -> Dict[str, str]:
        """Generate repository URL and file links for LMS submission."""
        base_url = self.get_repository_url(repo_name)
        
        submission_info = {
            'repository_url': base_url,
            'submission_link': base_url,  # Main link for LMS submission
        }
        
        if include_files:
            # Add direct links to key files
            submission_info.update({
                'notebook_url': f"{base_url}/blob/main/notebook.ipynb",
                'dataset_url': f"{base_url}/blob/main/dataset.csv",
                'readme_url': f"{base_url}/blob/main/README.md"
            })
        
        return submission_info
    
    def validate_repository_for_submission(self, repo_name: str) -> Dict[str, Any]:
        """Validate repository has all required files for submission."""
        validation_result = {
            'is_valid': True,
            'missing_files': [],
            'errors': [],
            'files_found': []
        }
        
        required_files = ['README.md']
        optional_files = ['notebook.ipynb', 'dataset.csv', 'requirements.txt']
        
        # Check for required and optional files
        all_files = required_files + optional_files
        
        for file_path in all_files:
            try:
                file_info = self._make_request('GET', f'/repos/{self.username}/{repo_name}/contents/{file_path}')
                validation_result['files_found'].append({
                    'path': file_path,
                    'size': file_info.get('size', 0),
                    'sha': file_info.get('sha', '')
                })
            except GitHubAPIError as e:
                if e.status_code == 404:
                    if file_path in required_files:
                        validation_result['missing_files'].append(file_path)
                        validation_result['is_valid'] = False
                else:
                    validation_result['errors'].append(f"Error checking {file_path}: {str(e)}")
        
        return validation_result
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return self._make_request('GET', '/rate_limit')
    
    def is_authenticated(self) -> bool:
        """Check if the service is properly authenticated."""
        try:
            # Try to get user information to verify authentication
            self._make_request('GET', '/user')
            return True
        except GitHubAPIError:
            return False