"""
Unit tests for project initialization workflow steps.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import shutil
from pathlib import Path

from src.services.workflow_steps import (
    ProjectSelectionStep,
    NotebookCreationStep,
    AttendanceReminderStep,
    ProjectInitializationOrchestrator
)
from src.services.file_manager import FileManager
from src.services.validation_service import ValidationService
from src.models.interfaces import StepStatus
from src.models.workflow_models import ProjectData


class TestProjectSelectionStep(unittest.TestCase):
    """Test cases for ProjectSelectionStep."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(base_directory=self.temp_dir)
        self.validation_service = Mock(spec=ValidationService)
        self.step = ProjectSelectionStep(self.file_manager, self.validation_service)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_execute_success(self):
        """Test successful project selection and dataset download."""
        # Mock validation service
        self.validation_service.check_prerequisites.return_value = True
        
        # Mock successful dataset download
        with patch.object(self.file_manager, 'download_dataset') as mock_download:
            mock_download.return_value = {
                'success': True,
                'file_path': f'{self.temp_dir}/ev_analysis/dataset.csv',
                'filename': 'dataset.csv',
                'file_size': 1024
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.COMPLETED)
            self.assertIn('project_data', result.result_data)
            self.assertIn('dataset_download', result.result_data)
            self.assertEqual(result.result_data['selected_project_id'], 'ev_analysis')
    
    def test_execute_download_failure(self):
        """Test project selection with dataset download failure."""
        # Mock validation service
        self.validation_service.check_prerequisites.return_value = True
        
        # Mock failed dataset download
        with patch.object(self.file_manager, 'download_dataset') as mock_download:
            mock_download.return_value = {
                'success': False,
                'error': 'Network error'
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.FAILED)
            self.assertIn('Failed to download dataset', result.error_message)
    
    def test_validate_success(self):
        """Test successful validation."""
        self.validation_service.check_prerequisites.return_value = True
        
        self.assertTrue(self.step.validate())
    
    def test_validate_failure(self):
        """Test validation failure."""
        self.validation_service.check_prerequisites.return_value = False
        
        self.assertFalse(self.step.validate())
    
    def test_rollback(self):
        """Test rollback functionality."""
        with patch.object(self.file_manager, 'cleanup_temp_files') as mock_cleanup:
            mock_cleanup.return_value = True
            
            self.assertTrue(self.step.rollback())
            mock_cleanup.assert_called_once()
    
    def test_available_projects_structure(self):
        """Test that available projects have correct structure."""
        for project_id, project_info in self.step.available_projects.items():
            # Test that ProjectData can be created from project_info
            project_data = ProjectData(**project_info)
            self.assertEqual(project_data.project_id, project_id)
            self.assertTrue(project_data.validate())


