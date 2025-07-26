"""
Core workflow orchestration and step management.
"""
from typing import Dict, List, Optional, Type, Callable, Any
from datetime import datetime
from ..models.interfaces import WorkflowStep, ProgressStore, StepStatus
from ..models.workflow_models import WorkflowState, StepResult
from ..utils.config import config
from .user_guidance import UserGuidanceService


class WorkflowCore:
    """Orchestrates the step-by-step workflow process."""
    
    def __init__(self, progress_store: ProgressStore):
        self.progress_store = progress_store
        self.workflow_state: Optional[WorkflowState] = None
        self.registered_steps: Dict[int, Type[WorkflowStep]] = {}
        self.step_instances: Dict[int, WorkflowStep] = {}
        self.step_dependencies: Dict[int, List[int]] = {}
        self.step_validators: Dict[int, Callable[[], bool]] = {}
        self.error_handlers: Dict[int, Callable[[Exception], bool]] = {}
        self.retry_counts: Dict[int, int] = {}
        self.max_retries: int = config.get('max_step_retries', 3)
        self.guidance_service = UserGuidanceService()
    
    def register_step(self, step_id: int, step_class: Type[WorkflowStep]) -> None:
        """Register a workflow step class."""
        self.registered_steps[step_id] = step_class
    
    def initialize_workflow(self, project_name: str) -> bool:
        """Initialize a new workflow."""
        try:
            self.workflow_state = WorkflowState(
                project_name=project_name,
                current_step=1
            )
            
            # Use the progress store's initialize_workflow method if available
            if hasattr(self.progress_store, 'initialize_workflow'):
                return self.progress_store.initialize_workflow(project_name)
            else:
                # Fallback to save_progress
                return self.progress_store.save_progress(0, StepStatus.PENDING, {
                    'project_name': project_name,
                    'initialized': True
                })
        except Exception as e:
            print(f"Error initializing workflow: {e}")
            return False
    
    def load_existing_workflow(self) -> bool:
        """Load an existing workflow from storage."""
        try:
            self.workflow_state = self.progress_store.load_progress()
            return self.workflow_state is not None
        except Exception as e:
            print(f"Error loading workflow: {e}")
            return False
    
    def execute_step(self, step_id: int) -> StepResult:
        """Execute a specific workflow step."""
        if not self.workflow_state:
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message="Workflow not initialized"
            )
        
        if step_id not in self.registered_steps:
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message=f"Step {step_id} not registered"
            )
        
        try:
            # Create step instance if not exists
            if step_id not in self.step_instances:
                step_class = self.registered_steps[step_id]
                self.step_instances[step_id] = step_class()
            
            step_instance = self.step_instances[step_id]
            
            # Validate prerequisites
            if not step_instance.validate():
                return StepResult(
                    step_id=step_id,
                    status=StepStatus.FAILED,
                    error_message="Step validation failed"
                )
            
            # Execute the step
            result = step_instance.execute()
            
            # Update workflow state if successful
            if result.status == StepStatus.COMPLETED:
                self.workflow_state.mark_step_complete(step_id)
                self.workflow_state.current_step = self.get_next_step_id(step_id)
                
                # Save progress
                self.progress_store.save_progress(
                    step_id, 
                    result.status, 
                    result.result_data
                )
            
            return result
            
        except Exception as e:
            # Get enhanced error guidance
            context = {
                'step_id': step_id,
                'project_name': self.workflow_state.project_name if self.workflow_state else None
            }
            guidance = self.guidance_service.get_error_guidance(str(e), context)
            formatted_guidance = self.guidance_service.format_guidance_message(guidance)
            
            print(f"\n{formatted_guidance}")
            
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message=f"Step execution failed: {str(e)}"
            )
    
    def validate_step(self, step_id: int) -> bool:
        """Validate a specific step's completion."""
        if not self.workflow_state:
            return False
        
        return self.workflow_state.is_step_completed(step_id)
    
    def get_next_step_id(self, current_step_id: int) -> int:
        """Determine the next step ID in the workflow."""
        # Simple sequential progression for now
        return current_step_id + 1
    
    def get_current_step(self) -> Optional[int]:
        """Get the current step ID."""
        if not self.workflow_state:
            return None
        return self.workflow_state.current_step
    
    def rollback_step(self, step_id: int) -> bool:
        """Rollback a specific step."""
        if step_id not in self.step_instances:
            return False
        
        try:
            step_instance = self.step_instances[step_id]
            success = step_instance.rollback()
            
            if success and self.workflow_state:
                # Remove from completed steps
                if step_id in self.workflow_state.completed_steps:
                    self.workflow_state.completed_steps.remove(step_id)
                
                # Update current step
                self.workflow_state.current_step = step_id
                self.workflow_state.update_timestamp()
            
            return success
            
        except Exception as e:
            print(f"Error rolling back step {step_id}: {e}")
            return False
    
    def get_workflow_summary(self) -> Dict[str, any]:
        """Get a summary of the current workflow state."""
        if not self.workflow_state:
            return {'status': 'not_initialized'}
        
        total_steps = len(self.registered_steps)
        completed_steps = len(self.workflow_state.completed_steps)
        
        return {
            'project_name': self.workflow_state.project_name,
            'current_step': self.workflow_state.current_step,
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'progress_percentage': self.workflow_state.get_progress_percentage(total_steps),
            'github_repo': self.workflow_state.github_repo,
            'submission_link': self.workflow_state.submission_link,
            'created_at': self.workflow_state.created_at.isoformat(),
            'updated_at': self.workflow_state.updated_at.isoformat()
        }
    
    def register_step_dependencies(self, step_id: int, dependencies: List[int]) -> None:
        """Register dependencies for a workflow step."""
        self.step_dependencies[step_id] = dependencies
    
    def register_step_validator(self, step_id: int, validator: Callable[[], bool]) -> None:
        """Register a custom validator for a workflow step."""
        self.step_validators[step_id] = validator
    
    def register_error_handler(self, step_id: int, handler: Callable[[Exception], bool]) -> None:
        """Register a custom error handler for a workflow step."""
        self.error_handlers[step_id] = handler
    
    def validate_step_dependencies(self, step_id: int) -> bool:
        """Validate that all dependencies for a step are completed."""
        if step_id not in self.step_dependencies:
            return True  # No dependencies
        
        if not self.workflow_state:
            return False
        
        dependencies = self.step_dependencies[step_id]
        for dep_id in dependencies:
            if not self.workflow_state.is_step_completed(dep_id):
                return False
        
        return True
    
    def validate_step_prerequisites(self, step_id: int) -> bool:
        """Comprehensive step prerequisite validation."""
        # Check dependencies
        if not self.validate_step_dependencies(step_id):
            return False
        
        # Check custom validator if exists
        if step_id in self.step_validators:
            try:
                return self.step_validators[step_id]()
            except Exception as e:
                print(f"Custom validator failed for step {step_id}: {e}")
                return False
        
        # Check step instance validation
        if step_id in self.step_instances:
            try:
                return self.step_instances[step_id].validate()
            except Exception as e:
                print(f"Step instance validation failed for step {step_id}: {e}")
                return False
        
        return True
    
    def execute_step_with_retry(self, step_id: int) -> StepResult:
        """Execute a step with retry logic and error handling."""
        if not self.workflow_state:
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message="Workflow not initialized"
            )
        
        if step_id not in self.registered_steps:
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message=f"Step {step_id} not registered"
            )
        
        # Initialize retry count
        if step_id not in self.retry_counts:
            self.retry_counts[step_id] = 0
        
        max_attempts = self.max_retries + 1
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                # Mark step as in progress
                self.progress_store.save_progress(
                    step_id, 
                    StepStatus.IN_PROGRESS, 
                    {'attempt': attempt + 1, 'max_attempts': max_attempts}
                )
                
                # Validate prerequisites
                if not self.validate_step_prerequisites(step_id):
                    return StepResult(
                        step_id=step_id,
                        status=StepStatus.FAILED,
                        error_message="Step prerequisites not met"
                    )
                
                # Create step instance if not exists
                if step_id not in self.step_instances:
                    step_class = self.registered_steps[step_id]
                    self.step_instances[step_id] = step_class()
                
                step_instance = self.step_instances[step_id]
                
                # Execute the step
                result = step_instance.execute()
                
                # Handle successful execution
                if result.status == StepStatus.COMPLETED:
                    self.workflow_state.mark_step_complete(step_id)
                    self.workflow_state.current_step = self.get_next_step_id(step_id)
                    
                    # Save progress
                    self.progress_store.save_progress(
                        step_id, 
                        result.status, 
                        result.result_data
                    )
                    
                    # Reset retry count on success
                    self.retry_counts[step_id] = 0
                    
                    return result
                
                # Handle failed execution
                elif result.status == StepStatus.FAILED:
                    last_error = Exception(result.error_message or "Step execution failed")
                    
                    # Try custom error handler
                    if step_id in self.error_handlers:
                        try:
                            if self.error_handlers[step_id](last_error):
                                # Error handler resolved the issue, retry
                                continue
                        except Exception as handler_error:
                            print(f"Error handler failed for step {step_id}: {handler_error}")
                    
                    # If not the last attempt, continue to retry
                    if attempt < max_attempts - 1:
                        self.retry_counts[step_id] += 1
                        print(f"Step {step_id} failed, retrying... (attempt {attempt + 2}/{max_attempts})")
                        continue
                    
                    # Final failure
                    self.progress_store.save_progress(
                        step_id, 
                        StepStatus.FAILED, 
                        result.result_data,
                        result.error_message
                    )
                    
                    return result
                
            except Exception as e:
                last_error = e
                
                # Try custom error handler
                if step_id in self.error_handlers:
                    try:
                        if self.error_handlers[step_id](e):
                            # Error handler resolved the issue, retry
                            continue
                    except Exception as handler_error:
                        print(f"Error handler failed for step {step_id}: {handler_error}")
                
                # If not the last attempt, continue to retry
                if attempt < max_attempts - 1:
                    self.retry_counts[step_id] += 1
                    print(f"Step {step_id} failed with exception, retrying... (attempt {attempt + 2}/{max_attempts})")
                    continue
        
        # All retries exhausted
        error_message = f"Step execution failed after {max_attempts} attempts: {str(last_error)}"
        
        self.progress_store.save_progress(
            step_id, 
            StepStatus.FAILED, 
            {'retry_count': self.retry_counts[step_id]},
            error_message
        )
        
        return StepResult(
            step_id=step_id,
            status=StepStatus.FAILED,
            error_message=error_message
        )
    
    def get_next_available_step(self) -> Optional[int]:
        """Get the next step that can be executed based on dependencies."""
        if not self.workflow_state:
            return None
        
        # Start from current step and find next available
        for step_id in sorted(self.registered_steps.keys()):
            # Skip completed steps
            if self.workflow_state.is_step_completed(step_id):
                continue
            
            # Check if dependencies are met
            if self.validate_step_dependencies(step_id):
                return step_id
        
        return None
    
    def can_execute_step(self, step_id: int) -> bool:
        """Check if a step can be executed."""
        if not self.workflow_state:
            return False
        
        # Step already completed
        if self.workflow_state.is_step_completed(step_id):
            return False
        
        # Step not registered
        if step_id not in self.registered_steps:
            return False
        
        # Dependencies not met
        if not self.validate_step_dependencies(step_id):
            return False
        
        return True
    
    def get_step_status(self, step_id: int) -> StepStatus:
        """Get the current status of a step."""
        if not self.workflow_state:
            return StepStatus.PENDING
        
        if self.workflow_state.is_step_completed(step_id):
            return StepStatus.COMPLETED
        
        # Check if step is currently being executed
        step_result = self.progress_store.get_step_result(step_id)
        if step_result:
            return step_result.status
        
        # Check if step can be executed
        if self.can_execute_step(step_id):
            return StepStatus.PENDING
        
        return StepStatus.PENDING
    
    def recover_from_failure(self, step_id: int) -> bool:
        """Attempt to recover from a failed step."""
        try:
            # Reset retry count
            self.retry_counts[step_id] = 0
            
            # Try to rollback the step first
            if step_id in self.step_instances:
                step_instance = self.step_instances[step_id]
                try:
                    step_instance.rollback()
                except Exception as e:
                    print(f"Rollback failed for step {step_id}: {e}")
            
            # Remove step instance to force recreation
            if step_id in self.step_instances:
                del self.step_instances[step_id]
            
            # Update workflow state
            if self.workflow_state:
                if step_id in self.workflow_state.completed_steps:
                    self.workflow_state.completed_steps.remove(step_id)
                
                # Reset current step if needed
                if self.workflow_state.current_step > step_id:
                    self.workflow_state.current_step = step_id
                
                self.workflow_state.update_timestamp()
            
            # Clear failed step result
            self.progress_store.rollback_step(step_id)
            
            return True
            
        except Exception as e:
            print(f"Recovery failed for step {step_id}: {e}")
            return False
    
    def get_workflow_health(self) -> Dict[str, Any]:
        """Get overall workflow health and status."""
        if not self.workflow_state:
            return {
                'status': 'not_initialized',
                'health': 'unknown'
            }
        
        total_steps = len(self.registered_steps)
        completed_steps = len(self.workflow_state.completed_steps)
        failed_steps = []
        pending_steps = []
        
        # Check status of all steps
        for step_id in self.registered_steps.keys():
            status = self.get_step_status(step_id)
            if status == StepStatus.FAILED:
                failed_steps.append(step_id)
            elif status == StepStatus.PENDING and self.can_execute_step(step_id):
                pending_steps.append(step_id)
        
        # Determine overall health
        if failed_steps:
            health = 'critical' if len(failed_steps) > 1 else 'warning'
        elif completed_steps == total_steps:
            health = 'excellent'
        elif completed_steps > total_steps * 0.8:
            health = 'good'
        else:
            health = 'fair'
        
        return {
            'status': 'active',
            'health': health,
            'total_steps': total_steps,
            'completed_steps': completed_steps,
            'failed_steps': failed_steps,
            'pending_steps': pending_steps,
            'progress_percentage': self.workflow_state.get_progress_percentage(total_steps),
            'next_available_step': self.get_next_available_step(),
            'last_updated': self.workflow_state.updated_at.isoformat()
        }
    
    def get_step_guidance(self, step_id: int, error_message: Optional[str] = None) -> str:
        """Get user guidance for a specific step or error."""
        context = {
            'step_id': step_id,
            'project_name': self.workflow_state.project_name if self.workflow_state else None
        }
        
        if error_message:
            guidance = self.guidance_service.get_error_guidance(error_message, context)
        else:
            # Provide general step guidance
            step_guidance_messages = {
                1: "Setting up project environment and downloading required files",
                2: "Processing and validating dataset files", 
                3: "Creating and populating Jupyter notebook",
                4: "Creating GitHub repository and uploading files",
                5: "Preparing and submitting to LMS portal"
            }
            
            message = step_guidance_messages.get(step_id, f"Executing step {step_id}")
            guidance = self.guidance_service.get_error_guidance(message, context)
        
        return self.guidance_service.format_guidance_message(guidance)
    
    def get_workflow_help(self, topic: str) -> Optional[str]:
        """Get help information for workflow topics."""
        help_info = self.guidance_service.get_help_for_topic(topic)
        if help_info:
            formatted = f"📖 {help_info['title']}\n"
            formatted += f"{help_info['description']}\n\n"
            
            for section in help_info.get('sections', []):
                formatted += f"## {section['title']}\n"
                if isinstance(section['content'], list):
                    for item in section['content']:
                        formatted += f"  • {item}\n"
                else:
                    formatted += f"  {section['content']}\n"
                formatted += "\n"
            
            return formatted
        
        return None