"""
Unit tests for GitHub service with mocked API responses.
"""
import pytest
import json
import base64
import requests
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from src.services.github_service import GitHubService, GitHubAPIError


class TestGitHubService:
    """Test cases for GitHubService class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        with patch('src.services.github_service.config') as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                'github.token': 'test_token_123',
                'github.username': 'testuser',
                'github.base_url': 'https://api.github.com',
                'workflow.timeout_seconds': 30
            }.get(key, default)
            yield mock_config
    
    @pytest.fixture
    def github_service(self, mock_config):
        """Create GitHubService instance for testing."""
        return GitHubService()
    
    @pytest.fixture
    def mock_response(self):
        """Create mock response object."""
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.headers = {
            'X-RateLimit-Remaining': '5000',
            'X-RateLimit-Reset': '1234567890'
        }
        response.content = True
        response.json.return_value = {'test': 'data'}
        return response
    
    def test_init_with_credentials(self, mock_config):
        """Test GitHubService initialization with provided credentials."""
        service = GitHubService(token='custom_token', username='custom_user')
        assert service.token == 'custom_token'
        assert service.username == 'custom_user'
        assert service.base_url == 'https://api.github.com'
    
    def test_init_without_credentials_raises_error(self):
        """Test GitHubService initialization without credentials raises error."""
        with patch('src.services.github_service.config') as mock_config:
            mock_config.get.return_value = None
            with pytest.raises(GitHubAPIError, match="GitHub token and username are required"):
                GitHubService()
    
    def test_init_sets_session_headers(self, github_service):
        """Test that session headers are properly set."""
        headers = github_service.session.headers
        assert headers['Authorization'] == 'token test_token_123'
        assert headers['Accept'] == 'application/vnd.github.v3+json'
        assert 'EV-Analysis-Tool/testuser' in headers['User-Agent']
    
    @patch('src.services.github_service.requests.Session.request')
    def test_make_request_success(self, mock_request, github_service, mock_response):
        """Test successful API request."""
        mock_request.return_value = mock_response
        
        result = github_service._make_request('GET', '/test/endpoint')
        
        assert result == {'test': 'data'}
        mock_request.assert_called_once_with(
            method='GET',
            url='https://api.github.com/test/endpoint',
            json=None,
            params=None,
            timeout=30
        )
    
    @patch('src.services.github_service.requests.Session.request')
    def test_make_request_404_error(self, mock_request, github_service):
        """Test 404 error handling."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        with pytest.raises(GitHubAPIError, match="Resource not found"):
            github_service._make_request('GET', '/nonexistent')
    
    @patch('src.services.github_service.requests.Session.request')
    def test_make_request_403_error(self, mock_request, github_service):
        """Test 403 forbidden error handling."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 403
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        with pytest.raises(GitHubAPIError, match="Access forbidden"):
            github_service._make_request('GET', '/forbidden')
    
    @patch('src.services.github_service.requests.Session.request')
    def test_make_request_401_error(self, mock_request, github_service):
        """Test 401 authentication error handling."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        with pytest.raises(GitHubAPIError, match="Authentication failed"):
            github_service._make_request('GET', '/unauthorized')
    
    @patch('src.services.github_service.requests.Session.request')
    def test_make_request_rate_limit_exceeded(self, mock_request, github_service):
        """Test rate limit handling."""
        github_service.rate_limit_remaining = 5
        github_service.rate_limit_reset = 9999999999  # Future timestamp
        
        with pytest.raises(GitHubAPIError, match="Rate limit exceeded"):
            github_service._make_request('GET', '/test')
    
    @patch('src.services.github_service.requests.Session.request')
    def test_make_request_timeout_error(self, mock_request, github_service):
        """Test timeout error handling."""
        mock_request.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(GitHubAPIError, match="Request timeout"):
            github_service._make_request('GET', '/test')
    
    @patch('src.services.github_service.requests.Session.request')
    def test_make_request_connection_error(self, mock_request, github_service):
        """Test connection error handling."""
        mock_request.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(GitHubAPIError, match="Connection error"):
            github_service._make_request('GET', '/test')
    
    def test_create_repository_success(self, github_service):
        """Test successful repository creation."""
        expected_repo_data = {
            'name': 'test-repo',
            'full_name': 'testuser/test-repo',
            'html_url': 'https://github.com/testuser/test-repo'
        }
        
        with patch.object(github_service, '_make_request') as mock_request:
            mock_request.return_value = expected_repo_data
            
            result = github_service.create_repository('test-repo', 'Test repository')
            
            assert result == expected_repo_data
            mock_request.assert_called_once_with('POST', '/user/repos', data={
                'name': 'test-repo',
                'description': 'Test repository',
                'private': False,
                'auto_init': False,
                'has_issues': True,
                'has_projects': False,
                'has_wiki': False
            })
    
    def test_create_repository_already_exists(self, github_service):
        """Test repository creation when repository already exists."""
        existing_repo_data = {
            'name': 'existing-repo',
            'full_name': 'testuser/existing-repo'
        }
        
        with patch.object(github_service, '_make_request') as mock_request:
            # First call (create) fails with 422, second call (get) succeeds
            mock_request.side_effect = [
                GitHubAPIError("already exists", 422),
                existing_repo_data
            ]
            
            result = github_service.create_repository('existing-repo')
            
            assert result == existing_repo_data
            assert mock_request.call_count == 2
    
    def test_get_repository(self, github_service):
        """Test getting repository information."""
        repo_data = {'name': 'test-repo', 'full_name': 'testuser/test-repo'}
        
        with patch.object(github_service, '_make_request') as mock_request:
            mock_request.return_value = repo_data
            
            result = github_service.get_repository('test-repo')
            
            assert result == repo_data
            mock_request.assert_called_once_with('GET', '/repos/testuser/test-repo')
    
    def test_initialize_readme(self, github_service):
        """Test README initialization."""
        with patch.object(github_service, 'upload_file') as mock_upload:
            mock_upload.return_value = {'path': 'README.md'}
            
            result = github_service.initialize_readme('test-repo', '# Test Project')
            
            assert result == {'path': 'README.md'}
            mock_upload.assert_called_once_with(
                'test-repo', 'README.md', '# Test Project', 'Initialize README'
            )
    
    def test_upload_file_new_file(self, github_service):
        """Test uploading a new file."""
        expected_response = {'path': 'test.txt', 'sha': 'abc123'}
        
        with patch.object(github_service, '_make_request') as mock_request:
            # First call (check existing) fails, second call (upload) succeeds
            mock_request.side_effect = [
                GitHubAPIError("Not found", 404),
                expected_response
            ]
            
            result = github_service.upload_file('test-repo', 'test.txt', 'Hello World')
            
            assert result == expected_response
            
            # Check the upload call
            upload_call = mock_request.call_args_list[1]
            assert upload_call[0] == ('PUT', '/repos/testuser/test-repo/contents/test.txt')
            
            upload_data = upload_call[1]['data']
            assert upload_data['message'] == 'Add test.txt'
            assert upload_data['content'] == base64.b64encode(b'Hello World').decode('utf-8')
            assert 'sha' not in upload_data  # New file, no SHA
    
    def test_upload_file_update_existing(self, github_service):
        """Test updating an existing file."""
        existing_file_data = {'sha': 'existing_sha_123'}
        expected_response = {'path': 'test.txt', 'sha': 'new_sha_456'}
        
        with patch.object(github_service, '_make_request') as mock_request:
            # First call (check existing) succeeds, second call (upload) succeeds
            mock_request.side_effect = [existing_file_data, expected_response]
            
            result = github_service.upload_file('test-repo', 'test.txt', 'Updated content')
            
            assert result == expected_response
            
            # Check the upload call
            upload_call = mock_request.call_args_list[1]
            upload_data = upload_call[1]['data']
            assert upload_data['message'] == 'Update test.txt'
            assert upload_data['sha'] == 'existing_sha_123'  # Existing file SHA
    
    def test_upload_file_from_path_text_file(self, github_service):
        """Test uploading a text file from local path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write('Test file content')
            temp_file_path = temp_file.name
        
        try:
            with patch.object(github_service, 'upload_file') as mock_upload:
                mock_upload.return_value = {'path': 'uploaded.txt'}
                
                result = github_service.upload_file_from_path(
                    'test-repo', temp_file_path, 'uploaded.txt'
                )
                
                assert result == {'path': 'uploaded.txt'}
                mock_upload.assert_called_once_with(
                    'test-repo', 'uploaded.txt', 'Test file content', None
                )
        finally:
            os.unlink(temp_file_path)
    
    def test_upload_file_from_path_nonexistent_file(self, github_service):
        """Test uploading nonexistent file raises error."""
        with pytest.raises(GitHubAPIError, match="Local file not found"):
            github_service.upload_file_from_path('test-repo', '/nonexistent/file.txt')
    
    def test_upload_file_from_path_binary_file(self, github_service):
        """Test uploading a binary file from local path."""
        binary_content = b'\x89PNG\r\n\x1a\n'  # PNG header
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as temp_file:
            temp_file.write(binary_content)
            temp_file_path = temp_file.name
        
        try:
            with patch.object(github_service, '_upload_binary_file') as mock_upload_binary:
                mock_upload_binary.return_value = {'path': 'image.png'}
                
                result = github_service.upload_file_from_path(
                    'test-repo', temp_file_path, 'image.png'
                )
                
                assert result == {'path': 'image.png'}
                mock_upload_binary.assert_called_once()
        finally:
            os.unlink(temp_file_path)
    
    def test_get_repository_url(self, github_service):
        """Test repository URL generation."""
        url = github_service.get_repository_url('test-repo')
        assert url == 'https://github.com/testuser/test-repo'
    
    def test_delete_repository_success(self, github_service):
        """Test successful repository deletion."""
        with patch.object(github_service, '_make_request') as mock_request:
            mock_request.return_value = {}
            
            result = github_service.delete_repository('test-repo')
            
            assert result is True
            mock_request.assert_called_once_with('DELETE', '/repos/testuser/test-repo')
    
    def test_delete_repository_failure(self, github_service):
        """Test repository deletion failure."""
        with patch.object(github_service, '_make_request') as mock_request:
            mock_request.side_effect = GitHubAPIError("Not found")
            
            result = github_service.delete_repository('test-repo')
            
            assert result is False
    
    def test_list_repositories(self, github_service):
        """Test listing user repositories."""
        repo_list = [
            {'name': 'repo1', 'full_name': 'testuser/repo1'},
            {'name': 'repo2', 'full_name': 'testuser/repo2'}
        ]
        
        with patch.object(github_service, '_make_request') as mock_request:
            mock_request.return_value = repo_list
            
            result = github_service.list_repositories()
            
            assert result == repo_list
            mock_request.assert_called_once_with('GET', '/user/repos', params={'per_page': 100})
    
    def test_get_rate_limit_status(self, github_service):
        """Test getting rate limit status."""
        rate_limit_data = {
            'rate': {
                'limit': 5000,
                'remaining': 4999,
                'reset': 1234567890
            }
        }
        
        with patch.object(github_service, '_make_request') as mock_request:
            mock_request.return_value = rate_limit_data
            
            result = github_service.get_rate_limit_status()
            
            assert result == rate_limit_data
            mock_request.assert_called_once_with('GET', '/rate_limit')


class TestGitHubAPIError:
    """Test cases for GitHubAPIError exception."""
    
    def test_basic_error(self):
        """Test basic error creation."""
        error = GitHubAPIError("Test error")
        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.response_data is None
    
    def test_error_with_status_code(self):
        """Test error with status code."""
        error = GitHubAPIError("API error", status_code=404)
        assert str(error) == "API error"
        assert error.status_code == 404
    
    def test_error_with_response_data(self):
        """Test error with response data."""
        response_data = {'message': 'Not found', 'documentation_url': 'https://docs.github.com'}
        error = GitHubAPIError("Not found", status_code=404, response_data=response_data)
        assert error.response_data == response_data


# Integration test fixtures and helpers
@pytest.fixture
def temp_test_file():
    """Create a temporary test file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write('Test content for integration testing')
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


