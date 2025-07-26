"""
Unit tests for submission validation service.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os
import json

from src.services.submission_service import (
    SubmissionValidationService, 
    SubmissionChecklist, 
    SubmissionStatus
)
from src.services.validation_service import ValidationService
from src.models.workflow_models import WorkflowState, ProjectData


class TestSubmissionChecklist(unittest.TestCase):
    """Test SubmissionChecklist data class."""
    
    def test_checklist_creation(self):
        """Test creating a checklist item."""
        checklist = SubmissionChecklist(
            item_id="test_item",
            description="Test description",
            is_required=True
        )
        
        self.assertEqual(checklist.item_id, "test_item")
        self.assertEqual(checklist.description, "Test description")
        self.assertTrue(checklist.is_required)
        self.assertFalse(checklist.is_completed)
        self.assertIsNone(checklist.validation_message)
        self.assertIsNone(checklist.last_checked)


class TestSubmissionStatus(unittest.TestCase):
    """Test SubmissionStatus data class."""
    
    def test_submission_status_creation(self):
        """Test creating submission status."""
        status = SubmissionStatus(project_name="test_project")
        
        self.assertEqual(status.project_name, "test_project")
        self.assertEqual(len(status.checklist_items), 0)
        self.assertEqual(status.overall_completion, 0.0)
        self.assertFalse(status.is_ready_for_submission)
        self.assertIsNone(status.deadline)
        self.assertIsNone(status.days_until_deadline)
        self.assertEqual(len(status.submission_warnings), 0)
        self.assertEqual(len(status.submission_errors), 0)
        self.assertIsNone(status.last_validated)


class TestSubmissionValidationService(unittest.TestCase):
    """Test SubmissionValidationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_validation_service = Mock(spec=ValidationService)
        self.service = SubmissionValidationService(self.mock_validation_service)
        
        # Create test workflow state
        self.test_project_data = ProjectData(
            project_id="test_project",
            dataset_url="https://example.com/dataset.csv",
            code_template_url="https://example.com/template.ipynb",
            project_description="Test project description for testing purposes",
            requirements=["Requirement 1", "Requirement 2", "Requirement 3"],
            deadline=datetime.now() + timedelta(days=7)
        )
        
        self.test_workflow_state = WorkflowState(
            project_name="Test Project",
            current_step=1,
            completed_steps=[],
            project_data=self.test_project_data,
            github_repo="testuser/test-project",
            submission_link="https://github.com/testuser/test-project"
        )
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsInstance(self.service.validation_service, Mock)
        self.assertEqual(len(self.service.standard_checklist), 11)  # 11 standard items
        self.assertEqual(self.service.reminder_thresholds, [7, 3, 1])
    
    def test_create_submission_checklist(self):
        """Test creating submission checklist."""
        submission_status = self.service.create_submission_checklist(self.test_workflow_state)
        
        self.assertEqual(submission_status.project_name, "Test Project")
        self.assertEqual(len(submission_status.checklist_items), 11)
        self.assertEqual(submission_status.deadline, self.test_project_data.deadline)
        
        # Check that all standard items are present
        item_ids = [item.item_id for item in submission_status.checklist_items]
        expected_ids = [
            'project_selection', 'notebook_created', 'dataset_uploaded',
            'code_implemented', 'notebook_executed', 'github_repo_created',
            'files_uploaded', 'readme_completed', 'repository_public',
            'submission_link_ready', 'attendance_marked'
        ]
        for expected_id in expected_ids:
            self.assertIn(expected_id, item_ids)
    
    def test_create_submission_checklist_with_completed_steps(self):
        """Test creating checklist with some completed steps."""
        self.test_workflow_state.completed_steps = [1, 2, 3]
        submission_status = self.service.create_submission_checklist(self.test_workflow_state)
        
        # Check that corresponding items are marked as completed
        completed_items = [item for item in submission_status.checklist_items if item.is_completed]
        self.assertEqual(len(completed_items), 3)
    
    def test_validate_submission_completeness(self):
        """Test validating submission completeness."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            notebook_path = Path(temp_dir) / "test_notebook.ipynb"
            dataset_path = Path(temp_dir) / "dataset.csv"
            readme_path = Path(temp_dir) / "README.md"
            
            # Create minimal notebook
            notebook_content = {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "print('Hello World')",
                        "outputs": [{"output_type": "stream", "text": "Hello World"}],
                        "execution_count": 1
                    }
                ]
            }
            with open(notebook_path, 'w') as f:
                json.dump(notebook_content, f)
            
            # Create test dataset
            with open(dataset_path, 'w') as f:
                f.write("col1,col2\n1,2\n3,4\n")
            
            # Create test README
            with open(readme_path, 'w') as f:
                f.write("# Test Project\n\nThis is a test project description with installation and usage instructions.")
            
            # Mock validation service methods
            self.mock_validation_service.validate_notebook_content.return_value = True
            self.mock_validation_service._validate_readme_content.return_value = True
            
            submission_status = self.service.validate_submission_completeness(
                self.test_workflow_state, temp_dir
            )
            
            self.assertEqual(submission_status.project_name, "Test Project")
            self.assertIsNotNone(submission_status.last_validated)
            
            # Check that some items are completed
            completed_items = [item for item in submission_status.checklist_items if item.is_completed]
            self.assertGreater(len(completed_items), 0)
    
    def test_check_deadline_status_normal(self):
        """Test deadline status check with normal deadline."""
        submission_status = SubmissionStatus(
            project_name="Test Project",
            deadline=datetime.now() + timedelta(days=5, hours=12)  # Add extra hours to ensure it's 5 days
        )
        
        is_ok, warnings = self.service.check_deadline_status(submission_status)
        
        self.assertTrue(is_ok)
        self.assertGreaterEqual(submission_status.days_until_deadline, 4)  # Allow for timing variations
        self.assertLessEqual(submission_status.days_until_deadline, 5)
        self.assertEqual(len(warnings), 0)
    
    def test_check_deadline_status_reminder(self):
        """Test deadline status with reminder threshold."""
        submission_status = SubmissionStatus(
            project_name="Test Project",
            deadline=datetime.now() + timedelta(days=3, hours=12)  # Add extra hours to ensure it's 3 days
        )
        
        is_ok, warnings = self.service.check_deadline_status(submission_status)
        
        self.assertTrue(is_ok)
        self.assertGreaterEqual(submission_status.days_until_deadline, 2)  # Allow for timing variations
        self.assertLessEqual(submission_status.days_until_deadline, 3)
        self.assertEqual(len(warnings), 1)
        self.assertIn("days remaining", warnings[0])
    
    def test_check_deadline_status_urgent(self):
        """Test deadline status with urgent deadline."""
        submission_status = SubmissionStatus(
            project_name="Test Project",
            deadline=datetime.now() + timedelta(hours=12)
        )
        
        is_ok, warnings = self.service.check_deadline_status(submission_status)
        
        self.assertTrue(is_ok)
        self.assertEqual(submission_status.days_until_deadline, 0)
        self.assertGreaterEqual(len(warnings), 1)  # Allow for multiple warnings
        self.assertTrue(any("hours remaining" in warning for warning in warnings))
    
    def test_check_deadline_status_overdue(self):
        """Test deadline status with overdue deadline."""
        submission_status = SubmissionStatus(
            project_name="Test Project",
            deadline=datetime.now() - timedelta(days=1)
        )
        
        is_ok, warnings = self.service.check_deadline_status(submission_status)
        
        self.assertFalse(is_ok)
        self.assertEqual(len(warnings), 1)
        self.assertIn("DEADLINE HAS PASSED", warnings[0])
    
    def test_check_deadline_status_no_deadline(self):
        """Test deadline status with no deadline set."""
        submission_status = SubmissionStatus(project_name="Test Project")
        
        is_ok, warnings = self.service.check_deadline_status(submission_status)
        
        self.assertFalse(is_ok)
        self.assertEqual(len(warnings), 1)
        self.assertIn("No deadline set", warnings[0])
    
    def test_generate_submission_summary(self):
        """Test generating submission summary."""
        # Create submission status with some completed items
        submission_status = SubmissionStatus(
            project_name="Test Project",
            deadline=datetime.now() + timedelta(days=5),
            overall_completion=75.0,
            is_ready_for_submission=False
        )
        
        # Add some checklist items
        submission_status.checklist_items = [
            SubmissionChecklist("item1", "Description 1", True, True),
            SubmissionChecklist("item2", "Description 2", True, False),
            SubmissionChecklist("item3", "Description 3", False, True),
        ]
        submission_status.days_until_deadline = 5
        submission_status.submission_warnings = ["Warning 1"]
        submission_status.submission_errors = ["Error 1"]
        submission_status.last_validated = datetime.now()
        
        summary = self.service.generate_submission_summary(submission_status)
        
        self.assertEqual(summary['project_name'], "Test Project")
        self.assertEqual(summary['overall_completion'], 75.0)
        self.assertFalse(summary['is_ready_for_submission'])
        
        # Check statistics
        stats = summary['statistics']
        self.assertEqual(stats['total_items'], 3)
        self.assertEqual(stats['completed_items'], 2)
        self.assertEqual(stats['required_items'], 2)
        self.assertEqual(stats['completed_required'], 1)
        
        # Check deadline info
        deadline_info = summary['deadline_info']
        self.assertEqual(deadline_info['days_until_deadline'], 5)
        self.assertFalse(deadline_info['is_overdue'])
        
        # Check checklist status
        self.assertEqual(len(summary['checklist_status']), 3)
        
        # Check warnings and errors
        self.assertEqual(summary['warnings'], ["Warning 1"])
        self.assertEqual(summary['errors'], ["Error 1"])
    
    def test_perform_final_validation_success(self):
        """Test successful final validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            self._create_test_files(temp_dir)
            
            # Mock validation service methods
            self.mock_validation_service.validate_notebook_content.return_value = True
            self.mock_validation_service._validate_readme_content.return_value = True
            
            # Set up workflow state with all steps completed
            self.test_workflow_state.completed_steps = list(range(1, 11))
            
            is_ready, submission_status = self.service.perform_final_validation(
                self.test_workflow_state, temp_dir
            )
            
            # Should be ready since all required items are completed
            self.assertTrue(is_ready)
            self.assertTrue(submission_status.is_ready_for_submission)
    
    def test_perform_final_validation_incomplete(self):
        """Test final validation with incomplete submission."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Don't create all required files
            
            # Mock validation service methods
            self.mock_validation_service.validate_notebook_content.return_value = False
            self.mock_validation_service._validate_readme_content.return_value = False
            
            is_ready, submission_status = self.service.perform_final_validation(
                self.test_workflow_state, temp_dir
            )
            
            # Should not be ready
            self.assertFalse(is_ready)
            self.assertFalse(submission_status.is_ready_for_submission)
    
    def test_validate_project_selection(self):
        """Test project selection validation."""
        submission_status = self.service.create_submission_checklist(self.test_workflow_state)
        self.service._validate_project_selection(submission_status, self.test_workflow_state)
        
        item = self.service._get_checklist_item(submission_status, 'project_selection')
        self.assertTrue(item.is_completed)
        self.assertIn("Test Project", item.validation_message)
    
    def test_validate_notebook_creation(self):
        """Test notebook creation validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test notebook
            notebook_path = Path(temp_dir) / "test.ipynb"
            with open(notebook_path, 'w') as f:
                json.dump({"cells": []}, f)
            
            submission_status = self.service.create_submission_checklist(self.test_workflow_state)
            self.service._validate_notebook_creation(submission_status, self.test_workflow_state, temp_dir)
            
            item = self.service._get_checklist_item(submission_status, 'notebook_created')
            self.assertTrue(item.is_completed)
            self.assertIn("test.ipynb", item.validation_message)
    
    def test_validate_dataset_upload(self):
        """Test dataset upload validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test dataset
            dataset_path = Path(temp_dir) / "dataset.csv"
            with open(dataset_path, 'w') as f:
                f.write("col1,col2\n1,2\n")
            
            submission_status = self.service.create_submission_checklist(self.test_workflow_state)
            self.service._validate_dataset_upload(submission_status, self.test_workflow_state, temp_dir)
            
            item = self.service._get_checklist_item(submission_status, 'dataset_uploaded')
            self.assertTrue(item.is_completed)
            self.assertIn("dataset.csv", item.validation_message)
    
    def test_validate_code_implementation(self):
        """Test code implementation validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test notebook
            notebook_path = Path(temp_dir) / "test.ipynb"
            with open(notebook_path, 'w') as f:
                json.dump({"cells": []}, f)
            
            # Mock validation service
            self.mock_validation_service.validate_notebook_content.return_value = True
            
            submission_status = self.service.create_submission_checklist(self.test_workflow_state)
            self.service._validate_code_implementation(submission_status, self.test_workflow_state, temp_dir)
            
            item = self.service._get_checklist_item(submission_status, 'code_implemented')
            self.assertTrue(item.is_completed)
            self.assertEqual(item.validation_message, "Code implementation validated")
    
    def test_validate_notebook_execution(self):
        """Test notebook execution validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create notebook with outputs
            notebook_path = Path(temp_dir) / "test.ipynb"
            notebook_content = {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "print('test')",
                        "outputs": [{"output_type": "stream", "text": "test"}],
                        "execution_count": 1
                    }
                ]
            }
            with open(notebook_path, 'w') as f:
                json.dump(notebook_content, f)
            
            submission_status = self.service.create_submission_checklist(self.test_workflow_state)
            self.service._validate_notebook_execution(submission_status, self.test_workflow_state, temp_dir)
            
            item = self.service._get_checklist_item(submission_status, 'notebook_executed')
            self.assertTrue(item.is_completed)
            self.assertEqual(item.validation_message, "Notebook has execution outputs")
    
    def test_validate_github_repository(self):
        """Test GitHub repository validation."""
        submission_status = self.service.create_submission_checklist(self.test_workflow_state)
        self.service._validate_github_repository(submission_status, self.test_workflow_state)
        
        item = self.service._get_checklist_item(submission_status, 'github_repo_created')
        self.assertTrue(item.is_completed)
        self.assertIn("testuser/test-project", item.validation_message)
    
    def test_validate_submission_link(self):
        """Test submission link validation."""
        submission_status = self.service.create_submission_checklist(self.test_workflow_state)
        self.service._validate_submission_link(submission_status, self.test_workflow_state)
        
        item = self.service._get_checklist_item(submission_status, 'submission_link_ready')
        self.assertTrue(item.is_completed)
        self.assertIn("https://github.com/testuser/test-project", item.validation_message)
    
    def test_calculate_overall_completion(self):
        """Test overall completion calculation."""
        submission_status = SubmissionStatus(project_name="Test")
        submission_status.checklist_items = [
            SubmissionChecklist("item1", "Desc1", True, True),
            SubmissionChecklist("item2", "Desc2", True, False),
            SubmissionChecklist("item3", "Desc3", True, True),
            SubmissionChecklist("item4", "Desc4", False, False),
        ]
        
        self.service._calculate_overall_completion(submission_status)
        
        # 2 out of 4 items completed = 50%
        self.assertEqual(submission_status.overall_completion, 50.0)
    
    def test_get_checklist_item(self):
        """Test getting checklist item by ID."""
        submission_status = SubmissionStatus(project_name="Test")
        test_item = SubmissionChecklist("test_id", "Test desc", True)
        submission_status.checklist_items = [test_item]
        
        found_item = self.service._get_checklist_item(submission_status, "test_id")
        self.assertEqual(found_item, test_item)
        
        not_found = self.service._get_checklist_item(submission_status, "nonexistent")
        self.assertIsNone(not_found)
    
    def test_validate_repository_accessibility(self):
        """Test repository accessibility validation."""
        # Valid GitHub URL
        valid_url = "https://github.com/user/repo"
        self.assertTrue(self.service._validate_repository_accessibility(valid_url))
        
        # Invalid URL
        invalid_url = "not-a-url"
        self.assertFalse(self.service._validate_repository_accessibility(invalid_url))
        
        # Non-GitHub URL
        non_github_url = "https://example.com/repo"
        self.assertFalse(self.service._validate_repository_accessibility(non_github_url))
    
    def test_validate_file_integrity(self):
        """Test file integrity validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with adequate size
            notebook_path = Path(temp_dir) / "test.ipynb"
            dataset_path = Path(temp_dir) / "dataset.csv"
            
            with open(notebook_path, 'w') as f:
                f.write('{"cells": []}' + 'x' * 200)  # Make it large enough
            
            with open(dataset_path, 'w') as f:
                f.write("col1,col2\n1,2\n3,4\n")  # Make it large enough
            
            self.assertTrue(self.service._validate_file_integrity(temp_dir))
    
    def test_check_common_submission_issues(self):
        """Test checking common submission issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create notebook with TODO
            notebook_path = Path(temp_dir) / "test.ipynb"
            notebook_content = {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "# TODO: Implement this function"
                    }
                ]
            }
            with open(notebook_path, 'w') as f:
                json.dump(notebook_content, f)
            
            # Create short README
            readme_path = Path(temp_dir) / "README.md"
            with open(readme_path, 'w') as f:
                f.write("Short")
            
            issues = self.service._check_common_submission_issues(self.test_workflow_state, temp_dir)
            
            self.assertGreater(len(issues), 0)
            self.assertTrue(any("TODO" in issue for issue in issues))
            self.assertTrue(any("README" in issue for issue in issues))
    
    def _create_test_files(self, temp_dir):
        """Helper method to create test files."""
        # Create notebook
        notebook_path = Path(temp_dir) / "test.ipynb"
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": "print('Hello World')",
                    "outputs": [{"output_type": "stream", "text": "Hello World"}],
                    "execution_count": 1
                }
            ]
        }
        with open(notebook_path, 'w') as f:
            json.dump(notebook_content, f)
        
        # Create dataset
        dataset_path = Path(temp_dir) / "dataset.csv"
        with open(dataset_path, 'w') as f:
            f.write("col1,col2\n1,2\n3,4\n")
        
        # Create README
        readme_path = Path(temp_dir) / "README.md"
        with open(readme_path, 'w') as f:
            f.write("# Test Project\n\nThis is a test project with proper description, installation instructions, and usage examples.")


if __name__ == '__main__':
    unittest.main()