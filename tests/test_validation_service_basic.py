"""
Basic unit tests for ValidationService without external dependencies.
"""
import unittest
from unittest.mock import Mock, patch
import os
from datetime import datetime, timedelta

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.validation_service import ValidationService
from models.workflow_models import ProjectData, WorkflowState


class TestValidationServiceBasic(unittest.TestCase):
    """Basic test cases for ValidationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validation_service = ValidationService()
        
        # Create test project data
        self.test_project_data = ProjectData(
            project_id="test-project-1",
            dataset_url="https://example.com/dataset.csv",
            code_template_url="https://example.com/template.ipynb",
            project_description="A test project for machine learning analysis",
            requirements=["Load and analyze data", "Train ML model", "Generate predictions"],
            deadline=datetime.now() + timedelta(days=7)
        )
        
        # Create test workflow state
        self.test_workflow_state = WorkflowState(
            project_name="Test Project",
            current_step=1,
            completed_steps=[],
            project_data=self.test_project_data
        )
    
    def test_init_with_config(self):
        """Test ValidationService initialization with config."""
        config = {"github_token": "test_token"}
        service = ValidationService(config)
        self.assertEqual(service.config, config)
    
    def test_init_without_config(self):
        """Test ValidationService initialization without config."""
        service = ValidationService()
        self.assertEqual(service.config, {})
    
    def test_required_files_list(self):
        """Test that required files list is properly set."""
        expected_files = ['README.md', 'requirements.txt', 'dataset.csv']
        self.assertEqual(self.validation_service.required_files, expected_files)
    
    def test_required_notebook_sections_list(self):
        """Test that required notebook sections list is properly set."""
        expected_sections = ['data_loading', 'data_preprocessing', 'model_training', 'evaluation']
        self.assertEqual(self.validation_service.required_notebook_sections, expected_sections)
    
    @patch('sys.version_info', (3, 8, 0))
    def test_check_python_environment_success(self):
        """Test Python environment check with valid version."""
        result = self.validation_service._check_python_environment()
        self.assertTrue(result)
    
    @patch('sys.version_info', (3, 6, 0))
    def test_check_python_environment_failure(self):
        """Test Python environment check with invalid version."""
        with patch('builtins.print') as mock_print:
            result = self.validation_service._check_python_environment()
            self.assertFalse(result)
            mock_print.assert_called_with("Python 3.7 or higher is required")
    
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'})
    def test_check_github_config_success(self):
        """Test GitHub config check with token in environment."""
        result = self.validation_service._check_github_config()
        self.assertTrue(result)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_check_github_config_failure(self):
        """Test GitHub config check without token."""
        with patch('builtins.print') as mock_print:
            result = self.validation_service._check_github_config()
            self.assertFalse(result)
            mock_print.assert_called()
    
    def test_validate_project_data_success(self):
        """Test project data validation with valid data."""
        with patch.object(self.validation_service, '_check_url_accessibility', return_value=True):
            is_valid, errors = self.validation_service.validate_project_data(self.test_project_data)
            self.assertTrue(is_valid)
            self.assertEqual(len(errors), 0)
    
    def test_validate_project_data_invalid_urls(self):
        """Test project data validation with invalid URLs."""
        with patch.object(self.validation_service, '_check_url_accessibility', return_value=False):
            is_valid, errors = self.validation_service.validate_project_data(self.test_project_data)
            self.assertFalse(is_valid)
            self.assertEqual(len(errors), 2)  # Both URLs should fail
    
    def test_validate_project_data_deadline_too_soon(self):
        """Test project data validation with deadline too soon."""
        # Create project data with deadline in the past by bypassing validation
        with patch.object(ProjectData, 'validate', return_value=True):
            past_project_data = ProjectData(
                project_id="test-project-1",
                dataset_url="https://example.com/dataset.csv",
                code_template_url="https://example.com/template.ipynb",
                project_description="A test project for machine learning analysis",
                requirements=["Load and analyze data", "Train ML model", "Generate predictions"],
                deadline=datetime.now() - timedelta(hours=1)
            )
        
        with patch.object(self.validation_service, '_check_url_accessibility', return_value=True):
            is_valid, errors = self.validation_service.validate_project_data(past_project_data)
            self.assertFalse(is_valid)
            self.assertTrue(any("deadline is too soon" in error for error in errors))
    
    def test_validate_project_data_insufficient_requirements(self):
        """Test project data validation with insufficient requirements."""
        # Create project data with too few requirements
        insufficient_project_data = ProjectData(
            project_id="test-project-1",
            dataset_url="https://example.com/dataset.csv",
            code_template_url="https://example.com/template.ipynb",
            project_description="A test project for machine learning analysis",
            requirements=["Load data", "Train model"],  # Only 2 requirements
            deadline=datetime.now() + timedelta(days=7)
        )
        
        with patch.object(self.validation_service, '_check_url_accessibility', return_value=True):
            is_valid, errors = self.validation_service.validate_project_data(insufficient_project_data)
            self.assertFalse(is_valid)
            self.assertTrue(any("at least 3 specific requirements" in error for error in errors))
    
    def test_validate_workflow_state_success(self):
        """Test workflow state validation with valid state."""
        with patch.object(self.validation_service, 'validate_project_data', return_value=(True, [])):
            is_valid, errors = self.validation_service.validate_workflow_state(self.test_workflow_state)
            self.assertTrue(is_valid)
            self.assertEqual(len(errors), 0)
    
    def test_validate_workflow_state_invalid_step_progression(self):
        """Test workflow state validation with invalid step progression."""
        # Create workflow state with current step less than completed steps
        invalid_workflow_state = WorkflowState(
            project_name="Test Project",
            current_step=1,
            completed_steps=[2, 3],  # Current step should not be less than max completed
            project_data=self.test_project_data
        )
        
        with patch.object(self.validation_service, 'validate_project_data', return_value=(True, [])):
            is_valid, errors = self.validation_service.validate_workflow_state(invalid_workflow_state)
            self.assertFalse(is_valid)
            self.assertTrue(any("Current step should not be less" in error for error in errors))
    
    def test_validate_workflow_state_invalid_github_repo_format(self):
        """Test workflow state validation with invalid GitHub repo format."""
        # Create workflow state with invalid GitHub repo format by bypassing validation
        with patch.object(WorkflowState, 'validate', return_value=True):
            invalid_workflow_state = WorkflowState(
                project_name="Test Project",
                current_step=1,
                completed_steps=[],
                project_data=self.test_project_data,
                github_repo="invalid-repo-format"  # Should be owner/repo
            )
        
        with patch.object(self.validation_service, 'validate_project_data', return_value=(True, [])):
            is_valid, errors = self.validation_service.validate_workflow_state(invalid_workflow_state)
            self.assertFalse(is_valid)
            self.assertTrue(any("GitHub repository format" in error for error in errors))
    
    def test_validate_notebook_content_file_not_found(self):
        """Test notebook validation when file doesn't exist."""
        with patch('builtins.print') as mock_print:
            result = self.validation_service.validate_notebook_content("nonexistent.ipynb")
            self.assertFalse(result)
            mock_print.assert_called()
    
    def test_verify_repository_structure_path_not_exists(self):
        """Test repository structure verification when path doesn't exist."""
        with patch('builtins.print') as mock_print:
            result = self.validation_service.verify_repository_structure("nonexistent_path")
            self.assertFalse(result)
            mock_print.assert_called()
    
    def test_check_url_accessibility_no_requests(self):
        """Test URL accessibility check when requests module is not available."""
        with patch('services.validation_service.HAS_REQUESTS', False):
            result = self.validation_service._check_url_accessibility("https://example.com")
            self.assertFalse(result)
    
    def test_confirm_submission_readiness_with_mocked_checks(self):
        """Test submission readiness confirmation with mocked validation checks."""
        with patch.object(self.validation_service, 'check_prerequisites', return_value=True), \
             patch.object(self.validation_service, 'verify_repository_structure', return_value=True), \
             patch('builtins.print') as mock_print:
            
            result = self.validation_service.confirm_submission_readiness()
            self.assertTrue(result)
            mock_print.assert_called_with("All validation checks passed. Submission is ready!")
    
    def test_confirm_submission_readiness_with_failed_checks(self):
        """Test submission readiness confirmation with failed validation checks."""
        with patch.object(self.validation_service, 'check_prerequisites', return_value=False), \
             patch.object(self.validation_service, 'verify_repository_structure', return_value=False), \
             patch('builtins.print') as mock_print:
            
            result = self.validation_service.confirm_submission_readiness()
            self.assertFalse(result)
            mock_print.assert_called()


if __name__ == '__main__':
    unittest.main()