class TestGitHubServiceIntegration:
    """Integration tests for GitHubService (require real API or more complex mocking)."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        with patch('src.services.github_service.config') as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                'github.token': 'test_token_123',
                'github.username': 'testuser',
                'github.base_url': 'https://api.github.com',
                'workflow.timeout_seconds': 30
            }.get(key, default)
            yield mock_config
    
    def test_full_workflow_mock(self, mock_config):
        """Test complete workflow with comprehensive mocking."""
        service = GitHubService()
        
        # Mock all API calls for a complete workflow
        with patch.object(service, '_make_request') as mock_request:
            # Repository creation
            mock_request.return_value = {
                'name': 'test-project',
                'full_name': 'testuser/test-project',
                'html_url': 'https://github.com/testuser/test-project'
            }
            
            # Create repository
            repo = service.create_repository('test-project', 'Test project for EV analysis')
            assert repo['name'] == 'test-project'
            
            # Mock file upload responses
            mock_request.side_effect = [
                GitHubAPIError("Not found", 404),  # File doesn't exist
                {'path': 'README.md', 'sha': 'readme_sha'},  # README upload
                GitHubAPIError("Not found", 404),  # Notebook doesn't exist
                {'path': 'notebook.ipynb', 'sha': 'notebook_sha'},  # Notebook upload
            ]
            
            # Initialize README
            readme_result = service.initialize_readme('test-project', '# Test Project\n\nEV analysis project')
            assert readme_result['path'] == 'README.md'
            
            # Upload notebook
            notebook_content = '{"cells": [], "metadata": {}, "nbformat": 4}'
            notebook_result = service.upload_file('test-project', 'notebook.ipynb', notebook_content)
            assert notebook_result['path'] == 'notebook.ipynb'
            
            # Verify repository URL
            repo_url = service.get_repository_url('test-project')
            assert repo_url == 'https://github.com/testuser/test-project'


class TestGitHubRepositoryOperations:
    """Test cases for new repository operations functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        with patch('src.services.github_service.config') as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                'github.token': 'test_token_123',
                'github.username': 'testuser',
                'github.base_url': 'https://api.github.com',
                'workflow.timeout_seconds': 30
            }.get(key, default)
            yield mock_config
    
    @pytest.fixture
    def github_service(self, mock_config):
        """Create GitHubService instance for testing."""
        return GitHubService()
    
    @pytest.fixture
    def temp_notebook_file(self):
        """Create a temporary notebook file."""
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# Test Notebook\n", "This is a test notebook for EV analysis project."]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["print('Hello, World!')"]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as temp_file:
            json.dump(notebook_content, temp_file, indent=2)
            temp_file_path = temp_file.name
        
        yield temp_file_path
        
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
    
    @pytest.fixture
    def temp_dataset_file(self):
        """Create a temporary CSV dataset file."""
        csv_content = "name,age,city\nJohn,25,New York\nJane,30,Los Angeles\nBob,35,Chicago"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name
        
        yield temp_file_path
        
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
    
    def test_upload_file_from_path_text_file(self, github_service, temp_dataset_file):
        """Test uploading a text file from local path."""
        with patch.object(github_service, '_make_request') as mock_request:
            # Mock file doesn't exist, then successful upload
            mock_request.side_effect = [
                GitHubAPIError("Not found", 404),
                {'path': 'dataset.csv', 'sha': 'abc123'}
            ]
            
            result = github_service.upload_file_from_path('test-repo', temp_dataset_file, 'dataset.csv')
            
            assert result == {'path': 'dataset.csv', 'sha': 'abc123'}
            assert mock_request.call_count == 2
            
            # Check upload call
            upload_call = mock_request.call_args_list[1]
            assert upload_call[0] == ('PUT', '/repos/testuser/test-repo/contents/dataset.csv')
    
    def test_upload_file_from_path_binary_file(self, github_service):
        """Test uploading a binary file from local path."""
        binary_content = b'\x89PNG\r\n\x1a\n'  # PNG header
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as temp_file:
            temp_file.write(binary_content)
            temp_file_path = temp_file.name
        
        try:
            with patch.object(github_service, '_make_request') as mock_request:
                mock_request.side_effect = [
                    GitHubAPIError("Not found", 404),
                    {'path': 'image.png', 'sha': 'def456'}
                ]
                
                result = github_service.upload_file_from_path('test-repo', temp_file_path, 'image.png')
                
                assert result == {'path': 'image.png', 'sha': 'def456'}
                
                # Verify binary content was base64 encoded
                upload_call = mock_request.call_args_list[1]
                upload_data = upload_call[1]['data']
                expected_encoded = base64.b64encode(binary_content).decode('utf-8')
                assert upload_data['content'] == expected_encoded
        finally:
            os.unlink(temp_file_path)
    
    def test_upload_file_from_path_nonexistent_file(self, github_service):
        """Test uploading nonexistent file raises error."""
        with pytest.raises(GitHubAPIError, match="Local file not found"):
            github_service.upload_file_from_path('test-repo', '/nonexistent/file.txt')
    
    def test_upload_notebook_and_dataset_success(self, github_service, temp_notebook_file, temp_dataset_file):
        """Test successful upload of notebook and dataset files."""
        with patch.object(github_service, '_upload_with_retry') as mock_upload:
            mock_upload.side_effect = [
                {'path': 'notebook.ipynb', 'sha': 'notebook_sha'},
                {'path': 'dataset.csv', 'sha': 'dataset_sha'}
            ]
            
            result = github_service.upload_notebook_and_dataset(
                'test-repo', temp_notebook_file, temp_dataset_file
            )
            
            assert result['notebook'] == {'path': 'notebook.ipynb', 'sha': 'notebook_sha'}
            assert result['dataset'] == {'path': 'dataset.csv', 'sha': 'dataset_sha'}
            assert result['errors'] == []
            assert mock_upload.call_count == 2
    
    def test_upload_notebook_and_dataset_notebook_only(self, github_service, temp_notebook_file):
        """Test upload with only notebook file (no dataset)."""
        with patch.object(github_service, '_upload_with_retry') as mock_upload:
            mock_upload.return_value = {'path': 'notebook.ipynb', 'sha': 'notebook_sha'}
            
            result = github_service.upload_notebook_and_dataset('test-repo', temp_notebook_file)
            
            assert result['notebook'] == {'path': 'notebook.ipynb', 'sha': 'notebook_sha'}
            assert result['dataset'] is None
            assert result['errors'] == []
            assert mock_upload.call_count == 1
    
    def test_upload_notebook_and_dataset_with_errors(self, github_service, temp_notebook_file, temp_dataset_file):
        """Test upload with partial failures."""
        with patch.object(github_service, '_upload_with_retry') as mock_upload:
            mock_upload.side_effect = [
                {'path': 'notebook.ipynb', 'sha': 'notebook_sha'},
                GitHubAPIError("Dataset upload failed", 500)
            ]
            
            result = github_service.upload_notebook_and_dataset(
                'test-repo', temp_notebook_file, temp_dataset_file
            )
            
            assert result['notebook'] == {'path': 'notebook.ipynb', 'sha': 'notebook_sha'}
            assert result['dataset'] is None
            assert len(result['errors']) == 1
            assert "Failed to upload dataset" in result['errors'][0]
    
    def test_upload_notebook_and_dataset_auth_error(self, github_service, temp_notebook_file):
        """Test upload with authentication error."""
        with patch.object(github_service, '_upload_with_retry') as mock_upload:
            mock_upload.side_effect = GitHubAPIError("Authentication failed", 401)
            
            with pytest.raises(GitHubAPIError, match="Authentication error while uploading notebook"):
                github_service.upload_notebook_and_dataset('test-repo', temp_notebook_file)
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_upload_with_retry_rate_limit_recovery(self, mock_sleep, github_service, temp_dataset_file):
        """Test retry logic for rate limit errors."""
        with patch.object(github_service, 'upload_file_from_path') as mock_upload:
            mock_upload.side_effect = [
                GitHubAPIError("Rate limit exceeded", 403),
                {'path': 'dataset.csv', 'sha': 'success_sha'}
            ]
            
            result = github_service._upload_with_retry('test-repo', temp_dataset_file)
            
            assert result == {'path': 'dataset.csv', 'sha': 'success_sha'}
            assert mock_upload.call_count == 2
            assert mock_sleep.called  # Verify backoff was applied
    
    @patch('time.sleep')
    def test_upload_with_retry_server_error_recovery(self, mock_sleep, github_service, temp_dataset_file):
        """Test retry logic for server errors."""
        with patch.object(github_service, 'upload_file_from_path') as mock_upload:
            mock_upload.side_effect = [
                GitHubAPIError("Internal server error", 500),
                GitHubAPIError("Bad gateway", 502),
                {'path': 'dataset.csv', 'sha': 'success_sha'}
            ]
            
            result = github_service._upload_with_retry('test-repo', temp_dataset_file)
            
            assert result == {'path': 'dataset.csv', 'sha': 'success_sha'}
            assert mock_upload.call_count == 3
            assert mock_sleep.call_count == 2
    
    @patch('time.sleep')
    def test_upload_with_retry_max_retries_exceeded(self, mock_sleep, github_service, temp_dataset_file):
        """Test retry logic when max retries are exceeded."""
        with patch.object(github_service, 'upload_file_from_path') as mock_upload:
            mock_upload.side_effect = GitHubAPIError("Persistent error", 500)
            
            with pytest.raises(GitHubAPIError, match="Failed to upload .* after 3 attempts"):
                github_service._upload_with_retry('test-repo', temp_dataset_file, max_retries=3)
            
            assert mock_upload.call_count == 3
    
    def test_upload_with_retry_non_retryable_error(self, github_service, temp_dataset_file):
        """Test that non-retryable errors are not retried."""
        with patch.object(github_service, 'upload_file_from_path') as mock_upload:
            mock_upload.side_effect = GitHubAPIError("File not found", 404)
            
            with pytest.raises(GitHubAPIError, match="File not found"):
                github_service._upload_with_retry('test-repo', temp_dataset_file)
            
            assert mock_upload.call_count == 1  # No retries for 404
    
    def test_generate_submission_url_with_files(self, github_service):
        """Test submission URL generation with file links."""
        result = github_service.generate_submission_url('test-project', include_files=True)
        
        expected = {
            'repository_url': 'https://github.com/testuser/test-project',
            'submission_link': 'https://github.com/testuser/test-project',
            'notebook_url': 'https://github.com/testuser/test-project/blob/main/notebook.ipynb',
            'dataset_url': 'https://github.com/testuser/test-project/blob/main/dataset.csv',
            'readme_url': 'https://github.com/testuser/test-project/blob/main/README.md'
        }
        
        assert result == expected
    
    def test_generate_submission_url_without_files(self, github_service):
        """Test submission URL generation without file links."""
        result = github_service.generate_submission_url('test-project', include_files=False)
        
        expected = {
            'repository_url': 'https://github.com/testuser/test-project',
            'submission_link': 'https://github.com/testuser/test-project'
        }
        
        assert result == expected
    
    def test_validate_repository_for_submission_valid(self, github_service):
        """Test repository validation with all required files present."""
        with patch.object(github_service, '_make_request') as mock_request:
            mock_request.side_effect = [
                {'path': 'README.md', 'size': 1024, 'sha': 'readme_sha'},
                {'path': 'notebook.ipynb', 'size': 2048, 'sha': 'notebook_sha'},
                {'path': 'dataset.csv', 'size': 512, 'sha': 'dataset_sha'},
                GitHubAPIError("Not found", 404)  # requirements.txt not found
            ]
            
            result = github_service.validate_repository_for_submission('test-repo')
            
            assert result['is_valid'] is True
            assert result['missing_files'] == []
            assert len(result['files_found']) == 3
            assert result['errors'] == []
    
    def test_validate_repository_for_submission_missing_required(self, github_service):
        """Test repository validation with missing required files."""
        with patch.object(github_service, '_make_request') as mock_request:
            mock_request.side_effect = [
                GitHubAPIError("Not found", 404),  # README.md missing
                {'path': 'notebook.ipynb', 'size': 2048, 'sha': 'notebook_sha'},
                GitHubAPIError("Not found", 404),  # dataset.csv missing
                GitHubAPIError("Not found", 404)   # requirements.txt missing
            ]
            
            result = github_service.validate_repository_for_submission('test-repo')
            
            assert result['is_valid'] is False
            assert 'README.md' in result['missing_files']
            assert len(result['files_found']) == 1
    
    def test_validate_repository_for_submission_api_errors(self, github_service):
        """Test repository validation with API errors."""
        with patch.object(github_service, '_make_request') as mock_request:
            mock_request.side_effect = [
                {'path': 'README.md', 'size': 1024, 'sha': 'readme_sha'},
                GitHubAPIError("Server error", 500),  # API error for notebook
                GitHubAPIError("Not found", 404),     # dataset missing
                GitHubAPIError("Not found", 404)      # requirements missing
            ]
            
            result = github_service.validate_repository_for_submission('test-repo')
            
            assert result['is_valid'] is True  # README found, so still valid
            assert len(result['errors']) == 1
            assert "Error checking notebook.ipynb" in result['errors'][0]


