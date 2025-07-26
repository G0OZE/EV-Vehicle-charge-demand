"""
Submission tracking and validation service for AICTE project workflow.
"""
import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field

from ..models.workflow_models import WorkflowState, ProjectData
from ..models.interfaces import StepStatus
from .validation_service import ValidationService


@dataclass
class SubmissionChecklist:
    """Checklist item for submission validation."""
    item_id: str
    description: str
    is_required: bool
    is_completed: bool = False
    validation_message: Optional[str] = None
    last_checked: Optional[datetime] = None


@dataclass
class SubmissionStatus:
    """Overall submission status and tracking."""
    project_name: str
    checklist_items: List[SubmissionChecklist] = field(default_factory=list)
    overall_completion: float = 0.0
    is_ready_for_submission: bool = False
    deadline: Optional[datetime] = None
    days_until_deadline: Optional[int] = None
    submission_warnings: List[str] = field(default_factory=list)
    submission_errors: List[str] = field(default_factory=list)
    last_validated: Optional[datetime] = None


class SubmissionValidationService:
    """Service for validating submission completeness and tracking deadlines."""
    
    def __init__(self, validation_service: ValidationService, config: Optional[Dict[str, Any]] = None):
        """Initialize submission validation service."""
        self.validation_service = validation_service
        self.config = config or {}
        self.reminder_thresholds = self.config.get('reminder_thresholds', [7, 3, 1])  # Days before deadline
        
        # Define standard checklist items based on AICTE requirements
        self.standard_checklist = [
            {
                'item_id': 'project_selection',
                'description': 'Project selected and dataset downloaded',
                'is_required': True
            },
            {
                'item_id': 'notebook_created',
                'description': 'Google Colab notebook created with project title',
                'is_required': True
            },
            {
                'item_id': 'dataset_uploaded',
                'description': 'Dataset uploaded to notebook environment',
                'is_required': True
            },
            {
                'item_id': 'code_implemented',
                'description': 'Code template populated and implemented',
                'is_required': True
            },
            {
                'item_id': 'notebook_executed',
                'description': 'Notebook executed with outputs generated',
                'is_required': True
            },
            {
                'item_id': 'github_repo_created',
                'description': 'GitHub repository created and initialized',
                'is_required': True
            },
            {
                'item_id': 'files_uploaded',
                'description': 'Notebook and dataset uploaded to GitHub',
                'is_required': True
            },
            {
                'item_id': 'readme_completed',
                'description': 'README file completed with project description',
                'is_required': True
            },
            {
                'item_id': 'repository_public',
                'description': 'Repository set to public for submission',
                'is_required': True
            },
            {
                'item_id': 'submission_link_ready',
                'description': 'Repository link ready for LMS submission',
                'is_required': True
            },
            {
                'item_id': 'attendance_marked',
                'description': 'Attendance marked as present',
                'is_required': False  # Optional but recommended
            }
        ]
    
    def create_submission_checklist(self, workflow_state: WorkflowState) -> SubmissionStatus:
        """Create submission checklist based on workflow state."""
        try:
            # Initialize checklist items
            checklist_items = []
            for item_config in self.standard_checklist:
                checklist_item = SubmissionChecklist(
                    item_id=item_config['item_id'],
                    description=item_config['description'],
                    is_required=item_config['is_required']
                )
                checklist_items.append(checklist_item)
            
            # Create submission status
            submission_status = SubmissionStatus(
                project_name=workflow_state.project_name,
                checklist_items=checklist_items,
                deadline=workflow_state.project_data.deadline if workflow_state.project_data else None
            )
            
            # Update completion status
            self._update_checklist_completion(submission_status, workflow_state)
            
            return submission_status
            
        except Exception as e:
            raise ValueError(f"Failed to create submission checklist: {e}")
    
    def validate_submission_completeness(self, workflow_state: WorkflowState, repo_path: str = ".") -> SubmissionStatus:
        """Validate submission completeness against requirements."""
        try:
            # Create or update checklist
            submission_status = self.create_submission_checklist(workflow_state)
            
            # Validate each checklist item
            self._validate_project_selection(submission_status, workflow_state)
            self._validate_notebook_creation(submission_status, workflow_state, repo_path)
            self._validate_dataset_upload(submission_status, workflow_state, repo_path)
            self._validate_code_implementation(submission_status, workflow_state, repo_path)
            self._validate_notebook_execution(submission_status, workflow_state, repo_path)
            self._validate_github_repository(submission_status, workflow_state)
            self._validate_file_uploads(submission_status, workflow_state, repo_path)
            self._validate_readme_completion(submission_status, workflow_state, repo_path)
            self._validate_repository_visibility(submission_status, workflow_state)
            self._validate_submission_link(submission_status, workflow_state)
            self._validate_attendance_status(submission_status, workflow_state)
            
            # Calculate overall completion
            self._calculate_overall_completion(submission_status)
            
            # Update validation timestamp
            submission_status.last_validated = datetime.now()
            
            return submission_status
            
        except Exception as e:
            raise ValueError(f"Failed to validate submission completeness: {e}")
    
    def check_deadline_status(self, submission_status: SubmissionStatus) -> Tuple[bool, List[str]]:
        """Check deadline status and generate reminders."""
        warnings = []
        
        try:
            if not submission_status.deadline:
                warnings.append("No deadline set for project")
                return False, warnings
            
            now = datetime.now()
            time_until_deadline = submission_status.deadline - now
            days_until_deadline = time_until_deadline.days
            
            submission_status.days_until_deadline = days_until_deadline
            
            # Check if deadline has passed
            if time_until_deadline.total_seconds() <= 0:
                warnings.append("⚠️ DEADLINE HAS PASSED! Immediate submission required.")
                return False, warnings
            
            # Generate deadline reminders
            if days_until_deadline <= 0:
                hours_remaining = int(time_until_deadline.total_seconds() / 3600)
                if hours_remaining <= 24:
                    warnings.append(f"🚨 URGENT: Only {hours_remaining} hours remaining until deadline!")
                else:
                    warnings.append("🚨 URGENT: Less than 1 day remaining until deadline!")
            elif days_until_deadline in self.reminder_thresholds:
                warnings.append(f"⏰ Reminder: {days_until_deadline} days remaining until deadline")
            
            # Check completion status vs deadline
            if days_until_deadline <= 1 and submission_status.overall_completion < 80:
                warnings.append("⚠️ Project is less than 80% complete with deadline approaching")
            
            return True, warnings
            
        except Exception as e:
            warnings.append(f"Error checking deadline status: {e}")
            return False, warnings
    
    def generate_submission_summary(self, submission_status: SubmissionStatus) -> Dict[str, Any]:
        """Generate comprehensive submission summary."""
        try:
            # Calculate statistics
            total_items = len(submission_status.checklist_items)
            completed_items = sum(1 for item in submission_status.checklist_items if item.is_completed)
            required_items = sum(1 for item in submission_status.checklist_items if item.is_required)
            completed_required = sum(1 for item in submission_status.checklist_items 
                                   if item.is_required and item.is_completed)
            
            # Generate summary
            summary = {
                'project_name': submission_status.project_name,
                'overall_completion': submission_status.overall_completion,
                'is_ready_for_submission': submission_status.is_ready_for_submission,
                'statistics': {
                    'total_items': total_items,
                    'completed_items': completed_items,
                    'required_items': required_items,
                    'completed_required': completed_required,
                    'completion_percentage': (completed_items / total_items * 100) if total_items > 0 else 0,
                    'required_completion_percentage': (completed_required / required_items * 100) if required_items > 0 else 0
                },
                'deadline_info': {
                    'deadline': submission_status.deadline.isoformat() if submission_status.deadline else None,
                    'days_until_deadline': submission_status.days_until_deadline,
                    'is_overdue': submission_status.days_until_deadline is not None and submission_status.days_until_deadline < 0
                },
                'checklist_status': [
                    {
                        'item_id': item.item_id,
                        'description': item.description,
                        'is_required': item.is_required,
                        'is_completed': item.is_completed,
                        'validation_message': item.validation_message,
                        'last_checked': item.last_checked.isoformat() if item.last_checked else None
                    }
                    for item in submission_status.checklist_items
                ],
                'warnings': submission_status.submission_warnings,
                'errors': submission_status.submission_errors,
                'last_validated': submission_status.last_validated.isoformat() if submission_status.last_validated else None
            }
            
            return summary
            
        except Exception as e:
            raise ValueError(f"Failed to generate submission summary: {e}")
    
    def perform_final_validation(self, workflow_state: WorkflowState, repo_path: str = ".") -> Tuple[bool, SubmissionStatus]:
        """Perform final validation before LMS submission."""
        try:
            # Validate submission completeness
            submission_status = self.validate_submission_completeness(workflow_state, repo_path)
            
            # Check deadline status
            deadline_ok, deadline_warnings = self.check_deadline_status(submission_status)
            submission_status.submission_warnings.extend(deadline_warnings)
            
            # Perform additional final checks
            final_errors = []
            
            # Check repository accessibility
            if workflow_state.github_repo and workflow_state.submission_link:
                if not self._validate_repository_accessibility(workflow_state.submission_link):
                    final_errors.append("Repository is not publicly accessible")
            
            # Check file integrity
            if not self._validate_file_integrity(repo_path):
                final_errors.append("Some files may be corrupted or incomplete")
            
            # Check for common submission issues
            common_issues = self._check_common_submission_issues(workflow_state, repo_path)
            final_errors.extend(common_issues)
            
            submission_status.submission_errors.extend(final_errors)
            
            # Determine if ready for submission
            required_items_complete = all(
                item.is_completed for item in submission_status.checklist_items if item.is_required
            )
            no_critical_errors = len([error for error in submission_status.submission_errors 
                                    if 'critical' in error.lower() or 'urgent' in error.lower()]) == 0
            
            submission_status.is_ready_for_submission = (
                required_items_complete and 
                no_critical_errors and 
                deadline_ok
            )
            
            return submission_status.is_ready_for_submission, submission_status
            
        except Exception as e:
            raise ValueError(f"Failed to perform final validation: {e}")
    
    # Private helper methods
    
    def _update_checklist_completion(self, submission_status: SubmissionStatus, workflow_state: WorkflowState):
        """Update checklist completion based on workflow state."""
        # Map workflow steps to checklist items
        step_mapping = {
            1: 'project_selection',
            2: 'notebook_created',
            3: 'dataset_uploaded',
            4: 'code_implemented',
            5: 'notebook_executed',
            6: 'github_repo_created',
            7: 'files_uploaded',
            8: 'readme_completed',
            9: 'repository_public',
            10: 'submission_link_ready'
        }
        
        # Update completion status based on completed steps
        for step_id in workflow_state.completed_steps:
            if step_id in step_mapping:
                item_id = step_mapping[step_id]
                for item in submission_status.checklist_items:
                    if item.item_id == item_id:
                        item.is_completed = True
                        item.last_checked = datetime.now()
                        break
    
    def _validate_project_selection(self, submission_status: SubmissionStatus, workflow_state: WorkflowState):
        """Validate project selection and dataset download."""
        item = self._get_checklist_item(submission_status, 'project_selection')
        if not item:
            return
        
        try:
            if workflow_state.project_data:
                item.is_completed = True
                item.validation_message = f"Project '{workflow_state.project_name}' selected"
            else:
                item.validation_message = "Project data not found"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating project selection: {e}"
    
    def _validate_notebook_creation(self, submission_status: SubmissionStatus, workflow_state: WorkflowState, repo_path: str):
        """Validate notebook creation."""
        item = self._get_checklist_item(submission_status, 'notebook_created')
        if not item:
            return
        
        try:
            notebook_files = list(Path(repo_path).glob('*.ipynb'))
            if notebook_files:
                item.is_completed = True
                item.validation_message = f"Found notebook: {notebook_files[0].name}"
            else:
                item.validation_message = "No notebook file found"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating notebook creation: {e}"
    
    def _validate_dataset_upload(self, submission_status: SubmissionStatus, workflow_state: WorkflowState, repo_path: str):
        """Validate dataset upload."""
        item = self._get_checklist_item(submission_status, 'dataset_uploaded')
        if not item:
            return
        
        try:
            dataset_files = list(Path(repo_path).glob('*.csv'))
            if dataset_files:
                item.is_completed = True
                item.validation_message = f"Found dataset: {dataset_files[0].name}"
            else:
                item.validation_message = "No dataset file found"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating dataset upload: {e}"
    
    def _validate_code_implementation(self, submission_status: SubmissionStatus, workflow_state: WorkflowState, repo_path: str):
        """Validate code implementation."""
        item = self._get_checklist_item(submission_status, 'code_implemented')
        if not item:
            return
        
        try:
            notebook_files = list(Path(repo_path).glob('*.ipynb'))
            if notebook_files:
                # Use validation service to check notebook content
                is_valid = self.validation_service.validate_notebook_content(str(notebook_files[0]))
                if is_valid:
                    item.is_completed = True
                    item.validation_message = "Code implementation validated"
                else:
                    item.validation_message = "Code implementation incomplete or invalid"
            else:
                item.validation_message = "No notebook file found for validation"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating code implementation: {e}"
    
    def _validate_notebook_execution(self, submission_status: SubmissionStatus, workflow_state: WorkflowState, repo_path: str):
        """Validate notebook execution with outputs."""
        item = self._get_checklist_item(submission_status, 'notebook_executed')
        if not item:
            return
        
        try:
            notebook_files = list(Path(repo_path).glob('*.ipynb'))
            if notebook_files:
                # Check if notebook has execution outputs
                with open(notebook_files[0], 'r', encoding='utf-8') as f:
                    notebook_content = json.load(f)
                
                has_outputs = False
                for cell in notebook_content.get('cells', []):
                    if cell.get('cell_type') == 'code' and (cell.get('outputs') or cell.get('execution_count')):
                        has_outputs = True
                        break
                
                if has_outputs:
                    item.is_completed = True
                    item.validation_message = "Notebook has execution outputs"
                else:
                    item.validation_message = "Notebook appears not to be executed"
            else:
                item.validation_message = "No notebook file found"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating notebook execution: {e}"
    
    def _validate_github_repository(self, submission_status: SubmissionStatus, workflow_state: WorkflowState):
        """Validate GitHub repository creation."""
        item = self._get_checklist_item(submission_status, 'github_repo_created')
        if not item:
            return
        
        try:
            if workflow_state.github_repo:
                item.is_completed = True
                item.validation_message = f"Repository: {workflow_state.github_repo}"
            else:
                item.validation_message = "GitHub repository not created"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating GitHub repository: {e}"
    
    def _validate_file_uploads(self, submission_status: SubmissionStatus, workflow_state: WorkflowState, repo_path: str):
        """Validate file uploads to GitHub."""
        item = self._get_checklist_item(submission_status, 'files_uploaded')
        if not item:
            return
        
        try:
            # Check if files exist locally (assuming they would be uploaded)
            notebook_exists = bool(list(Path(repo_path).glob('*.ipynb')))
            dataset_exists = bool(list(Path(repo_path).glob('*.csv')))
            
            if notebook_exists and dataset_exists:
                item.is_completed = True
                item.validation_message = "Notebook and dataset files ready for upload"
            else:
                missing = []
                if not notebook_exists:
                    missing.append("notebook")
                if not dataset_exists:
                    missing.append("dataset")
                item.validation_message = f"Missing files: {', '.join(missing)}"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating file uploads: {e}"
    
    def _validate_readme_completion(self, submission_status: SubmissionStatus, workflow_state: WorkflowState, repo_path: str):
        """Validate README completion."""
        item = self._get_checklist_item(submission_status, 'readme_completed')
        if not item:
            return
        
        try:
            readme_path = Path(repo_path) / 'README.md'
            if readme_path.exists():
                is_valid = self.validation_service._validate_readme_content(readme_path)
                if is_valid:
                    item.is_completed = True
                    item.validation_message = "README file completed"
                else:
                    item.validation_message = "README file incomplete or invalid"
            else:
                item.validation_message = "README file not found"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating README: {e}"
    
    def _validate_repository_visibility(self, submission_status: SubmissionStatus, workflow_state: WorkflowState):
        """Validate repository visibility (public)."""
        item = self._get_checklist_item(submission_status, 'repository_public')
        if not item:
            return
        
        try:
            # This would require GitHub API call to check visibility
            # For now, assume it's set if repository exists
            if workflow_state.github_repo:
                item.is_completed = True
                item.validation_message = "Repository visibility should be verified manually"
            else:
                item.validation_message = "Repository not created yet"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating repository visibility: {e}"
    
    def _validate_submission_link(self, submission_status: SubmissionStatus, workflow_state: WorkflowState):
        """Validate submission link generation."""
        item = self._get_checklist_item(submission_status, 'submission_link_ready')
        if not item:
            return
        
        try:
            if workflow_state.submission_link:
                item.is_completed = True
                item.validation_message = f"Submission link: {workflow_state.submission_link}"
            else:
                item.validation_message = "Submission link not generated"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating submission link: {e}"
    
    def _validate_attendance_status(self, submission_status: SubmissionStatus, workflow_state: WorkflowState):
        """Validate attendance marking (optional)."""
        item = self._get_checklist_item(submission_status, 'attendance_marked')
        if not item:
            return
        
        try:
            # This would require integration with attendance system
            # For now, mark as completed if other items are done
            completed_required = sum(1 for i in submission_status.checklist_items 
                                   if i.is_required and i.is_completed)
            total_required = sum(1 for i in submission_status.checklist_items if i.is_required)
            
            if completed_required >= total_required * 0.8:  # 80% of required items
                item.is_completed = True
                item.validation_message = "Attendance should be marked manually"
            else:
                item.validation_message = "Complete other requirements first"
            
            item.last_checked = datetime.now()
            
        except Exception as e:
            item.validation_message = f"Error validating attendance: {e}"
    
    def _calculate_overall_completion(self, submission_status: SubmissionStatus):
        """Calculate overall completion percentage."""
        try:
            total_items = len(submission_status.checklist_items)
            completed_items = sum(1 for item in submission_status.checklist_items if item.is_completed)
            
            if total_items > 0:
                submission_status.overall_completion = (completed_items / total_items) * 100
            else:
                submission_status.overall_completion = 0.0
                
        except Exception:
            submission_status.overall_completion = 0.0
    
    def _get_checklist_item(self, submission_status: SubmissionStatus, item_id: str) -> Optional[SubmissionChecklist]:
        """Get checklist item by ID."""
        for item in submission_status.checklist_items:
            if item.item_id == item_id:
                return item
        return None
    
    def _validate_repository_accessibility(self, repo_url: str) -> bool:
        """Validate that repository is publicly accessible."""
        try:
            # This would require HTTP request to check accessibility
            # For now, just validate URL format
            from urllib.parse import urlparse
            parsed = urlparse(repo_url)
            return bool(parsed.scheme and parsed.netloc and 'github.com' in parsed.netloc)
        except Exception:
            return False
    
    def _validate_file_integrity(self, repo_path: str) -> bool:
        """Validate file integrity."""
        try:
            # Check that files exist and are not empty
            repo_path = Path(repo_path)
            
            # Check notebook file
            notebook_files = list(repo_path.glob('*.ipynb'))
            if notebook_files:
                notebook_size = notebook_files[0].stat().st_size
                if notebook_size < 100:  # Too small
                    return False
            
            # Check dataset file
            dataset_files = list(repo_path.glob('*.csv'))
            if dataset_files:
                dataset_size = dataset_files[0].stat().st_size
                if dataset_size < 10:  # Too small
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _check_common_submission_issues(self, workflow_state: WorkflowState, repo_path: str) -> List[str]:
        """Check for common submission issues."""
        issues = []
        
        try:
            # Check for placeholder content
            notebook_files = list(Path(repo_path).glob('*.ipynb'))
            if notebook_files:
                with open(notebook_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'TODO' in content or 'FIXME' in content:
                        issues.append("Notebook contains TODO or FIXME placeholders")
            
            # Check for empty README
            readme_path = Path(repo_path) / 'README.md'
            if readme_path.exists():
                readme_size = readme_path.stat().st_size
                if readme_size < 50:
                    issues.append("README file is too short")
            
            # Check project name consistency
            if workflow_state.github_repo and workflow_state.project_name:
                repo_name = workflow_state.github_repo.split('/')[-1]
                if workflow_state.project_name.lower().replace(' ', '-') not in repo_name.lower():
                    issues.append("Repository name doesn't match project name")
            
        except Exception as e:
            issues.append(f"Error checking common issues: {e}")
        
        return issues