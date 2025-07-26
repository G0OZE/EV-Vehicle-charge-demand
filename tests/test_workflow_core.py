"""
Unit tests for workflow core implementation.
"""
import unittest
import tempfile
import shutil
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.services.workflow_core import WorkflowCore
from src.services.progress_store import FileProgressStore
from src.models.interfaces import WorkflowStep, StepStatus
from src.models.workflow_models import StepResult


class MockWorkflowStep(WorkflowStep):
    """Mock workflow step for testing."""
    
    def __init__(self, should_succeed=True, should_validate=True):
        self.should_succeed = should_succeed
        self.should_validate = should_validate
        self.executed = False
        self.validated = False
        self.rolled_back = False
    
    def execute(self) -> StepResult:
        """Mock execute method."""
        self.executed = True
        if self.should_succeed:
            return StepResult(
                step_id=1,
                status=StepStatus.COMPLETED,
                result_data={'success': True}
            )
        else:
            return StepResult(
                step_id=1,
                status=StepStatus.FAILED,
                error_message="Mock step failed"
            )
    
    def validate(self) -> bool:
        """Mock validate method."""
        self.validated = True
        return self.should_validate
    
    def rollback(self) -> bool:
        """Mock rollback method."""
        self.rolled_back = True
        return True


class TestWorkflowCore(unittest.TestCase):
    """Test cases for WorkflowCore."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.progress_store = FileProgressStore(self.temp_dir)
        self.workflow_core = WorkflowCore(self.progress_store)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test workflow core initialization."""
        self.assertIsNotNone(self.workflow_core.progress_store)
        self.assertIsNone(self.workflow_core.workflow_state)
        self.assertEqual(len(self.workflow_core.registered_steps), 0)
    
    def test_register_step(self):
        """Test step registration."""
        step_id = 1
        self.workflow_core.register_step(step_id, MockWorkflowStep)
        
        self.assertIn(step_id, self.workflow_core.registered_steps)
        self.assertEqual(self.workflow_core.registered_steps[step_id], MockWorkflowStep)
    
    def test_initialize_workflow(self):
        """Test workflow initialization."""
        project_name = "test_project"
        success = self.workflow_core.initialize_workflow(project_name)
        
        self.assertTrue(success)
        self.assertIsNotNone(self.workflow_core.workflow_state)
        self.assertEqual(self.workflow_core.workflow_state.project_name, project_name)
        self.assertEqual(self.workflow_core.workflow_state.current_step, 1)
    
    def test_load_existing_workflow(self):
        """Test loading existing workflow."""
        # Initialize workflow first
        project_name = "test_project"
        self.workflow_core.initialize_workflow(project_name)
        
        # Create new workflow core instance
        new_workflow_core = WorkflowCore(self.progress_store)
        success = new_workflow_core.load_existing_workflow()
        
        self.assertTrue(success)
        self.assertIsNotNone(new_workflow_core.workflow_state)
        self.assertEqual(new_workflow_core.workflow_state.project_name, project_name)
    
    def test_execute_step_success(self):
        """Test successful step execution."""
        # Setup
        step_id = 1
        self.workflow_core.register_step(step_id, MockWorkflowStep)
        self.workflow_core.initialize_workflow("test_project")
        
        # Execute step
        result = self.workflow_core.execute_step(step_id)
        
        self.assertEqual(result.status, StepStatus.COMPLETED)
        self.assertTrue(self.workflow_core.workflow_state.is_step_completed(step_id))
        self.assertEqual(self.workflow_core.workflow_state.current_step, step_id + 1)
    
    def test_execute_step_failure(self):
        """Test failed step execution."""
        # Setup with failing step
        step_id = 1
        
        class FailingStep(MockWorkflowStep):
            def __init__(self):
                super().__init__(should_succeed=False)
        
        self.workflow_core.register_step(step_id, FailingStep)
        self.workflow_core.initialize_workflow("test_project")
        
        # Execute step
        result = self.workflow_core.execute_step(step_id)
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertFalse(self.workflow_core.workflow_state.is_step_completed(step_id))
    
    def test_step_dependencies(self):
        """Test step dependency validation."""
        # Register steps with dependencies
        self.workflow_core.register_step(1, MockWorkflowStep)
        self.workflow_core.register_step(2, MockWorkflowStep)
        self.workflow_core.register_step_dependencies(2, [1])  # Step 2 depends on step 1
        
        self.workflow_core.initialize_workflow("test_project")
        
        # Step 2 should not be executable before step 1
        self.assertFalse(self.workflow_core.can_execute_step(2))
        
        # Execute step 1
        self.workflow_core.execute_step(1)
        
        # Now step 2 should be executable
        self.assertTrue(self.workflow_core.can_execute_step(2))
    
    def test_step_validation(self):
        """Test step validation."""
        step_id = 1
        
        class InvalidatingStep(MockWorkflowStep):
            def __init__(self):
                super().__init__(should_validate=False)
        
        self.workflow_core.register_step(step_id, InvalidatingStep)
        self.workflow_core.initialize_workflow("test_project")
        
        # Execute step
        result = self.workflow_core.execute_step(step_id)
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn("validation failed", result.error_message.lower())
    
    def test_custom_validator(self):
        """Test custom step validator."""
        step_id = 1
        validator_called = False
        
        def custom_validator():
            nonlocal validator_called
            validator_called = True
            return False  # Fail validation
        
        self.workflow_core.register_step(step_id, MockWorkflowStep)
        self.workflow_core.register_step_validator(step_id, custom_validator)
        self.workflow_core.initialize_workflow("test_project")
        
        # Validate step prerequisites
        result = self.workflow_core.validate_step_prerequisites(step_id)
        
        self.assertFalse(result)
        self.assertTrue(validator_called)
    
    def test_error_handler(self):
        """Test custom error handler."""
        step_id = 1
        handler_called = False
        
        def error_handler(error):
            nonlocal handler_called
            handler_called = True
            return True  # Indicate error was handled
        
        class FailingStep(MockWorkflowStep):
            def __init__(self):
                super().__init__(should_succeed=False)
        
        self.workflow_core.register_step(step_id, FailingStep)
        self.workflow_core.register_error_handler(step_id, error_handler)
        self.workflow_core.initialize_workflow("test_project")
        
        # Execute step with retry
        result = self.workflow_core.execute_step_with_retry(step_id)
        
        # Error handler should have been called
        self.assertTrue(handler_called)
    
    def test_retry_logic(self):
        """Test step retry logic."""
        step_id = 1
        execution_count = 0
        
        class RetryableStep(WorkflowStep):
            def execute(self):
                nonlocal execution_count
                execution_count += 1
                if execution_count < 3:  # Fail first 2 attempts
                    return StepResult(
                        step_id=step_id,
                        status=StepStatus.FAILED,
                        error_message="Temporary failure"
                    )
                else:  # Succeed on 3rd attempt
                    return StepResult(
                        step_id=step_id,
                        status=StepStatus.COMPLETED,
                        result_data={'success': True}
                    )
            
            def validate(self):
                return True
            
            def rollback(self):
                return True
        
        self.workflow_core.register_step(step_id, RetryableStep)
        self.workflow_core.initialize_workflow("test_project")
        
        # Execute step with retry
        result = self.workflow_core.execute_step_with_retry(step_id)
        
        self.assertEqual(result.status, StepStatus.COMPLETED)
        self.assertEqual(execution_count, 3)  # Should have retried
    
    def test_rollback_step(self):
        """Test step rollback."""
        step_id = 1
        self.workflow_core.register_step(step_id, MockWorkflowStep)
        self.workflow_core.initialize_workflow("test_project")
        
        # Execute step first
        self.workflow_core.execute_step(step_id)
        self.assertTrue(self.workflow_core.workflow_state.is_step_completed(step_id))
        
        # Rollback step
        success = self.workflow_core.rollback_step(step_id)
        
        self.assertTrue(success)
        self.assertFalse(self.workflow_core.workflow_state.is_step_completed(step_id))
    
    def test_get_next_available_step(self):
        """Test getting next available step."""
        # Register steps with dependencies
        self.workflow_core.register_step(1, MockWorkflowStep)
        self.workflow_core.register_step(2, MockWorkflowStep)
        self.workflow_core.register_step(3, MockWorkflowStep)
        self.workflow_core.register_step_dependencies(3, [1, 2])
        
        self.workflow_core.initialize_workflow("test_project")
        
        # Initially, step 1 and 2 should be available
        next_step = self.workflow_core.get_next_available_step()
        self.assertIn(next_step, [1, 2])
        
        # Complete step 1
        self.workflow_core.execute_step(1)
        
        # Step 2 should still be available, step 3 not yet
        next_step = self.workflow_core.get_next_available_step()
        self.assertEqual(next_step, 2)
        
        # Complete step 2
        self.workflow_core.execute_step(2)
        
        # Now step 3 should be available
        next_step = self.workflow_core.get_next_available_step()
        self.assertEqual(next_step, 3)
    
    def test_get_step_status(self):
        """Test getting step status."""
        step_id = 1
        self.workflow_core.register_step(step_id, MockWorkflowStep)
        self.workflow_core.initialize_workflow("test_project")
        
        # Initially pending
        status = self.workflow_core.get_step_status(step_id)
        self.assertEqual(status, StepStatus.PENDING)
        
        # Execute step
        self.workflow_core.execute_step(step_id)
        
        # Should be completed
        status = self.workflow_core.get_step_status(step_id)
        self.assertEqual(status, StepStatus.COMPLETED)
    
    def test_recover_from_failure(self):
        """Test recovery from failed step."""
        step_id = 1
        self.workflow_core.register_step(step_id, MockWorkflowStep)
        self.workflow_core.initialize_workflow("test_project")
        
        # Execute and complete step
        self.workflow_core.execute_step(step_id)
        
        # Simulate failure recovery
        success = self.workflow_core.recover_from_failure(step_id)
        
        self.assertTrue(success)
        self.assertFalse(self.workflow_core.workflow_state.is_step_completed(step_id))
        self.assertEqual(self.workflow_core.workflow_state.current_step, step_id)
    
    def test_get_workflow_summary(self):
        """Test getting workflow summary."""
        # Register multiple steps
        for i in range(1, 4):
            self.workflow_core.register_step(i, MockWorkflowStep)
        
        self.workflow_core.initialize_workflow("test_project")
        
        # Execute some steps
        self.workflow_core.execute_step(1)
        self.workflow_core.execute_step(2)
        
        # Get summary
        summary = self.workflow_core.get_workflow_summary()
        
        self.assertEqual(summary['project_name'], "test_project")
        self.assertEqual(summary['completed_steps'], 2)
        self.assertEqual(summary['total_steps'], 3)
        self.assertAlmostEqual(summary['progress_percentage'], 66.67, places=1)
    
    def test_get_workflow_health(self):
        """Test getting workflow health."""
        # Register steps
        for i in range(1, 4):
            self.workflow_core.register_step(i, MockWorkflowStep)
        
        self.workflow_core.initialize_workflow("test_project")
        
        # Execute some steps
        self.workflow_core.execute_step(1)
        self.workflow_core.execute_step(2)
        
        # Get health
        health = self.workflow_core.get_workflow_health()
        
        self.assertEqual(health['status'], 'active')
        self.assertEqual(health['completed_steps'], 2)
        self.assertEqual(health['total_steps'], 3)
        self.assertIn(health['health'], ['fair', 'good', 'excellent'])
        self.assertIsNotNone(health['next_available_step'])
    
    def test_workflow_not_initialized(self):
        """Test operations when workflow is not initialized."""
        step_id = 1
        self.workflow_core.register_step(step_id, MockWorkflowStep)
        
        # Try to execute step without initialization
        result = self.workflow_core.execute_step(step_id)
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn("not initialized", result.error_message.lower())
    
    def test_unregistered_step_execution(self):
        """Test executing unregistered step."""
        self.workflow_core.initialize_workflow("test_project")
        
        # Try to execute unregistered step
        result = self.workflow_core.execute_step(999)
        
        self.assertEqual(result.status, StepStatus.FAILED)
        self.assertIn("not registered", result.error_message.lower())


if __name__ == '__main__':
    unittest.main()