class TestNotebookCreationStep(unittest.TestCase):
    """Test cases for NotebookCreationStep."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(base_directory=self.temp_dir)
        self.step = NotebookCreationStep(self.file_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_execute_success(self):
        """Test successful notebook creation."""
        with patch.object(self.file_manager, 'create_notebook_from_template') as mock_create:
            mock_create.return_value = {
                'success': True,
                'notebook_path': f'{self.temp_dir}/ev_analysis/ev_analysis.ipynb',
                'filename': 'ev_analysis.ipynb'
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.COMPLETED)
            self.assertIn('notebook_creation', result.result_data)
            self.assertIn('project_name', result.result_data)
    
    def test_execute_failure(self):
        """Test notebook creation failure."""
        with patch.object(self.file_manager, 'create_notebook_from_template') as mock_create:
            mock_create.return_value = {
                'success': False,
                'error': 'Template not found'
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.FAILED)
            self.assertIn('Failed to create notebook', result.error_message)
    
    def test_validate(self):
        """Test validation."""
        self.assertTrue(self.step.validate())
    
    def test_rollback(self):
        """Test rollback functionality."""
        # Create a test notebook file
        project_dir = Path(self.temp_dir) / "ev_analysis"
        project_dir.mkdir(parents=True, exist_ok=True)
        notebook_file = project_dir / "test.ipynb"
        notebook_file.write_text('{"cells": []}')
        
        self.assertTrue(notebook_file.exists())
        
        # Test rollback
        self.assertTrue(self.step.rollback())
        
        # Verify notebook file is removed
        self.assertFalse(notebook_file.exists())


class TestAttendanceReminderStep(unittest.TestCase):
    """Test cases for AttendanceReminderStep."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.step = AttendanceReminderStep()
    
    def test_execute_success(self):
        """Test successful attendance reminder."""
        with patch.object(self.step, '_check_attendance_status') as mock_check:
            mock_check.return_value = {
                'marked': True,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'present',
                'portal_verified': True
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.COMPLETED)
            self.assertIn('attendance_reminder', result.result_data)
            self.assertIn('attendance_status', result.result_data)
            self.assertTrue(result.result_data['checklist_completed'])
    
    def test_execute_attendance_not_marked(self):
        """Test attendance reminder when attendance not marked."""
        with patch.object(self.step, '_check_attendance_status') as mock_check:
            mock_check.return_value = {
                'marked': False,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'absent',
                'portal_verified': False
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.FAILED)
            self.assertIn('Attendance not marked', result.error_message)
    
    def test_validate(self):
        """Test validation."""
        self.assertTrue(self.step.validate())
    
    def test_rollback(self):
        """Test rollback (should always succeed)."""
        self.assertTrue(self.step.rollback())
    
    def test_generate_attendance_reminder(self):
        """Test attendance reminder generation."""
        reminder = self.step._generate_attendance_reminder()
        
        self.assertIn('ATTENDANCE REMINDER', reminder)
        self.assertIn('Skills4Future portal', reminder)
        self.assertIn('Mark attendance', reminder)
        
        # Check that all checklist items are included
        for item in self.step.attendance_checklist:
            self.assertIn(item, reminder)
    
    def test_check_attendance_status(self):
        """Test attendance status check."""
        status = self.step._check_attendance_status()
        
        self.assertIn('marked', status)
        self.assertIn('date', status)
        self.assertIn('status', status)
        self.assertIn('portal_verified', status)
        
        # Mock implementation should return marked=True
        self.assertTrue(status['marked'])


