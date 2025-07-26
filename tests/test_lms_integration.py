"""
Unit tests for LMS integration service.
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

from src.services.lms_integration import (
    LMSIntegrationService,
    LMSSubmissionData,
    LMSSubmissionSummary
)
from src.services.submission_service import (
    SubmissionValidationService,
    SubmissionStatus,
    SubmissionChecklist
)
from src.models.workflow_models import WorkflowState, ProjectData


class TestLMSSubmissionData(unittest.TestCase):
    """Test LMSSubmissionData data class."""
    
    def test_submission_data_creation(self):
        """Test creating LMS submission data."""
        data = LMSSubmissionData(
            student_name="John Doe",
            student_id="12345",
            project_title="Test Project",
            project_description="Test description",
            repository_url="https://github.com/user/repo"
        )
        
        self.assertEqual(data.student_name, "John Doe")
        self.assertEqual(data.student_id, "12345")
        self.assertEqual(data.project_title, "Test Project")
        self.assertEqual(data.project_description, "Test description")
        self.assertEqual(data.repository_url, "https://github.com/user/repo")
        self.assertEqual(data.completion_status, "incomplete")
        self.assertIsNone(data.grade_percentage)
        self.assertEqual(len(data.submission_notes), 0)
        self.assertEqual(len(data.attachments), 0)


class TestLMSSubmissionSummary(unittest.TestCase):
    """Test LMSSubmissionSummary data class."""
    
    def test_submission_summary_creation(self):
        """Test creating LMS submission summary."""
        submission_data = LMSSubmissionData(project_title="Test Project")
        summary = LMSSubmissionSummary(submission_data=submission_data)
        
        self.assertEqual(summary.submission_data.project_title, "Test Project")
        self.assertEqual(len(summary.project_statistics), 0)
        self.assertEqual(len(summary.checklist_summary), 0)
        self.assertEqual(len(summary.validation_results), 0)
        self.assertEqual(len(summary.submission_readiness), 0)
        self.assertEqual(len(summary.formatted_content), 0)


class TestLMSIntegrationService(unittest.TestCase):
    """Test LMSIntegrationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_submission_service = Mock(spec=SubmissionValidationService)
        self.service = LMSIntegrationService(self.mock_submission_service)
        
        # Create test data
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
            current_step=5,
            completed_steps=[1, 2, 3, 4],
            project_data=self.test_project_data,
            github_repo="testuser/test-project",
            submission_link="https://github.com/testuser/test-project"
        )
        
        self.test_submission_status = SubmissionStatus(
            project_name="Test Project",
            deadline=datetime.now() + timedelta(days=7),
            overall_completion=75.0,
            is_ready_for_submission=False
        )
        
        # Add some checklist items
        self.test_submission_status.checklist_items = [
            SubmissionChecklist("item1", "Required item 1", True, True),
            SubmissionChecklist("item2", "Required item 2", True, False),
            SubmissionChecklist("item3", "Optional item 1", False, True),
        ]
        self.test_submission_status.days_until_deadline = 7
        self.test_submission_status.submission_warnings = ["Warning 1"]
        self.test_submission_status.submission_errors = ["Error 1"]
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsInstance(self.service.submission_service, Mock)
        self.assertEqual(self.service.submission_format, 'standard')
        self.assertEqual(len(self.service.valid_repo_patterns), 3)
        self.assertIn('github\\.com', self.service.valid_repo_patterns[0])
    
    def test_service_initialization_with_config(self):
        """Test service initialization with custom config."""
        config = {
            'lms': {
                'submission_format': 'custom',
                'required_fields': ['student_name', 'project_title']
            }
        }
        service = LMSIntegrationService(self.mock_submission_service, config)
        
        self.assertEqual(service.submission_format, 'custom')
        self.assertEqual(service.required_fields, ['student_name', 'project_title'])
    
    def test_generate_submission_summary(self):
        """Test generating submission summary."""
        student_info = {'name': 'John Doe', 'id': '12345'}
        
        summary = self.service.generate_submission_summary(
            self.test_workflow_state, 
            self.test_submission_status, 
            student_info
        )
        
        self.assertIsInstance(summary, LMSSubmissionSummary)
        self.assertEqual(summary.submission_data.student_name, 'John Doe')
        self.assertEqual(summary.submission_data.student_id, '12345')
        self.assertEqual(summary.submission_data.project_title, 'Test Project')
        self.assertEqual(summary.submission_data.repository_url, 'https://github.com/testuser/test-project')
        
        # Check project statistics
        self.assertIn('project_name', summary.project_statistics)
        self.assertIn('overall_completion', summary.project_statistics)
        
        # Check checklist summary
        self.assertIn('total_items', summary.checklist_summary)
        self.assertIn('required_items', summary.checklist_summary)
        
        # Check validation results
        self.assertIn('overall_valid', summary.validation_results)
        self.assertIn('error_count', summary.validation_results)
    
    def test_validate_repository_link_valid_github(self):
        """Test validating valid GitHub repository link."""
        valid_urls = [
            "https://github.com/user/repo",
            "https://github.com/user-name/repo-name",
            "https://github.com/user123/repo_name",
            "https://github.com/user.name/repo.name"
        ]
        
        for url in valid_urls:
            is_valid, errors = self.service.validate_repository_link(url)
            self.assertTrue(is_valid, f"URL should be valid: {url}, errors: {errors}")
            self.assertEqual(len(errors), 0)
    
    def test_validate_repository_link_valid_gitlab(self):
        """Test validating valid GitLab repository link."""
        valid_url = "https://gitlab.com/user/repo"
        is_valid, errors = self.service.validate_repository_link(valid_url)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_repository_link_valid_bitbucket(self):
        """Test validating valid Bitbucket repository link."""
        valid_url = "https://bitbucket.org/user/repo"
        is_valid, errors = self.service.validate_repository_link(valid_url)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_repository_link_invalid_urls(self):
        """Test validating invalid repository links."""
        invalid_urls = [
            "",  # Empty
            "not-a-url",  # Not a URL
            "https://github.com/user/repo/tree/main",  # Specific branch
            "https://github.com/user/repo/blob/main/file.py",  # Specific file
            "https://github.com/user/repo.git",  # Git URL
            "https://example.com/user/repo",  # Unsupported platform
            "https://github.com/",  # Incomplete
            "https://github.com/user",  # Missing repo
        ]
        
        for url in invalid_urls:
            is_valid, errors = self.service.validate_repository_link(url)
            self.assertFalse(is_valid, f"URL should be invalid: {url}")
            self.assertGreater(len(errors), 0, f"Should have errors for: {url}")
    
    def test_validate_repository_link_http_conversion(self):
        """Test that HTTP URLs are converted to HTTPS and validated."""
        http_url = "http://github.com/user/repo"
        is_valid, errors = self.service.validate_repository_link(http_url)
        
        self.assertTrue(is_valid, f"HTTP URL should be valid after conversion: {http_url}")
        self.assertEqual(len(errors), 0, f"Should have no errors for converted HTTP URL: {http_url}")
    
    def test_validate_repository_link_none_input(self):
        """Test validating None input."""
        is_valid, errors = self.service.validate_repository_link(None)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn("required", errors[0].lower())
    
    def test_format_repository_link(self):
        """Test formatting repository link."""
        # Test normal case
        formatted = self.service.format_repository_link("https://github.com/user/repo")
        self.assertEqual(formatted, "https://github.com/user/repo")
        
        # Test with trailing slash
        formatted = self.service.format_repository_link("https://github.com/user/repo/")
        self.assertEqual(formatted, "https://github.com/user/repo")
        
        # Test with whitespace
        formatted = self.service.format_repository_link("  https://github.com/user/repo  ")
        self.assertEqual(formatted, "https://github.com/user/repo")
    
    def test_format_repository_link_http_to_https(self):
        """Test converting HTTP to HTTPS."""
        formatted = self.service.format_repository_link("http://github.com/user/repo")
        self.assertEqual(formatted, "https://github.com/user/repo")
    
    def test_format_repository_link_invalid(self):
        """Test formatting invalid repository link."""
        with self.assertRaises(ValueError):
            self.service.format_repository_link("invalid-url")
    
    def test_track_submission_status(self):
        """Test tracking submission status."""
        status_tracking = self.service.track_submission_status(
            self.test_workflow_state, 
            self.test_submission_status
        )
        
        self.assertEqual(status_tracking['project_name'], 'Test Project')
        
        # Check student progress
        progress = status_tracking['student_progress']
        self.assertEqual(progress['total_items'], 3)
        self.assertEqual(progress['completed_items'], 2)
        self.assertEqual(progress['required_items'], 2)
        self.assertEqual(progress['completed_required'], 1)
        
        # Check readiness status
        readiness = status_tracking['readiness_status']
        self.assertFalse(readiness['is_ready'])
        self.assertEqual(readiness['blocking_issues'], 1)  # 1 error
        self.assertEqual(readiness['warnings'], 1)  # 1 warning
        
        # Check deadline tracking
        deadline = status_tracking['deadline_tracking']
        self.assertEqual(deadline['days_remaining'], 7)
        self.assertFalse(deadline['is_overdue'])
        self.assertEqual(deadline['urgency_level'], 'medium')
        
        # Check repository info
        repo_info = status_tracking['repository_info']
        self.assertEqual(repo_info['github_repo'], 'testuser/test-project')
        self.assertEqual(repo_info['submission_link'], 'https://github.com/testuser/test-project')
        self.assertTrue(repo_info['link_validated'])
    
    def test_generate_lms_report_html(self):
        """Test generating HTML report."""
        report = self.service.generate_lms_report(
            self.test_workflow_state, 
            self.test_submission_status, 
            'html'
        )
        
        self.assertIn('<html>', report)
        self.assertIn('Test Project', report)
        self.assertIn('github.com/testuser/test-project', report)
        self.assertIn('75.0%', report)
    
    def test_generate_lms_report_markdown(self):
        """Test generating Markdown report."""
        report = self.service.generate_lms_report(
            self.test_workflow_state, 
            self.test_submission_status, 
            'markdown'
        )
        
        self.assertIn('# AICTE Project Submission Report', report)
        self.assertIn('Test Project', report)
        self.assertIn('github.com/testuser/test-project', report)
        self.assertIn('75.0%', report)
    
    def test_generate_lms_report_json(self):
        """Test generating JSON report."""
        report = self.service.generate_lms_report(
            self.test_workflow_state, 
            self.test_submission_status, 
            'json'
        )
        
        # Should be valid JSON
        data = json.loads(report)
        self.assertIn('submission_data', data)
        self.assertIn('project_statistics', data)
        self.assertEqual(data['submission_data']['project_title'], 'Test Project')
    
    def test_generate_lms_report_text(self):
        """Test generating text report."""
        report = self.service.generate_lms_report(
            self.test_workflow_state, 
            self.test_submission_status, 
            'text'
        )
        
        self.assertIn('AICTE PROJECT SUBMISSION REPORT', report)
        self.assertIn('Test Project', report)
        self.assertIn('github.com/testuser/test-project', report)
        self.assertIn('75.0%', report)
    
    def test_generate_lms_report_invalid_format(self):
        """Test generating report with invalid format."""
        with self.assertRaises(ValueError):
            self.service.generate_lms_report(
                self.test_workflow_state, 
                self.test_submission_status, 
                'invalid_format'
            )
    
    def test_prepare_submission_package(self):
        """Test preparing submission package."""
        package = self.service.prepare_submission_package(
            self.test_workflow_state, 
            self.test_submission_status
        )
        
        # Check metadata
        self.assertIn('metadata', package)
        self.assertIn('generated_at', package['metadata'])
        self.assertIn('submission_id', package['metadata'])
        
        # Check submission summary
        self.assertIn('submission_summary', package)
        summary = package['submission_summary']
        self.assertEqual(summary['project_title'], 'Test Project')
        
        # Check progress tracking
        self.assertIn('progress_tracking', package)
        
        # Check validation results
        self.assertIn('validation_results', package)
        validation = package['validation_results']
        self.assertIn('repository_validation', validation)
        self.assertIn('checklist_validation', validation)
        
        # Check formatted reports
        self.assertIn('formatted_reports', package)
        reports = package['formatted_reports']
        self.assertIn('html', reports)
        self.assertIn('markdown', reports)
        self.assertIn('text', reports)
    
    def test_create_submission_data(self):
        """Test creating submission data."""
        student_info = {'name': 'Jane Doe', 'id': '67890'}
        
        submission_data = self.service._create_submission_data(
            self.test_workflow_state, 
            self.test_submission_status, 
            student_info
        )
        
        self.assertEqual(submission_data.student_name, 'Jane Doe')
        self.assertEqual(submission_data.student_id, '67890')
        self.assertEqual(submission_data.project_title, 'Test Project')
        self.assertEqual(submission_data.repository_url, 'https://github.com/testuser/test-project')
        self.assertEqual(submission_data.completion_status, 'incomplete')
        self.assertIsNotNone(submission_data.grade_percentage)
    
    def test_generate_project_statistics(self):
        """Test generating project statistics."""
        stats = self.service._generate_project_statistics(
            self.test_workflow_state, 
            self.test_submission_status
        )
        
        self.assertEqual(stats['project_name'], 'Test Project')
        self.assertEqual(stats['total_steps'], 5)  # 4 completed + 1 current
        self.assertEqual(stats['completed_steps'], 4)
        self.assertEqual(stats['current_step'], 5)
        self.assertEqual(stats['overall_completion'], 75.0)
        self.assertEqual(stats['github_repository'], 'testuser/test-project')
        self.assertTrue(stats['has_deadline'])
    
    def test_create_checklist_summary(self):
        """Test creating checklist summary."""
        summary = self.service._create_checklist_summary(self.test_submission_status)
        
        self.assertEqual(summary['total_items'], 3)
        self.assertEqual(summary['required_items'], 2)
        self.assertEqual(summary['optional_items'], 1)
        self.assertEqual(summary['completed_required'], 1)
        self.assertEqual(summary['completed_optional'], 1)
        self.assertEqual(len(summary['completion_details']), 3)
    
    def test_generate_validation_results(self):
        """Test generating validation results."""
        results = self.service._generate_validation_results(self.test_submission_status)
        
        self.assertFalse(results['overall_valid'])
        self.assertEqual(results['error_count'], 1)
        self.assertEqual(results['warning_count'], 1)
        self.assertEqual(results['errors'], ['Error 1'])
        self.assertEqual(results['warnings'], ['Warning 1'])
        self.assertEqual(results['completion_percentage'], 75.0)
    
    def test_assess_submission_readiness(self):
        """Test assessing submission readiness."""
        assessment = self.service._assess_submission_readiness(self.test_submission_status)
        
        self.assertFalse(assessment['is_ready'])
        self.assertFalse(assessment['required_items_complete'])  # Only 1 of 2 required items complete
        self.assertFalse(assessment['has_critical_errors'])
        self.assertTrue(assessment['deadline_status_ok'])
        self.assertIsInstance(assessment['readiness_score'], float)
        self.assertIsInstance(assessment['blocking_factors'], list)
        self.assertIsInstance(assessment['recommendations'], list)
    
    def test_validate_github_specific(self):
        """Test GitHub-specific validations."""
        # Valid GitHub URL
        errors = self.service._validate_github_specific("https://github.com/user/repo")
        self.assertEqual(len(errors), 0)
        
        # Invalid owner name
        errors = self.service._validate_github_specific("https://github.com/user@invalid/repo")
        self.assertGreater(len(errors), 0)
        
        # Invalid repo name
        errors = self.service._validate_github_specific("https://github.com/user/repo@invalid")
        self.assertGreater(len(errors), 0)
        
        # Missing parts
        errors = self.service._validate_github_specific("https://github.com/user")
        self.assertGreater(len(errors), 0)
    
    def test_determine_submission_phase(self):
        """Test determining submission phase."""
        # Test different completion levels
        test_cases = [
            (10, "initialization"),
            (35, "development"),
            (60, "integration"),
            (80, "validation"),
            (95, "finalization"),
            (100, "completed")
        ]
        
        for completion, expected_phase in test_cases:
            self.test_submission_status.overall_completion = completion
            phase = self.service._determine_submission_phase(self.test_submission_status)
            self.assertEqual(phase, expected_phase)
    
    def test_estimate_grade(self):
        """Test grade estimation."""
        # Test with no errors/warnings
        self.test_submission_status.submission_errors = []
        self.test_submission_status.submission_warnings = []
        self.test_submission_status.days_until_deadline = 5
        
        grade = self.service._estimate_grade(self.test_submission_status)
        self.assertIsInstance(grade, float)
        self.assertGreaterEqual(grade, 75.0)  # Should be at least the completion percentage
        
        # Test with errors and warnings
        self.test_submission_status.submission_errors = ["Error 1", "Error 2"]
        self.test_submission_status.submission_warnings = ["Warning 1"]
        
        grade_with_penalties = self.service._estimate_grade(self.test_submission_status)
        self.assertLess(grade_with_penalties, grade)  # Should be lower due to penalties
    
    def test_calculate_urgency_level(self):
        """Test calculating urgency level."""
        test_cases = [
            (-1, "overdue"),
            (0, "critical"),
            (1, "urgent"),
            (2, "high"),
            (5, "medium"),
            (10, "low")
        ]
        
        for days, expected_urgency in test_cases:
            self.test_submission_status.days_until_deadline = days
            urgency = self.service._calculate_urgency_level(self.test_submission_status)
            self.assertEqual(urgency, expected_urgency)
        
        # Test with None deadline
        self.test_submission_status.days_until_deadline = None
        urgency = self.service._calculate_urgency_level(self.test_submission_status)
        self.assertEqual(urgency, "unknown")
    
    def test_calculate_readiness_score(self):
        """Test calculating readiness score."""
        # Test with good conditions
        self.test_submission_status.submission_errors = []
        self.test_submission_status.submission_warnings = []
        self.test_submission_status.days_until_deadline = 5
        
        score = self.service._calculate_readiness_score(self.test_submission_status)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
        
        # Test with penalties
        self.test_submission_status.submission_errors = ["Error 1"]
        self.test_submission_status.submission_warnings = ["Warning 1"]
        self.test_submission_status.days_until_deadline = -1  # Overdue
        
        score_with_penalties = self.service._calculate_readiness_score(self.test_submission_status)
        self.assertLess(score_with_penalties, score)
    
    def test_identify_blocking_factors(self):
        """Test identifying blocking factors."""
        blocking_factors = self.service._identify_blocking_factors(self.test_submission_status)
        
        # Should identify incomplete required items
        self.assertGreater(len(blocking_factors), 0)
        self.assertTrue(any("Incomplete required items" in factor for factor in blocking_factors))
        
        # Test with overdue deadline
        self.test_submission_status.days_until_deadline = -1
        blocking_factors = self.service._identify_blocking_factors(self.test_submission_status)
        self.assertTrue(any("Deadline has passed" in factor for factor in blocking_factors))
    
    def test_generate_recommendations(self):
        """Test generating recommendations."""
        recommendations = self.service._generate_recommendations(self.test_submission_status)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should recommend completing items since completion < 80%
        self.assertTrue(any("Complete remaining" in rec for rec in recommendations))
        
        # Should recommend addressing errors
        self.assertTrue(any("Address all validation errors" in rec for rec in recommendations))
    
    def test_error_handling_invalid_workflow_state(self):
        """Test error handling with invalid workflow state."""
        # Test with None project_data
        invalid_state = WorkflowState(
            project_name="Test",
            current_step=1,
            completed_steps=[],
            project_data=None,
            github_repo=None,
            submission_link=None
        )
        
        # Should handle gracefully without crashing
        summary = self.service.generate_submission_summary(invalid_state, self.test_submission_status)
        self.assertIsInstance(summary, LMSSubmissionSummary)
        self.assertEqual(summary.submission_data.project_description, "")
    
    def test_repository_validation_edge_cases(self):
        """Test repository validation with edge cases."""
        edge_cases = [
            ("https://github.com/user/repo/", True),  # Trailing slash should be handled
            ("  https://github.com/user/repo  ", True),  # Whitespace should be handled
            ("https://github.com/user-123/repo_name", True),  # Valid special characters
            ("https://github.com/user/repo-name.test", True),  # Valid repo name with dot
        ]
        
        for url, expected_valid in edge_cases:
            is_valid, errors = self.service.validate_repository_link(url)
            if expected_valid:
                self.assertTrue(is_valid, f"URL should be valid: {url}, errors: {errors}")
            else:
                self.assertFalse(is_valid, f"URL should be invalid: {url}")
    
    def test_submission_status_tracking_edge_cases(self):
        """Test submission status tracking with edge cases."""
        # Test with empty checklist
        empty_status = SubmissionStatus(project_name="Empty Test")
        empty_status.checklist_items = []
        
        tracking = self.service.track_submission_status(self.test_workflow_state, empty_status)
        
        self.assertEqual(tracking['student_progress']['total_items'], 0)
        self.assertEqual(tracking['student_progress']['completion_percentage'], 0)
        
        # Test with no deadline
        no_deadline_status = SubmissionStatus(project_name="No Deadline Test")
        no_deadline_status.deadline = None
        no_deadline_status.days_until_deadline = None
        
        tracking = self.service.track_submission_status(self.test_workflow_state, no_deadline_status)
        
        self.assertIsNone(tracking['deadline_tracking']['deadline'])
        self.assertEqual(tracking['deadline_tracking']['urgency_level'], 'unknown')
    
    def test_report_generation_with_minimal_data(self):
        """Test report generation with minimal data."""
        minimal_state = WorkflowState(
            project_name="Minimal Test",
            current_step=1,
            completed_steps=[],
            project_data=None,
            github_repo=None,
            submission_link=None
        )
        
        minimal_status = SubmissionStatus(project_name="Minimal Test")
        minimal_status.checklist_items = []
        
        # Should generate reports without crashing
        html_report = self.service.generate_lms_report(minimal_state, minimal_status, 'html')
        self.assertIn('Minimal Test', html_report)
        
        markdown_report = self.service.generate_lms_report(minimal_state, minimal_status, 'markdown')
        self.assertIn('Minimal Test', markdown_report)
        
        json_report = self.service.generate_lms_report(minimal_state, minimal_status, 'json')
        import json
        data = json.loads(json_report)
        self.assertEqual(data['submission_data']['project_title'], 'Minimal Test')
        
        text_report = self.service.generate_lms_report(minimal_state, minimal_status, 'text')
        self.assertIn('Minimal Test', text_report)
    
    def test_submission_package_completeness(self):
        """Test that submission package contains all required components."""
        package = self.service.prepare_submission_package(
            self.test_workflow_state, 
            self.test_submission_status
        )
        
        # Check all required sections are present
        required_sections = [
            'metadata', 'submission_summary', 'progress_tracking', 
            'validation_results', 'formatted_reports'
        ]
        
        for section in required_sections:
            self.assertIn(section, package, f"Missing section: {section}")
        
        # Check metadata completeness
        metadata = package['metadata']
        required_metadata = ['generated_at', 'format_version', 'generator', 'submission_id']
        for field in required_metadata:
            self.assertIn(field, metadata, f"Missing metadata field: {field}")
        
        # Check formatted reports completeness
        reports = package['formatted_reports']
        required_formats = ['html', 'markdown', 'text']
        for format_type in required_formats:
            self.assertIn(format_type, reports, f"Missing report format: {format_type}")
            self.assertIsInstance(reports[format_type], str)
            self.assertGreater(len(reports[format_type]), 0)


if __name__ == '__main__':
    unittest.main()