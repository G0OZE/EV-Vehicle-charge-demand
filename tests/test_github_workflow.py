"""
Unit tests for GitHub workflow steps.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import shutil
from pathlib import Path

from src.services.workflow_steps import (
    RepositoryCreationStep,
    FileUploadOrchestrationStep,
    SubmissionLinkGenerationStep,
    GitHubWorkflowOrchestrator
)
from src.services.file_manager import FileManager
from src.services.github_service import GitHubService
from src.models.interfaces import StepStatus
from src.models.workflow_models import StepResult


class TestRepositoryCreationStep(unittest.TestCase):
    """Test cases for RepositoryCreationStep."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.github_service = Mock(spec=GitHubService)
        self.file_manager = FileManager(base_directory=self.temp_dir)
        self.step = RepositoryCreationStep(self.github_service, self.file_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_execute_success(self):
        """Test successful repository creation."""
        # Mock GitHub service methods
        self.github_service.is_authenticated.return_value = True
        self.github_service.create_repository.return_value = {
            'html_url': 'https://github.com/user/aicte-ev_analysis-20240119',
            'name': 'aicte-ev_analysis-20240119'
        }
        self.github_service.upload_file.return_value = {
            'content': {'name': 'README.md'}
        }
        
        result = self.step.execute()
        
        self.assertEqual(result.status, StepStatus.COMPLETED)
        self.assertIn('repository_name', result.result_data)
        self.assertIn('repository_url', result.result_data)
        self.assertIn('repository_description', result.result_data)
        self.assertTrue(result.result_data['readme_initialized'])
    
    def test_execute_repository_creation_failure(self):
        """Test execution when repository creation fails."""
        self.github_service.is_authenticated.return_value = True
        self.github_service.create_repository.return_value = None  # Simulate failure
        
        result = self.step.execute()
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn('Failed to create repository', result.error_message)
    
    def test_execute_readme_initialization_failure(self):
        """Test execution when README initialization fails."""
        self.github_service.is_authenticated.return_value = True
        self.github_service.create_repository.return_value = {
            'html_url': 'https://github.com/user/test-repo',
            'name': 'test-repo'
        }
        self.github_service.upload_file.return_value = None  # Simulate failure
        
        result = self.step.execute()
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn('Failed to initialize README', result.error_message)
    
    def test_validate_success(self):
        """Test successful validation."""
        self.github_service.is_authenticated.return_value = True
        
        self.assertTrue(self.step.validate())
    
    def test_validate_failure(self):
        """Test validation failure."""
        self.github_service.is_authenticated.return_value = False
        
        self.assertFalse(self.step.validate())
    
    def test_rollback(self):
        """Test rollback functionality."""
        self.assertTrue(self.step.rollback())
    
    def test_generate_readme_content(self):
        """Test README content generation."""
        content = self.step._generate_readme_content("ev_analysis", "Test project description")
        
        self.assertIn("Ev Analysis", content)
        self.assertIn("Test project description", content)
        self.assertIn("## Project Overview", content)
        self.assertIn("## Contents", content)
        self.assertIn("## Setup Instructions", content)
        self.assertIn("ev_analysis.ipynb", content)
        self.assertIn("dataset.csv", content)


class TestFileUploadOrchestrationStep(unittest.TestCase):
    """Test cases for FileUploadOrchestrationStep."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.github_service = Mock(spec=GitHubService)
        self.file_manager = FileManager(base_directory=self.temp_dir)
        self.step = FileUploadOrchestrationStep(self.github_service, self.file_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_execute_success(self):
        """Test successful file upload orchestration."""
        # Create test files
        project_dir = Path(self.temp_dir) / "ev_analysis"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        notebook_file = project_dir / "ev_analysis.ipynb"
        notebook_file.write_text('{"cells": []}')
        
        dataset_file = project_dir / "dataset.csv"
        dataset_file.write_text("col1,col2\n1,2\n")
        
        # Mock services
        self.github_service.is_authenticated.return_value = True
        self.github_service.upload_file.return_value = {'content': {'name': 'test.ipynb'}}
        
        with patch.object(self.file_manager, 'prepare_upload_bundle') as mock_prepare:
            mock_prepare.return_value = {
                'success': True,
                'files': [
                    {
                        'filename': 'ev_analysis.ipynb',
                        'path': str(notebook_file),
                        'size': 1024
                    },
                    {
                        'filename': 'dataset.csv',
                        'path': str(dataset_file),
                        'size': 512
                    }
                ]
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.COMPLETED)
            self.assertIn('repository_name', result.result_data)
            self.assertIn('uploaded_files', result.result_data)
            self.assertEqual(result.result_data['total_files'], 2)
    
    def test_execute_prepare_bundle_failure(self):
        """Test execution when bundle preparation fails."""
        self.github_service.is_authenticated.return_value = True
        
        with patch.object(self.file_manager, 'prepare_upload_bundle') as mock_prepare:
            mock_prepare.return_value = {
                'success': False,
                'error': 'Project directory not found'
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.FAILED)
            self.assertIn('Failed to prepare upload bundle', result.error_message)
    
    def test_execute_upload_failure(self):
        """Test execution when file upload fails."""
        # Create test file
        project_dir = Path(self.temp_dir) / "ev_analysis"
        project_dir.mkdir(parents=True, exist_ok=True)
        test_file = project_dir / "test.txt"
        test_file.write_text("test content")
        
        # Mock services
        self.github_service.is_authenticated.return_value = True
        self.github_service.upload_file.return_value = None  # Simulate failure
        
        with patch.object(self.file_manager, 'prepare_upload_bundle') as mock_prepare:
            mock_prepare.return_value = {
                'success': True,
                'files': [
                    {
                        'filename': 'test.txt',
                        'path': str(test_file),
                        'size': 12
                    }
                ]
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.FAILED)
            self.assertIn('Failed to upload test.txt', result.error_message)
    
    def test_validate_success(self):
        """Test successful validation."""
        self.github_service.is_authenticated.return_value = True
        
        self.assertTrue(self.step.validate())
    
    def test_validate_failure(self):
        """Test validation failure."""
        self.github_service.is_authenticated.return_value = False
        
        self.assertFalse(self.step.validate())
    
    def test_rollback(self):
        """Test rollback functionality."""
        self.assertTrue(self.step.rollback())


class TestSubmissionLinkGenerationStep(unittest.TestCase):
    """Test cases for SubmissionLinkGenerationStep."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.github_service = Mock(spec=GitHubService)
        self.step = SubmissionLinkGenerationStep(self.github_service)
    
    def test_execute_success(self):
        """Test successful submission link generation."""
        self.github_service.is_authenticated.return_value = True
        self.github_service.get_repository_url.return_value = 'https://github.com/user/test-repo'
        
        result = self.step.execute()
        
        self.assertEqual(result.status, StepStatus.COMPLETED)
        self.assertIn('repository_name', result.result_data)
        self.assertIn('repository_url', result.result_data)
        self.assertIn('submission_link', result.result_data)
        self.assertIn('submission_summary', result.result_data)
        self.assertTrue(result.result_data['ready_for_lms_submission'])
    
    def test_execute_url_generation_failure(self):
        """Test execution when URL generation fails."""
        self.github_service.is_authenticated.return_value = True
        self.github_service.get_repository_url.return_value = None
        
        result = self.step.execute()
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn('Failed to generate repository URL', result.error_message)
    
    def test_validate_success(self):
        """Test successful validation."""
        self.github_service.is_authenticated.return_value = True
        
        self.assertTrue(self.step.validate())
    
    def test_validate_failure(self):
        """Test validation failure."""
        self.github_service.is_authenticated.return_value = False
        
        self.assertFalse(self.step.validate())
    
    def test_rollback(self):
        """Test rollback functionality."""
        self.assertTrue(self.step.rollback())
    
    def test_generate_submission_summary(self):
        """Test submission summary generation."""
        summary = self.step._generate_submission_summary(
            "ev_analysis", 
            "aicte-ev_analysis-20240119", 
            "https://github.com/user/test-repo"
        )
        
        self.assertIn('project_title', summary)
        self.assertIn('repository_name', summary)
        self.assertIn('repository_url', summary)
        self.assertIn('submission_date', summary)
        self.assertIn('files_included', summary)
        self.assertIn('lms_submission_instructions', summary)
        
        self.assertEqual(summary['project_title'], 'Ev Analysis')
        self.assertEqual(summary['repository_name'], 'aicte-ev_analysis-20240119')
        self.assertEqual(summary['repository_url'], 'https://github.com/user/test-repo')
        self.assertTrue(summary['ready_for_submission'])
        
        # Check that instructions are provided
        self.assertIsInstance(summary['lms_submission_instructions'], list)
        self.assertGreater(len(summary['lms_submission_instructions']), 0)


class TestGitHubWorkflowOrchestrator(unittest.TestCase):
    """Test cases for GitHubWorkflowOrchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.github_service = Mock(spec=GitHubService)
        self.file_manager = FileManager(base_directory=self.temp_dir)
        self.orchestrator = GitHubWorkflowOrchestrator(
            self.github_service, 
            self.file_manager
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        self.assertEqual(len(self.orchestrator.steps), 3)
        self.assertEqual(self.orchestrator.step_order, [7, 8, 9])
        self.assertEqual(len(self.orchestrator.results), 0)
    
    def test_execute_step_success(self):
        """Test executing a single step successfully."""
        # Mock GitHub service
        self.github_service.is_authenticated.return_value = True
        self.github_service.create_repository.return_value = {
            'html_url': 'https://github.com/user/test-repo',
            'name': 'test-repo'
        }
        self.github_service.upload_file.return_value = {'content': {'name': 'README.md'}}
        
        result = self.orchestrator.execute_step(7)  # Repository creation
        
        self.assertEqual(result.status, StepStatus.COMPLETED)
        self.assertIn(7, self.orchestrator.results)
    
    def test_execute_step_not_found(self):
        """Test executing a non-existent step."""
        result = self.orchestrator.execute_step(999)
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn('Step 999 not found', result.error_message)
    
    def test_execute_step_validation_failure(self):
        """Test executing a step with validation failure."""
        self.github_service.is_authenticated.return_value = False
        
        result = self.orchestrator.execute_step(7)
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn('validation failed', result.error_message)
    
    def test_execute_all_steps_success(self):
        """Test executing all steps successfully."""
        # Create test project structure
        project_dir = Path(self.temp_dir) / "ev_analysis"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        notebook_file = project_dir / "ev_analysis.ipynb"
        notebook_file.write_text('{"cells": []}')
        
        dataset_file = project_dir / "dataset.csv"
        dataset_file.write_text("col1,col2\n1,2\n")
        
        # Mock GitHub service
        self.github_service.is_authenticated.return_value = True
        self.github_service.create_repository.return_value = {
            'html_url': 'https://github.com/user/test-repo',
            'name': 'test-repo'
        }
        self.github_service.upload_file.return_value = {'content': {'name': 'README.md'}}
        self.github_service.get_repository_url.return_value = 'https://github.com/user/test-repo'
        
        # Mock file manager
        with patch.object(self.file_manager, 'prepare_upload_bundle') as mock_prepare:
            mock_prepare.return_value = {
                'success': True,
                'files': [
                    {
                        'filename': 'ev_analysis.ipynb',
                        'path': str(notebook_file),
                        'size': 1024
                    },
                    {
                        'filename': 'dataset.csv',
                        'path': str(dataset_file),
                        'size': 512
                    }
                ]
            }
            
            results = self.orchestrator.execute_all_steps()
            
            self.assertEqual(len(results), 3)
            for result in results.values():
                self.assertEqual(result.status, StepStatus.COMPLETED)
    
    def test_execute_all_steps_failure_stops_execution(self):
        """Test that failure in one step stops execution of subsequent steps."""
        # Mock GitHub service to fail on repository creation
        self.github_service.is_authenticated.return_value = True
        self.github_service.create_repository.return_value = None  # Simulate failure
        
        results = self.orchestrator.execute_all_steps()
        
        # Should only have result for step 7 (which failed)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[7].status, StepStatus.FAILED)
    
    def test_rollback_step(self):
        """Test rolling back a step."""
        with patch.object(self.orchestrator.steps[7], 'rollback') as mock_rollback:
            mock_rollback.return_value = True
            
            self.assertTrue(self.orchestrator.rollback_step(7))
            mock_rollback.assert_called_once()
    
    def test_rollback_step_not_found(self):
        """Test rolling back a non-existent step."""
        self.assertFalse(self.orchestrator.rollback_step(999))
    
    def test_get_step_status(self):
        """Test getting step status."""
        # Initially no results
        self.assertIsNone(self.orchestrator.get_step_status(7))
        
        # Add a result
        self.orchestrator.results[7] = StepResult(
            step_id=7,
            status=StepStatus.COMPLETED
        )
        
        self.assertEqual(self.orchestrator.get_step_status(7), StepStatus.COMPLETED)
    
    def test_is_github_workflow_complete(self):
        """Test checking if GitHub workflow is complete."""
        # Initially not complete
        self.assertFalse(self.orchestrator.is_github_workflow_complete())
        
        # Add completed results for all steps
        for step_id in self.orchestrator.step_order:
            self.orchestrator.results[step_id] = StepResult(
                step_id=step_id,
                status=StepStatus.COMPLETED
            )
        
        self.assertTrue(self.orchestrator.is_github_workflow_complete())
    
    def test_get_github_workflow_summary(self):
        """Test getting GitHub workflow summary."""
        # Add some results
        self.orchestrator.results[7] = StepResult(
            step_id=7,
            status=StepStatus.COMPLETED
        )
        self.orchestrator.results[8] = StepResult(
            step_id=8,
            status=StepStatus.FAILED,
            error_message="Test error"
        )
        
        summary = self.orchestrator.get_github_workflow_summary()
        
        self.assertEqual(summary['total_steps'], 3)
        self.assertEqual(summary['completed_steps'], 1)
        self.assertAlmostEqual(summary['progress_percentage'], 33.33, places=1)
        self.assertFalse(summary['is_complete'])
        self.assertIsNone(summary['repository_url'])
        self.assertIsNone(summary['submission_link'])
        self.assertFalse(summary['ready_for_lms_submission'])
        self.assertIn('step_results', summary)
        self.assertEqual(len(summary['step_results']), 2)
    
    def test_get_github_workflow_summary_with_submission_link(self):
        """Test getting GitHub workflow summary with submission link."""
        # Add completed results including submission link generation
        self.orchestrator.results[9] = StepResult(
            step_id=9,
            status=StepStatus.COMPLETED,
            result_data={
                'repository_url': 'https://github.com/user/test-repo',
                'submission_link': 'https://github.com/user/test-repo'
            }
        )
        
        summary = self.orchestrator.get_github_workflow_summary()
        
        self.assertEqual(summary['repository_url'], 'https://github.com/user/test-repo')
        self.assertEqual(summary['submission_link'], 'https://github.com/user/test-repo')
        self.assertTrue(summary['ready_for_lms_submission'])


if __name__ == '__main__':
    unittest.main()