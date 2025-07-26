"""
Unit tests for code and dataset management workflow steps.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import shutil
import json
from pathlib import Path

from src.services.workflow_steps import (
    CodeTemplatePopulationStep,
    DatasetUploadStep,
    NotebookCompletionValidationStep,
    CodeDatasetManagementOrchestrator
)
from src.services.file_manager import FileManager
from src.services.validation_service import ValidationService
from src.models.interfaces import StepStatus
from src.models.workflow_models import StepResult


class TestCodeTemplatePopulationStep(unittest.TestCase):
    """Test cases for CodeTemplatePopulationStep."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(base_directory=self.temp_dir)
        self.step = CodeTemplatePopulationStep(self.file_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_execute_success(self):
        """Test successful code template population."""
        # Create a test project directory and notebook
        project_dir = Path(self.temp_dir) / "ev_analysis"
        project_dir.mkdir(parents=True, exist_ok=True)
        notebook_file = project_dir / "ev_analysis.ipynb"
        
        # Create a basic notebook
        basic_notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# Test Notebook"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with open(notebook_file, 'w') as f:
            json.dump(basic_notebook, f)
        
        # Mock file manager methods
        with patch.object(self.file_manager, 'get_project_files') as mock_get_files:
            mock_get_files.return_value = {
                'success': True,
                'files': [
                    {
                        'filename': 'ev_analysis.ipynb',
                        'path': str(notebook_file),
                        'size': 1024
                    }
                ]
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.COMPLETED)
            self.assertIn('notebook_file', result.result_data)
            self.assertIn('population_result', result.result_data)
            self.assertTrue(result.result_data['population_result']['success'])
    
    def test_execute_no_project_files(self):
        """Test execution when project files cannot be retrieved."""
        with patch.object(self.file_manager, 'get_project_files') as mock_get_files:
            mock_get_files.return_value = {
                'success': False,
                'error': 'Project directory not found'
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.FAILED)
            self.assertIn('Failed to get project files', result.error_message)
    
    def test_execute_no_notebook_file(self):
        """Test execution when no notebook file is found."""
        with patch.object(self.file_manager, 'get_project_files') as mock_get_files:
            mock_get_files.return_value = {
                'success': True,
                'files': [
                    {
                        'filename': 'dataset.csv',
                        'path': '/path/to/dataset.csv',
                        'size': 2048
                    }
                ]
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.FAILED)
            self.assertIn('No notebook file found', result.error_message)
    
    def test_validate(self):
        """Test validation."""
        self.assertTrue(self.step.validate())
    
    def test_rollback(self):
        """Test rollback functionality."""
        with patch.object(self.file_manager, 'create_notebook_from_template') as mock_create:
            mock_create.return_value = {'success': True}
            
            self.assertTrue(self.step.rollback())
            mock_create.assert_called_once()
    
    def test_populate_notebook_with_code(self):
        """Test notebook population with enhanced code."""
        # Create a test notebook file
        project_dir = Path(self.temp_dir) / "test_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        notebook_file = project_dir / "test.ipynb"
        
        basic_notebook = {
            "cells": [],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with open(notebook_file, 'w') as f:
            json.dump(basic_notebook, f)
        
        # Test population
        result = self.step._populate_notebook_with_code(str(notebook_file), "test_project")
        
        self.assertTrue(result['success'])
        self.assertIn('cells_added', result)
        self.assertGreater(result['cells_added'], 0)
        
        # Verify notebook was updated
        with open(notebook_file, 'r') as f:
            updated_notebook = json.load(f)
        
        self.assertGreater(len(updated_notebook['cells']), 0)
    
    def test_get_enhanced_code_cells(self):
        """Test enhanced code cells generation."""
        cells = self.step._get_enhanced_code_cells()
        
        self.assertIsInstance(cells, list)
        self.assertGreater(len(cells), 0)
        
        # Check that we have both markdown and code cells
        markdown_cells = [cell for cell in cells if cell['cell_type'] == 'markdown']
        code_cells = [cell for cell in cells if cell['cell_type'] == 'code']
        
        self.assertGreater(len(markdown_cells), 0)
        self.assertGreater(len(code_cells), 0)


class TestDatasetUploadStep(unittest.TestCase):
    """Test cases for DatasetUploadStep."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(base_directory=self.temp_dir)
        self.step = DatasetUploadStep(self.file_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_execute_success(self):
        """Test successful dataset upload."""
        # Create a test dataset file
        project_dir = Path(self.temp_dir) / "ev_analysis"
        project_dir.mkdir(parents=True, exist_ok=True)
        dataset_file = project_dir / "dataset.csv"
        dataset_file.write_text("col1,col2\n1,2\n3,4\n")
        
        # Mock file manager methods
        with patch.object(self.file_manager, 'get_project_files') as mock_get_files, \
             patch.object(self.file_manager, 'validate_dataset_file') as mock_validate:
            
            mock_get_files.return_value = {
                'success': True,
                'files': [
                    {
                        'filename': 'dataset.csv',
                        'path': str(dataset_file),
                        'size': 1024
                    }
                ]
            }
            
            mock_validate.return_value = {
                'valid': True,
                'format': 'csv',
                'columns': ['col1', 'col2']
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.COMPLETED)
            self.assertIn('dataset_file', result.result_data)
            self.assertIn('validation_result', result.result_data)
            self.assertIn('upload_result', result.result_data)
    
    def test_execute_no_dataset_file(self):
        """Test execution when no dataset file is found."""
        with patch.object(self.file_manager, 'get_project_files') as mock_get_files:
            mock_get_files.return_value = {
                'success': True,
                'files': [
                    {
                        'filename': 'notebook.ipynb',
                        'path': '/path/to/notebook.ipynb',
                        'size': 2048
                    }
                ]
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.FAILED)
            self.assertIn('No dataset file found', result.error_message)
    
    def test_execute_validation_failure(self):
        """Test execution when dataset validation fails."""
        with patch.object(self.file_manager, 'get_project_files') as mock_get_files, \
             patch.object(self.file_manager, 'validate_dataset_file') as mock_validate:
            
            mock_get_files.return_value = {
                'success': True,
                'files': [
                    {
                        'filename': 'dataset.csv',
                        'path': '/path/to/dataset.csv',
                        'size': 1024
                    }
                ]
            }
            
            mock_validate.return_value = {
                'valid': False,
                'error': 'Invalid CSV format'
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.FAILED)
            self.assertIn('Dataset validation failed', result.error_message)
    
    def test_validate(self):
        """Test validation."""
        self.assertTrue(self.step.validate())
    
    def test_rollback(self):
        """Test rollback functionality."""
        self.assertTrue(self.step.rollback())
    
    def test_simulate_dataset_upload(self):
        """Test dataset upload simulation."""
        # Create a test file
        test_file = Path(self.temp_dir) / "test.csv"
        test_file.write_text("col1,col2\n1,2\n")
        
        result = self.step._simulate_dataset_upload(str(test_file), "test_project")
        
        self.assertTrue(result['success'])
        self.assertIn('upload_path', result)
        self.assertIn('file_size', result)
        self.assertIn('upload_time', result)
    
    def test_simulate_dataset_upload_file_not_found(self):
        """Test dataset upload simulation with missing file."""
        result = self.step._simulate_dataset_upload("/nonexistent/file.csv", "test_project")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestNotebookCompletionValidationStep(unittest.TestCase):
    """Test cases for NotebookCompletionValidationStep."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validation_service = Mock(spec=ValidationService)
        self.step = NotebookCompletionValidationStep(self.validation_service)
    
    def test_execute_success(self):
        """Test successful notebook validation."""
        self.validation_service.validate_notebook_content.return_value = True
        
        # Create a mock notebook file for detailed validation
        with patch.object(self.step, '_perform_detailed_validation') as mock_detailed:
            mock_detailed.return_value = {
                'file_exists': True,
                'valid_json': True,
                'has_cells': True,
                'estimated_completion': 85.0
            }
            
            result = self.step.execute()
            
            self.assertEqual(result.status, StepStatus.COMPLETED)
            self.assertIn('notebook_path', result.result_data)
            self.assertTrue(result.result_data['validation_passed'])
    
    def test_execute_validation_failure(self):
        """Test execution when notebook validation fails."""
        self.validation_service.validate_notebook_content.return_value = False
        
        result = self.step.execute()
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn('Notebook validation failed', result.error_message)
    
    def test_validate(self):
        """Test validation."""
        self.assertTrue(self.step.validate())
    
    def test_rollback(self):
        """Test rollback functionality."""
        self.assertTrue(self.step.rollback())
    
    def test_perform_detailed_validation_success(self):
        """Test detailed validation with valid notebook."""
        # Create a test notebook file
        temp_dir = tempfile.mkdtemp()
        try:
            notebook_file = Path(temp_dir) / "test.ipynb"
            
            test_notebook = {
                "cells": [
                    {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": ["# Test Notebook"]
                    },
                    {
                        "cell_type": "code",
                        "execution_count": 1,
                        "metadata": {},
                        "outputs": [],
                        "source": ["print('Hello, World!')"]
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 4
            }
            
            with open(notebook_file, 'w') as f:
                json.dump(test_notebook, f)
            
            result = self.step._perform_detailed_validation(str(notebook_file))
            
            self.assertTrue(result['file_exists'])
            self.assertTrue(result['valid_json'])
            self.assertTrue(result['has_cells'])
            self.assertTrue(result['has_code_cells'])
            self.assertTrue(result['has_markdown_cells'])
            self.assertEqual(result['cell_count'], 2)
            self.assertEqual(result['code_cell_count'], 1)
            self.assertEqual(result['markdown_cell_count'], 1)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_perform_detailed_validation_file_not_found(self):
        """Test detailed validation with missing file."""
        result = self.step._perform_detailed_validation("/nonexistent/file.ipynb")
        
        self.assertFalse(result['file_exists'])
        self.assertFalse(result['valid_json'])
        self.assertFalse(result['has_cells'])


class TestCodeDatasetManagementOrchestrator(unittest.TestCase):
    """Test cases for CodeDatasetManagementOrchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(base_directory=self.temp_dir)
        self.validation_service = Mock(spec=ValidationService)
        self.orchestrator = CodeDatasetManagementOrchestrator(
            self.file_manager, 
            self.validation_service
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        self.assertEqual(len(self.orchestrator.steps), 3)
        self.assertEqual(self.orchestrator.step_order, [4, 5, 6])
        self.assertEqual(len(self.orchestrator.results), 0)
    
    def test_execute_step_success(self):
        """Test executing a single step successfully."""
        # Create test project structure
        project_dir = Path(self.temp_dir) / "ev_analysis"
        project_dir.mkdir(parents=True, exist_ok=True)
        notebook_file = project_dir / "ev_analysis.ipynb"
        
        basic_notebook = {
            "cells": [],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with open(notebook_file, 'w') as f:
            json.dump(basic_notebook, f)
        
        # Mock file manager methods
        with patch.object(self.file_manager, 'get_project_files') as mock_get_files:
            mock_get_files.return_value = {
                'success': True,
                'files': [
                    {
                        'filename': 'ev_analysis.ipynb',
                        'path': str(notebook_file),
                        'size': 1024
                    }
                ]
            }
            
            result = self.orchestrator.execute_step(4)  # Code template population
            
            self.assertEqual(result.status, StepStatus.COMPLETED)
            self.assertIn(4, self.orchestrator.results)
    
    def test_execute_step_not_found(self):
        """Test executing a non-existent step."""
        result = self.orchestrator.execute_step(999)
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn('Step 999 not found', result.error_message)
    
    def test_execute_all_steps_success(self):
        """Test executing all steps successfully."""
        # Create test project structure
        project_dir = Path(self.temp_dir) / "ev_analysis"
        project_dir.mkdir(parents=True, exist_ok=True)
        notebook_file = project_dir / "ev_analysis.ipynb"
        dataset_file = project_dir / "dataset.csv"
        
        # Create test files
        basic_notebook = {
            "cells": [],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with open(notebook_file, 'w') as f:
            json.dump(basic_notebook, f)
        
        dataset_file.write_text("col1,col2\n1,2\n3,4\n")
        
        # Mock services
        self.validation_service.validate_notebook_content.return_value = True
        
        with patch.object(self.file_manager, 'get_project_files') as mock_get_files, \
             patch.object(self.file_manager, 'validate_dataset_file') as mock_validate:
            
            # Mock for both notebook and dataset files
            def mock_get_files_side_effect(project_name):
                if project_name == "ev_analysis":
                    return {
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
                return {'success': False, 'error': 'Project not found'}
            
            mock_get_files.side_effect = mock_get_files_side_effect
            mock_validate.return_value = {
                'valid': True,
                'format': 'csv',
                'columns': ['col1', 'col2']
            }
            
            results = self.orchestrator.execute_all_steps()
            
            self.assertEqual(len(results), 3)
            for result in results.values():
                self.assertEqual(result.status, StepStatus.COMPLETED)
    
    def test_execute_all_steps_failure_stops_execution(self):
        """Test that failure in one step stops execution of subsequent steps."""
        # Mock file manager to fail on get_project_files
        with patch.object(self.file_manager, 'get_project_files') as mock_get_files:
            mock_get_files.return_value = {
                'success': False,
                'error': 'Project directory not found'
            }
            
            results = self.orchestrator.execute_all_steps()
            
            # Should only have result for step 4 (which failed)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[4].status, StepStatus.FAILED)
    
    def test_rollback_step(self):
        """Test rolling back a step."""
        with patch.object(self.orchestrator.steps[4], 'rollback') as mock_rollback:
            mock_rollback.return_value = True
            
            self.assertTrue(self.orchestrator.rollback_step(4))
            mock_rollback.assert_called_once()
    
    def test_rollback_step_not_found(self):
        """Test rolling back a non-existent step."""
        self.assertFalse(self.orchestrator.rollback_step(999))
    
    def test_get_step_status(self):
        """Test getting step status."""
        # Initially no results
        self.assertIsNone(self.orchestrator.get_step_status(4))
        
        # Add a result
        self.orchestrator.results[4] = StepResult(
            step_id=4,
            status=StepStatus.COMPLETED
        )
        
        self.assertEqual(self.orchestrator.get_step_status(4), StepStatus.COMPLETED)
    
    def test_is_management_complete(self):
        """Test checking if management is complete."""
        # Initially not complete
        self.assertFalse(self.orchestrator.is_management_complete())
        
        # Add completed results for all steps
        for step_id in self.orchestrator.step_order:
            self.orchestrator.results[step_id] = StepResult(
                step_id=step_id,
                status=StepStatus.COMPLETED
            )
        
        self.assertTrue(self.orchestrator.is_management_complete())
    
    def test_get_management_summary(self):
        """Test getting management summary."""
        # Add some results
        self.orchestrator.results[4] = StepResult(
            step_id=4,
            status=StepStatus.COMPLETED
        )
        self.orchestrator.results[5] = StepResult(
            step_id=5,
            status=StepStatus.FAILED,
            error_message="Test error"
        )
        
        summary = self.orchestrator.get_management_summary()
        
        self.assertEqual(summary['total_steps'], 3)
        self.assertEqual(summary['completed_steps'], 1)
        self.assertAlmostEqual(summary['progress_percentage'], 33.33, places=1)
        self.assertFalse(summary['is_complete'])
        self.assertIn('step_results', summary)
        self.assertEqual(len(summary['step_results']), 2)


if __name__ == '__main__':
    unittest.main()