"""
Unit tests for user guidance system.
"""
import unittest
from unittest.mock import Mock, patch
import json

from src.services.user_guidance import (
    UserGuidanceService, 
    GuidanceMessage, 
    ErrorCategory, 
    ErrorSeverity
)


class TestGuidanceMessage(unittest.TestCase):
    """Test GuidanceMessage class."""
    
    def test_guidance_message_creation(self):
        """Test creating a guidance message."""
        message = GuidanceMessage(
            error_code="TEST001",
            title="Test Error",
            description="This is a test error",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            resolution_steps=["Step 1", "Step 2"],
            related_links=["http://example.com"],
            troubleshooting_tips=["Tip 1"]
        )
        
        self.assertEqual(message.error_code, "TEST001")
        self.assertEqual(message.title, "Test Error")
        self.assertEqual(message.category, ErrorCategory.NETWORK)
        self.assertEqual(message.severity, ErrorSeverity.HIGH)
        self.assertEqual(len(message.resolution_steps), 2)
        self.assertEqual(len(message.related_links), 1)
        self.assertEqual(len(message.troubleshooting_tips), 1)
    
    def test_guidance_message_defaults(self):
        """Test guidance message with default values."""
        message = GuidanceMessage(
            error_code="TEST002",
            title="Test Error 2",
            description="Another test error",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            resolution_steps=["Step 1"]
        )
        
        self.assertEqual(message.related_links, [])
        self.assertEqual(message.troubleshooting_tips, [])