class TestProjectInitializationOrchestrator(unittest.TestCase):
    """Test cases for ProjectInitializationOrchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(base_directory=self.temp_dir)
        self.validation_service = Mock(spec=ValidationService)
        self.orchestrator = ProjectInitializationOrchestrator(
            self.file_manager, 
            self.validation_service
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        self.assertEqual(len(self.orchestrator.steps), 3)
        self.assertEqual(self.orchestrator.step_order, [1, 2, 3])
        self.assertEqual(len(self.orchestrator.results), 0)
    
    def test_execute_step_success(self):
        """Test executing a single step successfully."""
        # Mock validation service
        self.validation_service.check_prerequisites.return_value = True
        
        # Mock file manager methods
        with patch.object(self.file_manager, 'download_dataset') as mock_download:
            mock_download.return_value = {
                'success': True,
                'file_path': f'{self.temp_dir}/ev_analysis/dataset.csv',
                'filename': 'dataset.csv',
                'file_size': 1024
            }
            
            result = self.orchestrator.execute_step(1)
            
            self.assertEqual(result.status, StepStatus.COMPLETED)
            self.assertIn(1, self.orchestrator.results)
    
    def test_execute_step_not_found(self):
        """Test executing a non-existent step."""
        result = self.orchestrator.execute_step(999)
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn('Step 999 not found', result.error_message)
    
    def test_execute_step_validation_failure(self):
        """Test executing a step with validation failure."""
        self.validation_service.check_prerequisites.return_value = False
        
        result = self.orchestrator.execute_step(1)
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn('validation failed', result.error_message)
    
    def test_execute_all_steps_success(self):
        """Test executing all steps successfully."""
        # Mock validation service
        self.validation_service.check_prerequisites.return_value = True
        
        # Mock file manager methods
        with patch.object(self.file_manager, 'download_dataset') as mock_download, \
             patch.object(self.file_manager, 'create_notebook_from_template') as mock_create:
            
            mock_download.return_value = {
                'success': True,
                'file_path': f'{self.temp_dir}/ev_analysis/dataset.csv',
                'filename': 'dataset.csv',
                'file_size': 1024
            }
            
            mock_create.return_value = {
                'success': True,
                'notebook_path': f'{self.temp_dir}/ev_analysis/ev_analysis.ipynb',
                'filename': 'ev_analysis.ipynb'
            }
            
            results = self.orchestrator.execute_all_steps()
            
            self.assertEqual(len(results), 3)
            for result in results.values():
                self.assertEqual(result.status, StepStatus.COMPLETED)
    
    def test_execute_all_steps_failure_stops_execution(self):
        """Test that failure in one step stops execution of subsequent steps."""
        # Mock validation service
        self.validation_service.check_prerequisites.return_value = True
        
        # Mock file manager to fail on download
        with patch.object(self.file_manager, 'download_dataset') as mock_download:
            mock_download.return_value = {
                'success': False,
                'error': 'Network error'
            }
            
            results = self.orchestrator.execute_all_steps()
            
            # Should only have result for step 1 (which failed)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[1].status, StepStatus.FAILED)
    
    def test_rollback_step(self):
        """Test rolling back a step."""
        with patch.object(self.orchestrator.steps[1], 'rollback') as mock_rollback:
            mock_rollback.return_value = True
            
            self.assertTrue(self.orchestrator.rollback_step(1))
            mock_rollback.assert_called_once()
    
    def test_rollback_step_not_found(self):
        """Test rolling back a non-existent step."""
        self.assertFalse(self.orchestrator.rollback_step(999))
    
    def test_get_step_status(self):
        """Test getting step status."""
        # Initially no results
        self.assertIsNone(self.orchestrator.get_step_status(1))
        
        # Add a result
        from src.models.workflow_models import StepResult
        self.orchestrator.results[1] = StepResult(
            step_id=1,
            status=StepStatus.COMPLETED
        )
        
        self.assertEqual(self.orchestrator.get_step_status(1), StepStatus.COMPLETED)
    
    def test_is_initialization_complete(self):
        """Test checking if initialization is complete."""
        # Initially not complete
        self.assertFalse(self.orchestrator.is_initialization_complete())
        
        # Add completed results for all steps
        from src.models.workflow_models import StepResult
        for step_id in self.orchestrator.step_order:
            self.orchestrator.results[step_id] = StepResult(
                step_id=step_id,
                status=StepStatus.COMPLETED
            )
        
        self.assertTrue(self.orchestrator.is_initialization_complete())
    
    def test_get_initialization_summary(self):
        """Test getting initialization summary."""
        # Add some results
        from src.models.workflow_models import StepResult
        self.orchestrator.results[1] = StepResult(
            step_id=1,
            status=StepStatus.COMPLETED
        )
        self.orchestrator.results[2] = StepResult(
            step_id=2,
            status=StepStatus.FAILED,
            error_message="Test error"
        )
        
        summary = self.orchestrator.get_initialization_summary()
        
        self.assertEqual(summary['total_steps'], 3)
        self.assertEqual(summary['completed_steps'], 1)
        self.assertAlmostEqual(summary['progress_percentage'], 33.33, places=1)
        self.assertFalse(summary['is_complete'])
        self.assertIn('step_results', summary)
        self.assertEqual(len(summary['step_results']), 2)


if __name__ == '__main__':
    unittest.main()