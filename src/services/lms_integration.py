"""
LMS integration helpers for AICTE project workflow.
"""
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urlparse
from dataclasses import dataclass, field

from ..models.workflow_models import WorkflowState, ProjectData
from .submission_service import SubmissionStatus, SubmissionValidationService


@dataclass
class LMSSubmissionData:
    """Data structure for LMS submission."""
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    project_title: str = ""
    project_description: str = ""
    repository_url: str = ""
    submission_date: datetime = field(default_factory=datetime.now)
    completion_status: str = "incomplete"
    grade_percentage: Optional[float] = None
    submission_notes: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)


@dataclass
class LMSSubmissionSummary:
    """Comprehensive submission summary for LMS."""
    submission_data: LMSSubmissionData
    project_statistics: Dict[str, Any] = field(default_factory=dict)
    checklist_summary: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    submission_readiness: Dict[str, Any] = field(default_factory=dict)
    formatted_content: Dict[str, str] = field(default_factory=dict)


class LMSIntegrationService:
    """Service for LMS integration and submission helpers."""
    
    def __init__(self, submission_service: SubmissionValidationService, config: Optional[Dict[str, Any]] = None):
        """Initialize LMS integration service."""
        self.submission_service = submission_service
        self.config = config or {}
        
        # LMS-specific configuration
        self.lms_config = self.config.get('lms', {})
        self.submission_format = self.lms_config.get('submission_format', 'standard')
        self.required_fields = self.lms_config.get('required_fields', [
            'student_name', 'project_title', 'repository_url'
        ])
        
        # Repository URL patterns for validation
        self.valid_repo_patterns = [
            r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$',
            r'^https://gitlab\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$',
            r'^https://bitbucket\.org/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$'
        ]
    
    def generate_submission_summary(self, workflow_state: WorkflowState, 
                                  submission_status: SubmissionStatus,
                                  student_info: Optional[Dict[str, str]] = None) -> LMSSubmissionSummary:
        """Generate comprehensive submission summary for LMS."""
        try:
            # Create submission data
            submission_data = self._create_submission_data(workflow_state, submission_status, student_info)
            
            # Generate project statistics
            project_stats = self._generate_project_statistics(workflow_state, submission_status)
            
            # Create checklist summary
            checklist_summary = self._create_checklist_summary(submission_status)
            
            # Generate validation results
            validation_results = self._generate_validation_results(submission_status)
            
            # Assess submission readiness
            readiness_assessment = self._assess_submission_readiness(submission_status)
            
            # Format content for different LMS systems
            formatted_content = self._format_submission_content(submission_data, project_stats, checklist_summary)
            
            return LMSSubmissionSummary(
                submission_data=submission_data,
                project_statistics=project_stats,
                checklist_summary=checklist_summary,
                validation_results=validation_results,
                submission_readiness=readiness_assessment,
                formatted_content=formatted_content
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate submission summary: {e}")
    
    def validate_repository_link(self, repository_url: str) -> Tuple[bool, List[str]]:
        """Validate and format repository link for LMS submission."""
        errors = []
        
        try:
            # Basic URL validation
            if not repository_url or not isinstance(repository_url, str):
                errors.append("Repository URL is required and must be a string")
                return False, errors
            
            # Remove trailing whitespace and normalize
            repository_url = repository_url.strip()
            
            # Check URL format
            parsed_url = urlparse(repository_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                errors.append("Repository URL must be a valid URL with scheme (http/https)")
                return False, errors
            
            # Convert HTTP to HTTPS for validation
            test_url = repository_url
            if test_url.startswith('http://'):
                test_url = test_url.replace('http://', 'https://', 1)
            
            # Check against valid patterns
            is_valid_pattern = False
            for pattern in self.valid_repo_patterns:
                if re.match(pattern, test_url):
                    is_valid_pattern = True
                    break
            
            if not is_valid_pattern:
                errors.append("Repository URL must be from a supported platform (GitHub, GitLab, or Bitbucket)")
                return False, errors
            
            # Check for common issues
            if '/tree/' in repository_url or '/blob/' in repository_url:
                errors.append("Repository URL should point to the main repository, not a specific file or branch")
                return False, errors
            
            if repository_url.endswith('.git'):
                errors.append("Repository URL should be the web URL, not the git clone URL")
                return False, errors
            
            # Additional GitHub-specific validations
            if 'github.com' in test_url:
                github_errors = self._validate_github_specific(test_url)
                errors.extend(github_errors)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Error validating repository URL: {e}")
            return False, errors
    
    def format_repository_link(self, repository_url: str) -> str:
        """Format repository link for consistent LMS submission."""
        try:
            # Validate first
            is_valid, errors = self.validate_repository_link(repository_url)
            if not is_valid:
                raise ValueError(f"Invalid repository URL: {'; '.join(errors)}")
            
            # Normalize URL
            repository_url = repository_url.strip().rstrip('/')
            
            # Ensure HTTPS
            if repository_url.startswith('http://'):
                repository_url = repository_url.replace('http://', 'https://', 1)
            
            return repository_url
            
        except Exception as e:
            raise ValueError(f"Failed to format repository link: {e}")
    
    def track_submission_status(self, workflow_state: WorkflowState, 
                              submission_status: SubmissionStatus) -> Dict[str, Any]:
        """Track and return submission status for LMS integration."""
        try:
            # Calculate completion metrics
            total_items = len(submission_status.checklist_items)
            completed_items = sum(1 for item in submission_status.checklist_items if item.is_completed)
            required_items = sum(1 for item in submission_status.checklist_items if item.is_required)
            completed_required = sum(1 for item in submission_status.checklist_items 
                                   if item.is_required and item.is_completed)
            
            # Determine submission phase
            submission_phase = self._determine_submission_phase(submission_status)
            
            # Calculate grade estimation (if applicable)
            grade_estimation = self._estimate_grade(submission_status)
            
            # Generate status tracking data
            status_tracking = {
                'project_name': workflow_state.project_name,
                'student_progress': {
                    'total_items': total_items,
                    'completed_items': completed_items,
                    'required_items': required_items,
                    'completed_required': completed_required,
                    'completion_percentage': (completed_items / total_items * 100) if total_items > 0 else 0,
                    'required_completion_percentage': (completed_required / required_items * 100) if required_items > 0 else 0
                },
                'submission_phase': submission_phase,
                'readiness_status': {
                    'is_ready': submission_status.is_ready_for_submission,
                    'blocking_issues': len(submission_status.submission_errors),
                    'warnings': len(submission_status.submission_warnings),
                    'last_validated': submission_status.last_validated.isoformat() if submission_status.last_validated else None
                },
                'deadline_tracking': {
                    'deadline': submission_status.deadline.isoformat() if submission_status.deadline else None,
                    'days_remaining': submission_status.days_until_deadline,
                    'is_overdue': submission_status.days_until_deadline is not None and submission_status.days_until_deadline < 0,
                    'urgency_level': self._calculate_urgency_level(submission_status)
                },
                'repository_info': {
                    'github_repo': workflow_state.github_repo,
                    'submission_link': workflow_state.submission_link,
                    'link_validated': workflow_state.submission_link is not None
                },
                'grade_estimation': grade_estimation,
                'last_updated': datetime.now().isoformat()
            }
            
            return status_tracking
            
        except Exception as e:
            raise ValueError(f"Failed to track submission status: {e}")
    
    def generate_lms_report(self, workflow_state: WorkflowState, 
                           submission_status: SubmissionStatus,
                           format_type: str = 'html') -> str:
        """Generate formatted report for LMS submission."""
        try:
            # Generate submission summary
            summary = self.generate_submission_summary(workflow_state, submission_status)
            
            if format_type.lower() == 'html':
                return self._generate_html_report(summary)
            elif format_type.lower() == 'markdown':
                return self._generate_markdown_report(summary)
            elif format_type.lower() == 'json':
                return self._generate_json_report(summary)
            elif format_type.lower() == 'text':
                return self._generate_text_report(summary)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
                
        except Exception as e:
            raise ValueError(f"Failed to generate LMS report: {e}")
    
    def prepare_submission_package(self, workflow_state: WorkflowState,
                                 submission_status: SubmissionStatus,
                                 output_format: str = 'json') -> Dict[str, Any]:
        """Prepare complete submission package for LMS."""
        try:
            # Generate all components
            summary = self.generate_submission_summary(workflow_state, submission_status)
            status_tracking = self.track_submission_status(workflow_state, submission_status)
            
            # Validate repository link
            repo_valid, repo_errors = self.validate_repository_link(workflow_state.submission_link or "")
            
            # Create submission package
            submission_package = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'format_version': '1.0',
                    'generator': 'AICTE Workflow Automation',
                    'submission_id': f"{workflow_state.project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                },
                'submission_summary': {
                    'project_title': summary.submission_data.project_title,
                    'project_description': summary.submission_data.project_description,
                    'repository_url': summary.submission_data.repository_url,
                    'submission_date': summary.submission_data.submission_date.isoformat(),
                    'completion_status': summary.submission_data.completion_status
                },
                'progress_tracking': status_tracking,
                'validation_results': {
                    'repository_validation': {
                        'is_valid': repo_valid,
                        'errors': repo_errors
                    },
                    'checklist_validation': summary.validation_results,
                    'readiness_assessment': summary.submission_readiness
                },
                'formatted_reports': {
                    'html': self.generate_lms_report(workflow_state, submission_status, 'html'),
                    'markdown': self.generate_lms_report(workflow_state, submission_status, 'markdown'),
                    'text': self.generate_lms_report(workflow_state, submission_status, 'text')
                }
            }
            
            return submission_package
            
        except Exception as e:
            raise ValueError(f"Failed to prepare submission package: {e}")
    
    # Private helper methods
    
    def _create_submission_data(self, workflow_state: WorkflowState, 
                              submission_status: SubmissionStatus,
                              student_info: Optional[Dict[str, str]] = None) -> LMSSubmissionData:
        """Create LMS submission data structure."""
        student_info = student_info or {}
        
        return LMSSubmissionData(
            student_name=student_info.get('name'),
            student_id=student_info.get('id'),
            project_title=workflow_state.project_name,
            project_description=workflow_state.project_data.project_description if workflow_state.project_data else "",
            repository_url=workflow_state.submission_link or "",
            submission_date=datetime.now(),
            completion_status="complete" if submission_status.is_ready_for_submission else "incomplete",
            grade_percentage=self._estimate_grade(submission_status),
            submission_notes=submission_status.submission_warnings + submission_status.submission_errors,
            attachments=[workflow_state.submission_link] if workflow_state.submission_link else []
        )
    
    def _generate_project_statistics(self, workflow_state: WorkflowState, 
                                   submission_status: SubmissionStatus) -> Dict[str, Any]:
        """Generate project statistics."""
        return {
            'project_name': workflow_state.project_name,
            'created_at': workflow_state.created_at.isoformat(),
            'last_updated': workflow_state.updated_at.isoformat(),
            'total_steps': len(workflow_state.completed_steps) + 1,  # +1 for current step
            'completed_steps': len(workflow_state.completed_steps),
            'current_step': workflow_state.current_step,
            'overall_completion': submission_status.overall_completion,
            'github_repository': workflow_state.github_repo,
            'has_deadline': submission_status.deadline is not None,
            'deadline_status': 'on_time' if submission_status.days_until_deadline and submission_status.days_until_deadline > 0 else 'overdue'
        }
    
    def _create_checklist_summary(self, submission_status: SubmissionStatus) -> Dict[str, Any]:
        """Create checklist summary."""
        required_items = [item for item in submission_status.checklist_items if item.is_required]
        optional_items = [item for item in submission_status.checklist_items if not item.is_required]
        
        return {
            'total_items': len(submission_status.checklist_items),
            'required_items': len(required_items),
            'optional_items': len(optional_items),
            'completed_required': sum(1 for item in required_items if item.is_completed),
            'completed_optional': sum(1 for item in optional_items if item.is_completed),
            'completion_details': [
                {
                    'item_id': item.item_id,
                    'description': item.description,
                    'is_required': item.is_required,
                    'is_completed': item.is_completed,
                    'validation_message': item.validation_message,
                    'last_checked': item.last_checked.isoformat() if item.last_checked else None
                }
                for item in submission_status.checklist_items
            ]
        }
    
    def _generate_validation_results(self, submission_status: SubmissionStatus) -> Dict[str, Any]:
        """Generate validation results summary."""
        return {
            'overall_valid': submission_status.is_ready_for_submission,
            'validation_timestamp': submission_status.last_validated.isoformat() if submission_status.last_validated else None,
            'error_count': len(submission_status.submission_errors),
            'warning_count': len(submission_status.submission_warnings),
            'errors': submission_status.submission_errors,
            'warnings': submission_status.submission_warnings,
            'completion_percentage': submission_status.overall_completion
        }
    
    def _assess_submission_readiness(self, submission_status: SubmissionStatus) -> Dict[str, Any]:
        """Assess submission readiness."""
        required_complete = all(item.is_completed for item in submission_status.checklist_items if item.is_required)
        has_critical_errors = any('critical' in error.lower() for error in submission_status.submission_errors)
        deadline_ok = submission_status.days_until_deadline is None or submission_status.days_until_deadline >= 0
        
        return {
            'is_ready': submission_status.is_ready_for_submission,
            'required_items_complete': required_complete,
            'has_critical_errors': has_critical_errors,
            'deadline_status_ok': deadline_ok,
            'readiness_score': self._calculate_readiness_score(submission_status),
            'blocking_factors': self._identify_blocking_factors(submission_status),
            'recommendations': self._generate_recommendations(submission_status)
        }
    
    def _format_submission_content(self, submission_data: LMSSubmissionData,
                                 project_stats: Dict[str, Any],
                                 checklist_summary: Dict[str, Any]) -> Dict[str, str]:
        """Format submission content for different systems."""
        return {
            'title': f"AICTE Project Submission: {submission_data.project_title}",
            'description': submission_data.project_description,
            'summary': f"Project completion: {project_stats['overall_completion']:.1f}% "
                      f"({checklist_summary['completed_required']}/{checklist_summary['required_items']} required items)",
            'repository_link': submission_data.repository_url,
            'submission_notes': '; '.join(submission_data.submission_notes) if submission_data.submission_notes else "No additional notes"
        }
    
    def _validate_github_specific(self, repository_url: str) -> List[str]:
        """Perform GitHub-specific validations."""
        errors = []
        
        try:
            # Extract owner and repo from URL
            parts = repository_url.replace('https://github.com/', '').split('/')
            if len(parts) < 2:
                errors.append("GitHub URL should contain both owner and repository name")
                return errors
            
            owner, repo = parts[0], parts[1]
            
            # Validate owner and repo names
            if not re.match(r'^[a-zA-Z0-9_.-]+$', owner):
                errors.append("GitHub owner name contains invalid characters")
            
            if not re.match(r'^[a-zA-Z0-9_.-]+$', repo):
                errors.append("GitHub repository name contains invalid characters")
            
            # Check for common mistakes
            if owner.lower() in ['www', 'http', 'https']:
                errors.append("GitHub owner name appears to be invalid")
            
            if repo.lower() in ['git', 'clone', 'download']:
                errors.append("GitHub repository name appears to be invalid")
                
        except Exception as e:
            errors.append(f"Error validating GitHub URL: {e}")
        
        return errors
    
    def _determine_submission_phase(self, submission_status: SubmissionStatus) -> str:
        """Determine current submission phase."""
        completion = submission_status.overall_completion
        
        if completion < 25:
            return "initialization"
        elif completion < 50:
            return "development"
        elif completion < 75:
            return "integration"
        elif completion < 90:
            return "validation"
        elif completion < 100:
            return "finalization"
        else:
            return "completed"
    
    def _estimate_grade(self, submission_status: SubmissionStatus) -> Optional[float]:
        """Estimate grade based on completion status."""
        try:
            base_score = submission_status.overall_completion
            
            # Deduct points for errors and warnings
            error_penalty = len(submission_status.submission_errors) * 5
            warning_penalty = len(submission_status.submission_warnings) * 2
            
            # Bonus for early submission
            deadline_bonus = 0
            if submission_status.days_until_deadline and submission_status.days_until_deadline > 3:
                deadline_bonus = 5
            
            estimated_grade = max(0, min(100, base_score - error_penalty - warning_penalty + deadline_bonus))
            return round(estimated_grade, 1)
            
        except Exception:
            return None
    
    def _calculate_urgency_level(self, submission_status: SubmissionStatus) -> str:
        """Calculate urgency level based on deadline."""
        if submission_status.days_until_deadline is None:
            return "unknown"
        
        days = submission_status.days_until_deadline
        
        if days < 0:
            return "overdue"
        elif days == 0:
            return "critical"
        elif days <= 1:
            return "urgent"
        elif days <= 3:
            return "high"
        elif days <= 7:
            return "medium"
        else:
            return "low"
    
    def _calculate_readiness_score(self, submission_status: SubmissionStatus) -> float:
        """Calculate readiness score (0-100)."""
        try:
            base_score = submission_status.overall_completion
            
            # Adjust for errors and warnings
            error_impact = len(submission_status.submission_errors) * 10
            warning_impact = len(submission_status.submission_warnings) * 5
            
            # Adjust for deadline pressure
            deadline_impact = 0
            if submission_status.days_until_deadline is not None:
                if submission_status.days_until_deadline < 0:
                    deadline_impact = 20  # Overdue penalty
                elif submission_status.days_until_deadline == 0:
                    deadline_impact = 10  # Same day penalty
            
            readiness_score = max(0, min(100, base_score - error_impact - warning_impact - deadline_impact))
            return round(readiness_score, 1)
            
        except Exception:
            return 0.0
    
    def _identify_blocking_factors(self, submission_status: SubmissionStatus) -> List[str]:
        """Identify factors blocking submission."""
        blocking_factors = []
        
        # Check for incomplete required items
        incomplete_required = [item for item in submission_status.checklist_items 
                             if item.is_required and not item.is_completed]
        if incomplete_required:
            blocking_factors.append(f"Incomplete required items: {len(incomplete_required)}")
        
        # Check for critical errors
        critical_errors = [error for error in submission_status.submission_errors 
                         if 'critical' in error.lower()]
        if critical_errors:
            blocking_factors.append(f"Critical errors: {len(critical_errors)}")
        
        # Check deadline status
        if submission_status.days_until_deadline is not None and submission_status.days_until_deadline < 0:
            blocking_factors.append("Deadline has passed")
        
        return blocking_factors
    
    def _generate_recommendations(self, submission_status: SubmissionStatus) -> List[str]:
        """Generate recommendations for improving submission."""
        recommendations = []
        
        # Check completion status
        if submission_status.overall_completion < 80:
            recommendations.append("Complete remaining checklist items to improve submission quality")
        
        # Check for errors
        if submission_status.submission_errors:
            recommendations.append("Address all validation errors before final submission")
        
        # Check deadline
        if submission_status.days_until_deadline is not None:
            if submission_status.days_until_deadline <= 1:
                recommendations.append("Submit as soon as possible - deadline is approaching")
            elif submission_status.days_until_deadline <= 3:
                recommendations.append("Plan to complete submission within the next 2 days")
        
        # Check warnings
        if len(submission_status.submission_warnings) > 3:
            recommendations.append("Review and address submission warnings to improve quality")
        
        return recommendations
    
    def _generate_html_report(self, summary: LMSSubmissionSummary) -> str:
        """Generate HTML formatted report."""
        html = f"""
        <html>
        <head>
            <title>AICTE Project Submission Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .checklist {{ list-style-type: none; }}
                .completed {{ color: green; }}
                .incomplete {{ color: red; }}
                .warning {{ color: orange; }}
                .error {{ color: red; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>AICTE Project Submission Report</h1>
                <p><strong>Project:</strong> {summary.submission_data.project_title}</p>
                <p><strong>Repository:</strong> <a href="{summary.submission_data.repository_url}">{summary.submission_data.repository_url}</a></p>
                <p><strong>Completion:</strong> {summary.project_statistics.get('overall_completion', 0):.1f}%</p>
            </div>
            
            <div class="section">
                <h2>Project Statistics</h2>
                <ul>
                    <li>Total Steps: {summary.project_statistics.get('total_steps', 0)}</li>
                    <li>Completed Steps: {summary.project_statistics.get('completed_steps', 0)}</li>
                    <li>Current Step: {summary.project_statistics.get('current_step', 0)}</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Submission Status</h2>
                <p class="{'completed' if summary.submission_data.completion_status == 'complete' else 'incomplete'}">
                    Status: {summary.submission_data.completion_status.title()}
                </p>
            </div>
        </body>
        </html>
        """
        return html.strip()
    
    def _generate_markdown_report(self, summary: LMSSubmissionSummary) -> str:
        """Generate Markdown formatted report."""
        markdown = f"""# AICTE Project Submission Report

## Project Information
- **Project Title:** {summary.submission_data.project_title}
- **Repository URL:** {summary.submission_data.repository_url}
- **Submission Date:** {summary.submission_data.submission_date.strftime('%Y-%m-%d %H:%M:%S')}
- **Completion Status:** {summary.submission_data.completion_status.title()}

## Progress Summary
- **Overall Completion:** {summary.project_statistics.get('overall_completion', 0):.1f}%
- **Total Steps:** {summary.project_statistics.get('total_steps', 0)}
- **Completed Steps:** {summary.project_statistics.get('completed_steps', 0)}
- **Current Step:** {summary.project_statistics.get('current_step', 0)}

## Checklist Status
- **Required Items:** {summary.checklist_summary.get('completed_required', 0)}/{summary.checklist_summary.get('required_items', 0)}
- **Optional Items:** {summary.checklist_summary.get('completed_optional', 0)}/{summary.checklist_summary.get('optional_items', 0)}

## Validation Results
- **Ready for Submission:** {'Yes' if summary.validation_results.get('overall_valid', False) else 'No'}
- **Errors:** {summary.validation_results.get('error_count', 0)}
- **Warnings:** {summary.validation_results.get('warning_count', 0)}
"""
        return markdown.strip()
    
    def _generate_json_report(self, summary: LMSSubmissionSummary) -> str:
        """Generate JSON formatted report."""
        report_data = {
            'submission_data': {
                'project_title': summary.submission_data.project_title,
                'repository_url': summary.submission_data.repository_url,
                'submission_date': summary.submission_data.submission_date.isoformat(),
                'completion_status': summary.submission_data.completion_status
            },
            'project_statistics': summary.project_statistics,
            'checklist_summary': summary.checklist_summary,
            'validation_results': summary.validation_results,
            'submission_readiness': summary.submission_readiness
        }
        return json.dumps(report_data, indent=2)
    
    def _generate_text_report(self, summary: LMSSubmissionSummary) -> str:
        """Generate plain text formatted report."""
        text = f"""AICTE PROJECT SUBMISSION REPORT
{'=' * 40}

Project Title: {summary.submission_data.project_title}
Repository URL: {summary.submission_data.repository_url}
Submission Date: {summary.submission_data.submission_date.strftime('%Y-%m-%d %H:%M:%S')}
Completion Status: {summary.submission_data.completion_status.title()}

PROGRESS SUMMARY
{'-' * 20}
Overall Completion: {summary.project_statistics.get('overall_completion', 0):.1f}%
Total Steps: {summary.project_statistics.get('total_steps', 0)}
Completed Steps: {summary.project_statistics.get('completed_steps', 0)}
Current Step: {summary.project_statistics.get('current_step', 0)}

CHECKLIST STATUS
{'-' * 20}
Required Items: {summary.checklist_summary.get('completed_required', 0)}/{summary.checklist_summary.get('required_items', 0)}
Optional Items: {summary.checklist_summary.get('completed_optional', 0)}/{summary.checklist_summary.get('optional_items', 0)}

VALIDATION RESULTS
{'-' * 20}
Ready for Submission: {'Yes' if summary.validation_results.get('overall_valid', False) else 'No'}
Errors: {summary.validation_results.get('error_count', 0)}
Warnings: {summary.validation_results.get('warning_count', 0)}
"""
        return text.strip()