class TestUserGuidanceService(unittest.TestCase):
    """Test UserGuidanceService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.guidance_service = UserGuidanceService()
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        self.assertIsNotNone(self.guidance_service.error_catalog)
        self.assertIsNotNone(self.guidance_service.help_topics)
        self.assertIsNotNone(self.guidance_service.troubleshooting_guides)
        
        # Check that catalogs are populated
        self.assertGreater(len(self.guidance_service.error_catalog), 0)
        self.assertGreater(len(self.guidance_service.help_topics), 0)
        self.assertGreater(len(self.guidance_service.troubleshooting_guides), 0)
    
    def test_error_classification_network(self):
        """Test network error classification."""
        test_cases = [
            "Connection failed",
            "Network timeout",
            "DNS resolution failed",
            "Host unreachable"
        ]
        
        for error_msg in test_cases:
            guidance = self.guidance_service.get_error_guidance(error_msg)
            self.assertEqual(guidance.error_code, "NET001")
            self.assertEqual(guidance.category, ErrorCategory.NETWORK)
    
    def test_error_classification_rate_limit(self):
        """Test rate limit error classification."""
        error_msg = "GitHub API rate limit exceeded"
        guidance = self.guidance_service.get_error_guidance(error_msg)
        
        self.assertEqual(guidance.error_code, "NET002")
        self.assertEqual(guidance.category, ErrorCategory.NETWORK)
    
    def test_error_classification_authentication(self):
        """Test authentication error classification."""
        test_cases = [
            "401 Unauthorized",
            "Invalid token",
            "Authentication failed"
        ]
        
        for error_msg in test_cases:
            guidance = self.guidance_service.get_error_guidance(error_msg)
            self.assertEqual(guidance.error_code, "AUTH001")
            self.assertEqual(guidance.category, ErrorCategory.AUTHENTICATION)
    
    def test_error_classification_validation(self):
        """Test validation error classification."""
        # Notebook validation
        notebook_errors = [
            "Notebook validation failed",
            "Missing section in notebook",
            "Empty cell found"
        ]
        
        for error_msg in notebook_errors:
            guidance = self.guidance_service.get_error_guidance(error_msg)
            self.assertEqual(guidance.error_code, "VAL001")
            self.assertEqual(guidance.category, ErrorCategory.VALIDATION)
        
        # Dataset validation
        dataset_errors = [
            "Dataset file invalid",
            "CSV format error",
            "Invalid data format"
        ]
        
        for error_msg in dataset_errors:
            guidance = self.guidance_service.get_error_guidance(error_msg)
            self.assertEqual(guidance.error_code, "VAL002")
            self.assertEqual(guidance.category, ErrorCategory.VALIDATION)
    
    def test_error_classification_file_system(self):
        """Test file system error classification."""
        test_cases = [
            "Permission denied",
            "Access denied",
            "File not found"
        ]
        
        for error_msg in test_cases:
            guidance = self.guidance_service.get_error_guidance(error_msg)
            self.assertEqual(guidance.error_code, "FS001")
            self.assertEqual(guidance.category, ErrorCategory.FILE_SYSTEM)
    
    def test_error_classification_github(self):
        """Test GitHub error classification."""
        test_cases = [
            "Repository creation failed",
            "GitHub API error",
            "403 Forbidden"
        ]
        
        for error_msg in test_cases:
            guidance = self.guidance_service.get_error_guidance(error_msg)
            self.assertEqual(guidance.error_code, "GH001")
            self.assertEqual(guidance.category, ErrorCategory.GITHUB_API)
    
    def test_error_classification_configuration(self):
        """Test configuration error classification."""
        test_cases = [
            "Config file missing",
            "Invalid JSON format",
            "Configuration error"
        ]
        
        for error_msg in test_cases:
            guidance = self.guidance_service.get_error_guidance(error_msg)
            self.assertEqual(guidance.error_code, "CFG001")
            self.assertEqual(guidance.category, ErrorCategory.CONFIGURATION)
    
    def test_error_classification_dependency(self):
        """Test dependency error classification."""
        test_cases = [
            "Module not found",
            "Import error",
            "Package missing"
        ]
        
        for error_msg in test_cases:
            guidance = self.guidance_service.get_error_guidance(error_msg)
            self.assertEqual(guidance.error_code, "DEP001")
            self.assertEqual(guidance.category, ErrorCategory.DEPENDENCY)
    
    def test_error_classification_generic(self):
        """Test generic error classification."""
        error_msg = "Some unknown error occurred"
        guidance = self.guidance_service.get_error_guidance(error_msg)
        
        self.assertEqual(guidance.error_code, "GENERIC")
        self.assertEqual(guidance.category, ErrorCategory.USER_INPUT)
        self.assertEqual(guidance.severity, ErrorSeverity.MEDIUM)
    
    def test_error_guidance_with_context(self):
        """Test error guidance with context information."""
        context = {
            'project_name': 'test-project',
            'step_id': 3,
            'file_path': '/path/to/file.csv'
        }
        
        guidance = self.guidance_service.get_error_guidance("Connection failed", context)
        
        # Check that context is incorporated
        self.assertIn("test-project", guidance.resolution_steps[0])
        self.assertIn("step 3", guidance.troubleshooting_tips[-2])
        self.assertIn("/path/to/file.csv", guidance.troubleshooting_tips[-1])
    
    def test_help_topics(self):
        """Test help topics functionality."""
        # Test listing topics
        topics = self.guidance_service.list_help_topics()
        self.assertIsInstance(topics, list)
        self.assertGreater(len(topics), 0)
        
        # Test getting specific topic
        if topics:
            topic_name = topics[0]
            topic_info = self.guidance_service.get_help_for_topic(topic_name)
            self.assertIsNotNone(topic_info)
            self.assertIn('title', topic_info)
            self.assertIn('description', topic_info)
    
    def test_help_topics_case_insensitive(self):
        """Test help topics are case insensitive."""
        # Assuming 'getting-started' topic exists
        topic_lower = self.guidance_service.get_help_for_topic('getting-started')
        topic_upper = self.guidance_service.get_help_for_topic('GETTING-STARTED')
        topic_mixed = self.guidance_service.get_help_for_topic('Getting-Started')
        
        if topic_lower:  # Only test if topic exists
            self.assertEqual(topic_lower, topic_upper)
            self.assertEqual(topic_lower, topic_mixed)
    
    def test_troubleshooting_guides(self):
        """Test troubleshooting guides functionality."""
        # Test listing guides
        guides = self.guidance_service.list_troubleshooting_guides()
        self.assertIsInstance(guides, list)
        self.assertGreater(len(guides), 0)
        
        # Test getting specific guide
        if guides:
            guide_name = guides[0]
            guide_info = self.guidance_service.get_troubleshooting_guide(guide_name)
            self.assertIsNotNone(guide_info)
            self.assertIn('title', guide_info)
            self.assertIn('description', guide_info)
    
    def test_troubleshooting_guides_case_insensitive(self):
        """Test troubleshooting guides are case insensitive."""
        # Test with a known guide
        guide_lower = self.guidance_service.get_troubleshooting_guide('workflow-stuck')
        guide_upper = self.guidance_service.get_troubleshooting_guide('WORKFLOW-STUCK')
        
        if guide_lower:  # Only test if guide exists
            self.assertEqual(guide_lower, guide_upper)
    
    def test_format_guidance_message(self):
        """Test formatting of guidance messages."""
        message = GuidanceMessage(
            error_code="TEST001",
            title="Test Error",
            description="This is a test error",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            resolution_steps=["Step 1", "Step 2"],
            related_links=["http://example.com"],
            troubleshooting_tips=["Tip 1"]
        )
        
        formatted = self.guidance_service.format_guidance_message(message)
        
        # Check that all components are included
        self.assertIn("Test Error", formatted)
        self.assertIn("TEST001", formatted)
        self.assertIn("Network", formatted)
        self.assertIn("This is a test error", formatted)
        self.assertIn("Step 1", formatted)
        self.assertIn("Step 2", formatted)
        self.assertIn("http://example.com", formatted)
        self.assertIn("Tip 1", formatted)
        self.assertIn("❌", formatted)  # High severity icon
    
    def test_format_guidance_message_severity_icons(self):
        """Test correct severity icons in formatted messages."""
        severities_and_icons = [
            (ErrorSeverity.LOW, "ℹ️"),
            (ErrorSeverity.MEDIUM, "⚠️"),
            (ErrorSeverity.HIGH, "❌"),
            (ErrorSeverity.CRITICAL, "🚨")
        ]
        
        for severity, expected_icon in severities_and_icons:
            message = GuidanceMessage(
                error_code="TEST",
                title="Test",
                description="Test",
                category=ErrorCategory.NETWORK,
                severity=severity,
                resolution_steps=["Step 1"]
            )
            
            formatted = self.guidance_service.format_guidance_message(message)
            self.assertIn(expected_icon, formatted)
    
    def test_customize_guidance_no_context(self):
        """Test guidance customization with no context."""
        original_message = GuidanceMessage(
            error_code="TEST001",
            title="Test Error",
            description="Test description",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=["Step 1"],
            troubleshooting_tips=["Tip 1"]
        )
        
        customized = self.guidance_service._customize_guidance(original_message, None)
        
        # Should be identical to original
        self.assertEqual(customized.error_code, original_message.error_code)
        self.assertEqual(customized.resolution_steps, original_message.resolution_steps)
        self.assertEqual(customized.troubleshooting_tips, original_message.troubleshooting_tips)
    
    def test_customize_guidance_with_context(self):
        """Test guidance customization with context."""
        original_message = GuidanceMessage(
            error_code="TEST001",
            title="Test Error",
            description="Test description",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=["Step 1"],
            troubleshooting_tips=["Tip 1"]
        )
        
        context = {
            'project_name': 'test-project',
            'step_id': 2,
            'file_path': '/test/path'
        }
        
        customized = self.guidance_service._customize_guidance(original_message, context)
        
        # Should have additional context information
        self.assertGreater(len(customized.resolution_steps), len(original_message.resolution_steps))
        self.assertGreater(len(customized.troubleshooting_tips), len(original_message.troubleshooting_tips))
        
        # Check context is included
        self.assertIn("test-project", customized.resolution_steps[0])
    
    def test_get_nonexistent_help_topic(self):
        """Test getting non-existent help topic."""
        result = self.guidance_service.get_help_for_topic("nonexistent-topic")
        self.assertIsNone(result)
    
    def test_get_nonexistent_troubleshooting_guide(self):
        """Test getting non-existent troubleshooting guide."""
        result = self.guidance_service.get_troubleshooting_guide("nonexistent-guide")
        self.assertIsNone(result)
    
    def test_error_catalog_completeness(self):
        """Test that error catalog contains expected error codes."""
        expected_codes = [
            "NET001", "NET002", "AUTH001", "VAL001", "VAL002",
            "FS001", "GH001", "CFG001", "DEP001", "WF001", 
            "WF002", "WF003", "LMS001", "PRJ001"
        ]
        
        for code in expected_codes:
            self.assertIn(code, self.guidance_service.error_catalog)
            guidance = self.guidance_service.error_catalog[code]
            self.assertIsInstance(guidance, GuidanceMessage)
            self.assertEqual(guidance.error_code, code)
            self.assertGreater(len(guidance.resolution_steps), 0)
    
    def test_help_topics_structure(self):
        """Test help topics have proper structure."""
        for topic_name, topic_info in self.guidance_service.help_topics.items():
            self.assertIn('title', topic_info)
            self.assertIn('description', topic_info)
            self.assertIn('sections', topic_info)
            
            for section in topic_info['sections']:
                self.assertIn('title', section)
                self.assertIn('content', section)
    
    def test_troubleshooting_guides_structure(self):
        """Test troubleshooting guides have proper structure."""
        for guide_name, guide_info in self.guidance_service.troubleshooting_guides.items():
            self.assertIn('title', guide_info)
            self.assertIn('description', guide_info)
            
            # Optional fields should be lists if present
            for field in ['symptoms', 'diagnosis_steps', 'solutions']:
                if field in guide_info:
                    self.assertIsInstance(guide_info[field], list)
    
    def test_workflow_error_classification(self):
        """Test workflow-specific error classification."""
        test_cases = [
            ("Workflow step failed", "WF001"),
            ("Progress state corrupted", "WF002"),
            ("Submission validation failed", "WF003")
        ]
        
        for error_msg, expected_code in test_cases:
            guidance = self.guidance_service.get_error_guidance(error_msg)
            self.assertEqual(guidance.error_code, expected_code)
    
    def test_lms_error_classification(self):
        """Test LMS integration error classification."""
        error_msg = "LMS submission failed"
        guidance = self.guidance_service.get_error_guidance(error_msg)
        
        self.assertEqual(guidance.error_code, "LMS001")
        self.assertEqual(guidance.category, ErrorCategory.NETWORK)
    
    def test_project_error_classification(self):
        """Test project-specific error classification."""
        error_msg = "Project selection invalid"
        guidance = self.guidance_service.get_error_guidance(error_msg)
        
        self.assertEqual(guidance.error_code, "PRJ001")
        self.assertEqual(guidance.category, ErrorCategory.USER_INPUT)
    
    def test_enhanced_help_topics(self):
        """Test enhanced help topics are available."""
        expected_topics = [
            "getting-started", "github-setup", "troubleshooting",
            "workflow-commands", "project-requirements", "error-recovery"
        ]
        
        available_topics = self.guidance_service.list_help_topics()
        
        for topic in expected_topics:
            self.assertIn(topic, available_topics)
            topic_info = self.guidance_service.get_help_for_topic(topic)
            self.assertIsNotNone(topic_info)
            self.assertIn('title', topic_info)
            self.assertIn('sections', topic_info)
    
    def test_enhanced_troubleshooting_guides(self):
        """Test enhanced troubleshooting guides are available."""
        expected_guides = [
            "workflow-stuck", "github-authentication", "notebook-validation",
            "dataset-issues", "submission-deadline", "repository-access",
            "environment-setup", "performance-optimization"
        ]
        
        available_guides = self.guidance_service.list_troubleshooting_guides()
        
        for guide in expected_guides:
            self.assertIn(guide, available_guides)
            guide_info = self.guidance_service.get_troubleshooting_guide(guide)
            self.assertIsNotNone(guide_info)
            self.assertIn('title', guide_info)
            self.assertIn('description', guide_info)
    
    def test_error_message_context_integration(self):
        """Test error messages properly integrate context information."""
        context = {
            'project_name': 'test-project',
            'step_id': 5,
            'file_path': '/test/data.csv',
            'user_id': 'test_user'
        }
        
        guidance = self.guidance_service.get_error_guidance("Network timeout", context)
        
        # Check context is properly integrated
        self.assertIn("test-project", guidance.resolution_steps[0])
        
        # Check troubleshooting tips include context
        context_tips = [tip for tip in guidance.troubleshooting_tips 
                       if any(ctx_val in tip for ctx_val in context.values() if isinstance(ctx_val, str))]
        self.assertGreater(len(context_tips), 0)
    
    def test_severity_based_formatting(self):
        """Test that different severity levels produce appropriate formatting."""
        severities = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        expected_icons = ["ℹ️", "⚠️", "❌", "🚨"]
        
        for severity, expected_icon in zip(severities, expected_icons):
            message = GuidanceMessage(
                error_code="TEST",
                title="Test Error",
                description="Test description",
                category=ErrorCategory.NETWORK,
                severity=severity,
                resolution_steps=["Step 1"]
            )
            
            formatted = self.guidance_service.format_guidance_message(message)
            self.assertIn(expected_icon, formatted)
    
    def test_comprehensive_error_scenarios(self):
        """Test comprehensive error scenarios that might occur in real usage."""
        error_scenarios = [
            {
                'message': 'GitHub API rate limit exceeded for user',
                'expected_code': 'NET002',
                'context': {'user_id': 'test_user', 'api_calls': 5000}
            },
            {
                'message': 'Notebook validation failed: missing data analysis section',
                'expected_code': 'VAL001',
                'context': {'notebook_path': '/project/analysis.ipynb', 'step_id': 4}
            },
            {
                'message': 'Repository creation failed: name already exists',
                'expected_code': 'GH001',
                'context': {'repo_name': 'test-repo', 'user': 'testuser'}
            },
            {
                'message': 'LMS submission failed: connection timeout',
                'expected_code': 'LMS001',
                'context': {'submission_id': '12345', 'deadline': '2024-01-15'}
            }
        ]
        
        for scenario in error_scenarios:
            guidance = self.guidance_service.get_error_guidance(
                scenario['message'], 
                scenario.get('context')
            )
            
            self.assertEqual(guidance.error_code, scenario['expected_code'])
            self.assertGreater(len(guidance.resolution_steps), 0)
            self.assertIsInstance(guidance.severity, ErrorSeverity)
    
    def test_help_topic_content_quality(self):
        """Test that help topics contain quality, useful content."""
        for topic_name in self.guidance_service.list_help_topics():
            topic_info = self.guidance_service.get_help_for_topic(topic_name)
            
            # Check basic structure
            self.assertIn('title', topic_info)
            self.assertIn('description', topic_info)
            self.assertIn('sections', topic_info)
            
            # Check content quality
            self.assertGreater(len(topic_info['title']), 5)
            self.assertGreater(len(topic_info['description']), 10)
            self.assertGreater(len(topic_info['sections']), 0)
            
            # Check each section has meaningful content
            for section in topic_info['sections']:
                self.assertIn('title', section)
                self.assertIn('content', section)
                self.assertIsInstance(section['content'], list)
                self.assertGreater(len(section['content']), 0)
    
    def test_troubleshooting_guide_completeness(self):
        """Test that troubleshooting guides are complete and useful."""
        for guide_name in self.guidance_service.list_troubleshooting_guides():
            guide_info = self.guidance_service.get_troubleshooting_guide(guide_name)
            
            # Check required fields
            self.assertIn('title', guide_info)
            self.assertIn('description', guide_info)
            
            # Check content quality
            self.assertGreater(len(guide_info['title']), 5)
            self.assertGreater(len(guide_info['description']), 10)
            
            # If optional fields exist, they should have content
            for field in ['symptoms', 'diagnosis_steps', 'solutions']:
                if field in guide_info:
                    self.assertIsInstance(guide_info[field], list)
                    self.assertGreater(len(guide_info[field]), 0)
                    # Each item should be a meaningful string
                    for item in guide_info[field]:
                        self.assertIsInstance(item, str)
                        self.assertGreater(len(item), 5)
    
    def test_error_guidance_consistency(self):
        """Test that error guidance is consistent across similar error types."""
        # Test that all network errors have similar structure
        network_errors = ["Connection failed", "Network timeout", "DNS resolution failed"]
        
        for error_msg in network_errors:
            guidance = self.guidance_service.get_error_guidance(error_msg)
            self.assertEqual(guidance.category, ErrorCategory.NETWORK)
            self.assertIn("connection", guidance.resolution_steps[0].lower())
    
    def test_generic_error_handling_quality(self):
        """Test that generic error handling provides useful guidance."""
        unknown_error = "Some completely unknown error that doesn't match any pattern"
        guidance = self.guidance_service.get_error_guidance(unknown_error)
        
        self.assertEqual(guidance.error_code, "GENERIC")
        self.assertEqual(guidance.category, ErrorCategory.USER_INPUT)
        self.assertEqual(guidance.severity, ErrorSeverity.MEDIUM)
        
        # Should still provide useful generic guidance
        self.assertGreater(len(guidance.resolution_steps), 3)
        self.assertIn(unknown_error, guidance.description)
    
    def test_interactive_help_search(self):
        """Test interactive help search functionality."""
        # Test searching for GitHub-related help
        results = self.guidance_service.get_interactive_help("github")
        
        self.assertIn('query', results)
        self.assertIn('help_topics', results)
        self.assertIn('troubleshooting_guides', results)
        self.assertIn('error_guidance', results)
        self.assertIn('total_results', results)
        
        self.assertEqual(results['query'], "github")
        self.assertGreater(results['total_results'], 0)
        
        # Should find GitHub-related content
        github_content_found = (
            any('github' in topic['name'].lower() for topic in results['help_topics']) or
            any('github' in guide['name'].lower() for guide in results['troubleshooting_guides']) or
            any('github' in error['title'].lower() for error in results['error_guidance'])
        )
        self.assertTrue(github_content_found)
    
    def test_interactive_help_empty_query(self):
        """Test interactive help with empty or non-matching query."""
        results = self.guidance_service.get_interactive_help("nonexistentquery12345")
        
        self.assertEqual(results['total_results'], 0)
        self.assertEqual(len(results['help_topics']), 0)
        self.assertEqual(len(results['troubleshooting_guides']), 0)
        self.assertEqual(len(results['error_guidance']), 0)
    
    def test_quick_help_functionality(self):
        """Test quick help functionality."""
        # Test known quick help topics
        known_topics = ['start', 'resume', 'progress', 'github', 'notebook']
        
        for topic in known_topics:
            help_text = self.guidance_service.get_quick_help(topic)
            self.assertIsInstance(help_text, str)
            self.assertGreater(len(help_text), 10)
            self.assertNotIn("No quick help available", help_text)
        
        # Test unknown topic
        unknown_help = self.guidance_service.get_quick_help("unknowntopic")
        self.assertIn("No quick help available", unknown_help)
    
    def test_quick_help_case_insensitive(self):
        """Test that quick help is case insensitive."""
        help_lower = self.guidance_service.get_quick_help("github")
        help_upper = self.guidance_service.get_quick_help("GITHUB")
        help_mixed = self.guidance_service.get_quick_help("GitHub")
        
        self.assertEqual(help_lower, help_upper)
        self.assertEqual(help_lower, help_mixed)
    
    def test_suggest_next_steps_normal_flow(self):
        """Test next step suggestions for normal workflow."""
        for step in range(1, 6):
            suggestions = self.guidance_service.suggest_next_steps(step, error_occurred=False)
            
            self.assertIsInstance(suggestions, list)
            self.assertGreater(len(suggestions), 0)
            
            # Each suggestion should be a meaningful string
            for suggestion in suggestions:
                self.assertIsInstance(suggestion, str)
                self.assertGreater(len(suggestion), 10)
    
    def test_suggest_next_steps_error_flow(self):
        """Test next step suggestions when error occurred."""
        suggestions = self.guidance_service.suggest_next_steps(3, error_occurred=True)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Should contain error-specific guidance
        error_keywords = ['error', 'troubleshooting', 'retry', 'resume']
        suggestion_text = ' '.join(suggestions).lower()
        
        found_error_guidance = any(keyword in suggestion_text for keyword in error_keywords)
        self.assertTrue(found_error_guidance)
    
    def test_suggest_next_steps_unknown_step(self):
        """Test next step suggestions for unknown step."""
        suggestions = self.guidance_service.suggest_next_steps(99, error_occurred=False)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Should provide generic but useful guidance
        for suggestion in suggestions:
            self.assertIsInstance(suggestion, str)
            self.assertGreater(len(suggestion), 5)


class TestErrorCategoryAndSeverity(unittest.TestCase):
    """Test ErrorCategory and ErrorSeverity enums."""
    
    def test_error_category_values(self):
        """Test ErrorCategory enum values."""
        expected_categories = [
            "network", "authentication", "validation", "user_input",
            "file_system", "github_api", "configuration", "dependency"
        ]
        
        for category in ErrorCategory:
            self.assertIn(category.value, expected_categories)
    
    def test_error_severity_values(self):
        """Test ErrorSeverity enum values."""
        expected_severities = ["low", "medium", "high", "critical"]
        
        for severity in ErrorSeverity:
            self.assertIn(severity.value, expected_severities)


if __name__ == '__main__':
    unittest.main()