"""
Unit tests for ValidationService.
"""
import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
import json

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.validation_service import ValidationService
from models.workflow_models import ProjectData, WorkflowState
from models.interfaces import StepStatus


class TestValidationService(unittest.TestCase):
    """Test cases for ValidationService."""
    
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
    
    @patch('services.validation_service.sys.version_info', (3, 8, 0))
    def test_check_python_environment_success(self):
        """Test Python environment check with valid version."""
        result = self.validation_service._check_python_environment()
        self.assertTrue(result)
    
    @patch('services.validation_service.sys.version_info', (3, 6, 0))
    def test_check_python_environment_failure(self):
        """Test Python environment check with invalid version."""
        with patch('builtins.print') as mock_print:
            result = self.validation_service._check_python_environment()
            self.assertFalse(result)
            mock_print.assert_called_with("Python 3.7 or higher is required")
    
    @patch('builtins.__import__')
    def test_check_required_packages_success(self, mock_import):
        """Test required packages check when all packages are available."""
        mock_import.return_value = Mock()
        result = self.validation_service._check_required_packages()
        self.assertTrue(result)
    
    @patch('builtins.__import__')
    def test_check_required_packages_failure(self, mock_import):
        """Test required packages check when packages are missing."""
        mock_import.side_effect = ImportError("No module named 'requests'")
        with patch('builtins.print') as mock_print:
            result = self.validation_service._check_required_packages()
            self.assertFalse(result)
            mock_print.assert_called()
    
    @patch('requests.get')
    def test_check_internet_connectivity_success(self, mock_get):
        """Test internet connectivity check with successful connection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.validation_service._check_internet_connectivity()
        self.assertTrue(result)
    
    @patch('requests.get')
    def test_check_internet_connectivity_failure(self, mock_get):
        """Test internet connectivity check with failed connection."""
        mock_get.side_effect = Exception("Connection error")
        with patch('builtins.print') as mock_print:
            result = self.validation_service._check_internet_connectivity()
            self.assertFalse(result)
            mock_print.assert_called_with("No internet connectivity detected")
    
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
        # Create project data with deadline in the past
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
    
    def test_validate_notebook_content_file_not_found(self):
        """Test notebook validation when file doesn't exist."""
        with patch('builtins.print') as mock_print:
            result = self.validation_service.validate_notebook_content("nonexistent.ipynb")
            self.assertFalse(result)
            mock_print.assert_called()
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('nbformat.read')
    def test_validate_notebook_content_success(self, mock_nbformat_read, mock_file, mock_exists):
        """Test successful notebook validation."""
        mock_exists.return_value = True
        
        # Create mock notebook with proper structure
        mock_notebook = Mock()
        mock_notebook.cells = [
            Mock(cell_type='markdown', source='# Data Loading\nThis section loads data'),
            Mock(cell_type='code', source='import pandas as pd', outputs=['output'], execution_count=1),
            Mock(cell_type='markdown', source='# Data Preprocessing\nClean the data'),
            Mock(cell_type='code', source='df.dropna()', outputs=['output'], execution_count=2),
            Mock(cell_type='markdown', source='# Model Training\nTrain the model'),
            Mock(cell_type='code', source='model.fit(X, y)', outputs=['output'], execution_count=3),
            Mock(cell_type='markdown', source='# Evaluation\nEvaluate results'),
            Mock(cell_type='code', source='print(accuracy)', outputs=['output'], execution_count=4)
        ]
        mock_nbformat_read.return_value = mock_notebook
        
        result = self.validation_service.validate_notebook_content("test.ipynb")
        self.assertTrue(result)
    
    def test_verify_repository_structure_path_not_exists(self):
        """Test repository structure verification when path doesn't exist."""
        with patch('builtins.print') as mock_print:
            result = self.validation_service.verify_repository_structure("nonexistent_path")
            self.assertFalse(result)
            mock_print.assert_called()
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_verify_repository_structure_missing_files(self, mock_glob, mock_exists):
        """Test repository structure verification with missing files."""
        # Mock path exists but required files don't
        mock_exists.return_value = True
        mock_glob.return_value = []  # No notebook files
        
        with patch('builtins.print') as mock_print:
            result = self.validation_service.verify_repository_structure("test_repo")
            self.assertFalse(result)
            mock_print.assert_called()
    
    @patch('requests.head')
    def test_check_url_accessibility_success(self, mock_head):
        """Test URL accessibility check with successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        result = self.validation_service._check_url_accessibility("https://example.com")
        self.assertTrue(result)
    
    @patch('requests.head')
    def test_check_url_accessibility_failure(self, mock_head):
        """Test URL accessibility check with failed response."""
        mock_head.side_effect = Exception("Connection error")
        
        result = self.validation_service._check_url_accessibility("https://example.com")
        self.assertFalse(result)
    
    def test_validate_readme_content_file_too_short(self):
        """Test README validation with content too short."""
        with patch('builtins.open', mock_open(read_data="Short content")):
            with patch('builtins.print') as mock_print:
                result = self.validation_service._validate_readme_content(Path("README.md"))
                self.assertFalse(result)
                mock_print.assert_called()
    
    def test_validate_readme_content_missing_sections(self):
        """Test README validation with missing required sections."""
        readme_content = "This is a long enough README file content but it doesn't have the required sections like installation or usage instructions."
        
        with patch('builtins.open', mock_open(read_data=readme_content)):
            with patch('builtins.print') as mock_print:
                result = self.validation_service._validate_readme_content(Path("README.md"))
                self.assertFalse(result)
                mock_print.assert_called()
    
    def test_validate_readme_content_success(self):
        """Test successful README validation."""
        readme_content = """
        # Project Description
        This is a comprehensive project description that explains what the project does.
        
        ## Installation
        Instructions on how to install the project dependencies.
        
        ## Usage
        Instructions on how to use the project and run the code.
        """
        
        with patch('builtins.open', mock_open(read_data=readme_content)):
            result = self.validation_service._validate_readme_content(Path("README.md"))
            self.assertTrue(result)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_validate_dataset_file_empty(self, mock_stat, mock_exists):
        """Test dataset validation with empty file."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 0
        
        with patch('builtins.print') as mock_print:
            result = self.validation_service._validate_dataset_file(Path("dataset.csv"))
            self.assertFalse(result)
            mock_print.assert_called_with("Dataset file is empty")
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    @patch('pandas.read_csv')
    def test_validate_dataset_file_success(self, mock_read_csv, mock_stat, mock_exists):
        """Test successful dataset validation."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 1024  # 1KB file
        
        # Mock pandas DataFrame
        mock_df = Mock()
        mock_df.empty = False
        mock_df.columns = ['col1', 'col2', 'col3']
        mock_read_csv.return_value = mock_df
        
        result = self.validation_service._validate_dataset_file(Path("dataset.csv"))
        self.assertTrue(result)


if __name__ == '__main__':
    # Create tests directory if it doesn't exist
    os.makedirs('tests', exist_ok=True)
    unittest.main()