class TestGitHubRepositoryOperationsIntegration:
    """Integration tests for GitHub repository operations workflow."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        with patch('src.services.github_service.config') as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                'github.token': 'test_token_123',
                'github.username': 'testuser',
                'github.base_url': 'https://api.github.com',
                'workflow.timeout_seconds': 30
            }.get(key, default)
            yield mock_config
    
    @pytest.fixture
    def github_service(self, mock_config):
        """Create GitHubService instance for testing."""
        return GitHubService()
    
    @pytest.fixture
    def temp_project_files(self):
        """Create temporary project files for testing."""
        # Create notebook file
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# EV Analysis Project\n", "This is my charge demand analysis project."]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["import pandas as pd\n", "df = pd.read_csv('dataset.csv')\n", "print(df.head())"]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as notebook_file:
            json.dump(notebook_content, notebook_file, indent=2)
            notebook_path = notebook_file.name
        
        # Create dataset file
        dataset_content = "name,age,score\nAlice,25,85\nBob,30,92\nCharlie,22,78\nDiana,28,96"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as dataset_file:
            dataset_file.write(dataset_content)
            dataset_path = dataset_file.name
        
        yield {
            'notebook_path': notebook_path,
            'dataset_path': dataset_path,
            'notebook_content': notebook_content,
            'dataset_content': dataset_content
        }
        
        # Cleanup
        for path in [notebook_path, dataset_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_complete_repository_setup_workflow(self, github_service, temp_project_files):
        """Test complete workflow: create repo, upload files, generate submission URL."""
        with patch.object(github_service, '_make_request') as mock_request:
            # Mock repository creation
            repo_data = {
                'name': 'ev-analysis-project',
                'full_name': 'testuser/ev-analysis-project',
                'html_url': 'https://github.com/testuser/ev-analysis-project'
            }
            
            # Mock file upload sequence
            mock_request.side_effect = [
                repo_data,  # Repository creation
                GitHubAPIError("Not found", 404),  # README doesn't exist
                {'path': 'README.md', 'sha': 'readme_sha'},  # README upload
                GitHubAPIError("Not found", 404),  # Notebook doesn't exist
                {'path': 'notebook.ipynb', 'sha': 'notebook_sha'},  # Notebook upload
                GitHubAPIError("Not found", 404),  # Dataset doesn't exist
                {'path': 'dataset.csv', 'sha': 'dataset_sha'},  # Dataset upload
            ]
            
            # Step 1: Create repository
            repo = github_service.create_repository(
                'ev-analysis-project', 
                'EV Charge Demand Analysis Project'
            )
            assert repo['name'] == 'ev-analysis-project'
            
            # Step 2: Initialize README
            readme_content = "# EV Analysis Project\n\nThis repository contains my charge demand analysis project."
            readme_result = github_service.initialize_readme('ev-analysis-project', readme_content)
            assert readme_result['path'] == 'README.md'
            
            # Step 3: Upload project files
            upload_result = github_service.upload_notebook_and_dataset(
                'ev-analysis-project',
                temp_project_files['notebook_path'],
                temp_project_files['dataset_path']
            )
            
            assert upload_result['notebook']['path'] == 'notebook.ipynb'
            assert upload_result['dataset']['path'] == 'dataset.csv'
            assert len(upload_result['errors']) == 0
            
            # Step 4: Generate submission URL
            submission_info = github_service.generate_submission_url('ev-analysis-project')
            assert submission_info['repository_url'] == 'https://github.com/testuser/ev-analysis-project'
            assert submission_info['notebook_url'] == 'https://github.com/testuser/ev-analysis-project/blob/main/notebook.ipynb'
            assert submission_info['dataset_url'] == 'https://github.com/testuser/ev-analysis-project/blob/main/dataset.csv'
    
    def test_repository_operations_with_rate_limiting(self, github_service, temp_project_files):
        """Test repository operations with rate limiting and recovery."""
        with patch.object(github_service, '_make_request') as mock_request, \
             patch('time.sleep') as mock_sleep:
            
            # Simulate rate limiting on first upload, then success
            mock_request.side_effect = [
                GitHubAPIError("Not found", 404),  # File doesn't exist check
                GitHubAPIError("Rate limit exceeded", 403),  # Rate limited
                {'path': 'notebook.ipynb', 'sha': 'notebook_sha'},  # Success after retry
            ]
            
            # Mock upload_file_from_path to use our mocked _make_request
            with patch.object(github_service, 'upload_file_from_path') as mock_upload:
                mock_upload.side_effect = [
                    GitHubAPIError("Rate limit exceeded", 403),
                    {'path': 'notebook.ipynb', 'sha': 'notebook_sha'}
                ]
                
                result = github_service._upload_with_retry(
                    'test-repo', 
                    temp_project_files['notebook_path'],
                    max_retries=3
                )
                
                assert result['path'] == 'notebook.ipynb'
                assert mock_upload.call_count == 2
                assert mock_sleep.called  # Verify backoff was applied
    
    def test_repository_operations_with_partial_failures(self, github_service, temp_project_files):
        """Test repository operations with partial upload failures."""
        with patch.object(github_service, '_upload_with_retry') as mock_upload:
            # Notebook upload succeeds, dataset upload fails
            mock_upload.side_effect = [
                {'path': 'notebook.ipynb', 'sha': 'notebook_sha'},
                GitHubAPIError("File too large", 413)
            ]
            
            result = github_service.upload_notebook_and_dataset(
                'test-repo',
                temp_project_files['notebook_path'],
                temp_project_files['dataset_path']
            )
            
            # Should have notebook success and dataset error
            assert result['notebook']['path'] == 'notebook.ipynb'
            assert result['dataset'] is None
            assert len(result['errors']) == 1
            assert "Failed to upload dataset" in result['errors'][0]
    
    def test_repository_validation_integration(self, github_service):
        """Test repository validation for submission readiness."""
        with patch.object(github_service, '_make_request') as mock_request:
            # Mock repository with all required files
            mock_request.side_effect = [
                {'path': 'README.md', 'size': 1024, 'sha': 'readme_sha'},
                {'path': 'notebook.ipynb', 'size': 2048, 'sha': 'notebook_sha'},
                {'path': 'dataset.csv', 'size': 512, 'sha': 'dataset_sha'},
                GitHubAPIError("Not found", 404)  # requirements.txt optional
            ]
            
            validation = github_service.validate_repository_for_submission('test-repo')
            
            assert validation['is_valid'] is True
            assert len(validation['files_found']) == 3
            assert validation['missing_files'] == []
            
            # Verify all expected files are found
            found_files = [f['path'] for f in validation['files_found']]
            assert 'README.md' in found_files
            assert 'notebook.ipynb' in found_files
            assert 'dataset.csv' in found_files
    
    def test_submission_url_generation_integration(self, github_service):
        """Test submission URL generation for LMS integration."""
        # Test basic URL generation
        basic_urls = github_service.generate_submission_url('my-project', include_files=False)
        assert basic_urls['repository_url'] == 'https://github.com/testuser/my-project'
        assert basic_urls['submission_link'] == 'https://github.com/testuser/my-project'
        assert 'notebook_url' not in basic_urls
        
        # Test with file URLs
        detailed_urls = github_service.generate_submission_url('my-project', include_files=True)
        assert detailed_urls['repository_url'] == 'https://github.com/testuser/my-project'
        assert detailed_urls['notebook_url'] == 'https://github.com/testuser/my-project/blob/main/notebook.ipynb'
        assert detailed_urls['dataset_url'] == 'https://github.com/testuser/my-project/blob/main/dataset.csv'
        assert detailed_urls['readme_url'] == 'https://github.com/testuser/my-project/blob/main/README.md'
    
    def test_error_handling_integration_workflow(self, github_service, temp_project_files):
        """Test comprehensive error handling in repository operations."""
        # Test authentication error handling
        with patch.object(github_service, '_upload_with_retry') as mock_upload:
            mock_upload.side_effect = GitHubAPIError("Bad credentials", 401)
            
            with pytest.raises(GitHubAPIError, match="Authentication error while uploading notebook"):
                github_service.upload_notebook_and_dataset(
                    'test-repo',
                    temp_project_files['notebook_path']
                )
        
        # Test network error handling
        with patch.object(github_service, '_make_request') as mock_request:
            mock_request.side_effect = GitHubAPIError("Connection error")
            
            with pytest.raises(GitHubAPIError, match="Connection error"):
                github_service.create_repository('test-repo')
    
    def test_large_file_handling_integration(self, github_service):
        """Test handling of large files and binary content."""
        # Create a larger test file
        large_content = "data,value\n" + "\n".join([f"row{i},{i*10}" for i in range(1000)])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as large_file:
            large_file.write(large_content)
            large_file_path = large_file.name
        
        try:
            with patch.object(github_service, '_make_request') as mock_request:
                mock_request.side_effect = [
                    GitHubAPIError("Not found", 404),  # File doesn't exist
                    {'path': 'large_dataset.csv', 'sha': 'large_sha'}  # Upload success
                ]
                
                result = github_service.upload_file_from_path(
                    'test-repo', 
                    large_file_path, 
                    'large_dataset.csv'
                )
                
                assert result['path'] == 'large_dataset.csv'
                
                # Verify content was base64 encoded properly
                upload_call = mock_request.call_args_list[1]
                upload_data = upload_call[1]['data']
                decoded_content = base64.b64decode(upload_data['content']).decode('utf-8')
                assert decoded_content == large_content
        finally:
            os.unlink(large_file_path)
    
    def test_concurrent_operations_simulation(self, github_service, temp_project_files):
        """Test simulation of concurrent repository operations."""
        with patch.object(github_service, '_upload_with_retry') as mock_upload:
            # Simulate multiple files being uploaded
            mock_upload.side_effect = [
                {'path': 'notebook.ipynb', 'sha': 'notebook_sha'},
                {'path': 'dataset.csv', 'sha': 'dataset_sha'}
            ]
            
            # Upload notebook and dataset
            result = github_service.upload_notebook_and_dataset(
                'test-repo',
                temp_project_files['notebook_path'],
                temp_project_files['dataset_path']
            )
            
            # Verify both uploads completed
            assert result['notebook']['path'] == 'notebook.ipynb'
            assert result['dataset']['path'] == 'dataset.csv'
            assert len(result['errors']) == 0
            assert mock_upload.call_count == 2
    
    def test_end_to_end_ev_analysis_workflow_simulation(self, github_service, temp_project_files):
        """Test complete end-to-end EV analysis project workflow."""
        with patch.object(github_service, '_make_request') as mock_request:
            # Complete workflow simulation
            mock_responses = [
                # Repository creation
                {
                    'name': 'ev-charge-analysis',
                    'full_name': 'testuser/ev-charge-analysis',
                    'html_url': 'https://github.com/testuser/ev-charge-analysis'
                },
                # README upload (check + upload)
                GitHubAPIError("Not found", 404),
                {'path': 'README.md', 'sha': 'readme_sha'},
                # Notebook upload (check + upload)
                GitHubAPIError("Not found", 404),
                {'path': 'ev_analysis.ipynb', 'sha': 'notebook_sha'},
                # Dataset upload (check + upload)
                GitHubAPIError("Not found", 404),
                {'path': 'ev_data.csv', 'sha': 'dataset_sha'},
                # Validation checks
                {'path': 'README.md', 'size': 1024, 'sha': 'readme_sha'},
                {'path': 'ev_analysis.ipynb', 'size': 2048, 'sha': 'notebook_sha'},
                {'path': 'ev_data.csv', 'size': 512, 'sha': 'dataset_sha'},
                GitHubAPIError("Not found", 404)  # requirements.txt not found
            ]
            mock_request.side_effect = mock_responses
            
            # Step 1: Create repository
            repo = github_service.create_repository(
                'ev-charge-analysis',
                'EV Charge Demand Analysis Project'
            )
            assert repo['name'] == 'ev-charge-analysis'
            
            # Step 2: Initialize README
            readme_content = """# EV Charge Demand Analysis Project
            
## Machine Learning Analysis

This project analyzes electric vehicle market trends using Python and data visualization.

### Files
- `ev_analysis.ipynb`: Main analysis notebook
- `ev_data.csv`: Dataset with EV market data
- `README.md`: This file

### How to Run
1. Open the notebook in Google Colab
2. Upload the dataset
3. Run all cells to see the analysis
"""
            github_service.initialize_readme('ev-charge-analysis', readme_content)
            
            # Step 3: Upload project files
            upload_result = github_service.upload_notebook_and_dataset(
                'ev-charge-analysis',
                temp_project_files['notebook_path'],
                temp_project_files['dataset_path']
            )
            assert len(upload_result['errors']) == 0
            
            # Step 4: Validate repository for submission
            validation = github_service.validate_repository_for_submission('ev-charge-analysis')
            assert validation['is_valid'] is True
            assert len(validation['files_found']) == 3
            
            # Step 5: Generate submission URLs
            submission_info = github_service.generate_submission_url('ev-charge-analysis')
            assert 'repository_url' in submission_info
            assert 'notebook_url' in submission_info
            assert 'dataset_url' in submission_info
            
            # Verify the complete workflow executed successfully
            expected_calls = len(mock_responses)
            assert mock_request.call_count == expected_calls