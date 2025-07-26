"""
Unit tests for help system CLI.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import argparse
import io
import sys

from src.cli.help_system import HelpSystemCLI
from src.services.user_guidance import UserGuidanceService, GuidanceMessage, ErrorCategory, ErrorSeverity


class TestHelpSystemCLI(unittest.TestCase):
    """Test HelpSystemCLI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.help_cli = HelpSystemCLI()
        self.mock_guidance_service = Mock(spec=UserGuidanceService)
        self.help_cli.guidance_service = self.mock_guidance_service
    
    def test_cli_initialization(self):
        """Test CLI initializes correctly."""
        cli = HelpSystemCLI()
        self.assertIsNotNone(cli.guidance_service)
        self.assertIsInstance(cli.guidance_service, UserGuidanceService)
    
    def test_setup_parser(self):
        """Test parser setup."""
        self.help_cli.setup_parser()
        
        # Test that parser has expected subcommands
        help_text = self.help_cli.parser.format_help()
        self.assertIn('topic', help_text)
        self.assertIn('troubleshoot', help_text)
        self.assertIn('error', help_text)
        self.assertIn('interactive', help_text)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_topic_command_list(self, mock_stdout):
        """Test topic command with list option."""
        self.mock_guidance_service.list_help_topics.return_value = ['topic1', 'topic2']
        self.mock_guidance_service.get_help_for_topic.side_effect = [
            {'description': 'Description 1'},
            {'description': 'Description 2'}
        ]
        
        args = argparse.Namespace(command='topic', topic_name='list')
        result = self.help_cli._handle_topic_command(args)
        
        self.assertEqual(result, 0)
        self.mock_guidance_service.list_help_topics.assert_called_once()
        output = mock_stdout.getvalue()
        self.assertIn('Available Help Topics', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_topic_command_specific(self, mock_stdout):
        """Test topic command with specific topic."""
        mock_topic_info = {
            'title': 'Test Topic',
            'description': 'Test description',
            'sections': [
                {
                    'title': 'Section 1',
                    'content': ['Item 1', 'Item 2']
                }
            ]
        }
        self.mock_guidance_service.get_help_for_topic.return_value = mock_topic_info
        
        args = argparse.Namespace(command='topic', topic_name='test-topic')
        result = self.help_cli._handle_topic_command(args)
        
        self.assertEqual(result, 0)
        self.mock_guidance_service.get_help_for_topic.assert_called_once_with('test-topic')
        output = mock_stdout.getvalue()
        self.assertIn('Test Topic', output)
        self.assertIn('Test description', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_topic_command_not_found(self, mock_stdout):
        """Test topic command with non-existent topic."""
        self.mock_guidance_service.get_help_for_topic.return_value = None
        self.mock_guidance_service.list_help_topics.return_value = ['topic1', 'topic2']
        
        args = argparse.Namespace(command='topic', topic_name='nonexistent')
        result = self.help_cli._handle_topic_command(args)
        
        self.assertEqual(result, 1)
        output = mock_stdout.getvalue()
        self.assertIn("not found", output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_troubleshoot_command_list(self, mock_stdout):
        """Test troubleshoot command with list option."""
        self.mock_guidance_service.list_troubleshooting_guides.return_value = ['guide1', 'guide2']
        self.mock_guidance_service.get_troubleshooting_guide.side_effect = [
            {'description': 'Guide 1 description'},
            {'description': 'Guide 2 description'}
        ]
        
        args = argparse.Namespace(command='troubleshoot', issue='list')
        result = self.help_cli._handle_troubleshoot_command(args)
        
        self.assertEqual(result, 0)
        self.mock_guidance_service.list_troubleshooting_guides.assert_called_once()
        output = mock_stdout.getvalue()
        self.assertIn('Available Troubleshooting Guides', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_troubleshoot_command_specific(self, mock_stdout):
        """Test troubleshoot command with specific issue."""
        mock_guide = {
            'title': 'Test Guide',
            'description': 'Test guide description',
            'symptoms': ['Symptom 1', 'Symptom 2'],
            'diagnosis_steps': ['Step 1', 'Step 2'],
            'solutions': ['Solution 1', 'Solution 2']
        }
        self.mock_guidance_service.get_troubleshooting_guide.return_value = mock_guide
        
        args = argparse.Namespace(command='troubleshoot', issue='test-issue')
        result = self.help_cli._handle_troubleshoot_command(args)
        
        self.assertEqual(result, 0)
        self.mock_guidance_service.get_troubleshooting_guide.assert_called_once_with('test-issue')
        output = mock_stdout.getvalue()
        self.assertIn('Test Guide', output)
        self.assertIn('Symptoms', output)
        self.assertIn('Solutions', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_error_command(self, mock_stdout):
        """Test error command."""
        mock_guidance = GuidanceMessage(
            error_code="TEST001",
            title="Test Error",
            description="Test description",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            resolution_steps=["Step 1", "Step 2"]
        )
        self.mock_guidance_service.get_error_guidance.return_value = mock_guidance
        self.mock_guidance_service.format_guidance_message.return_value = "Formatted guidance"
        
        args = argparse.Namespace(command='error', error_message='test error', context=None)
        result = self.help_cli._handle_error_command(args)
        
        self.assertEqual(result, 0)
        self.mock_guidance_service.get_error_guidance.assert_called_once_with('test error', None)
        self.mock_guidance_service.format_guidance_message.assert_called_once_with(mock_guidance)
        output = mock_stdout.getvalue()
        self.assertIn('Formatted guidance', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_error_command_with_context(self, mock_stdout):
        """Test error command with JSON context."""
        mock_guidance = GuidanceMessage(
            error_code="TEST001",
            title="Test Error",
            description="Test description",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            resolution_steps=["Step 1"]
        )
        self.mock_guidance_service.get_error_guidance.return_value = mock_guidance
        self.mock_guidance_service.format_guidance_message.return_value = "Formatted guidance"
        
        context_json = '{"project_name": "test", "step_id": 1}'
        args = argparse.Namespace(command='error', error_message='test error', context=context_json)
        result = self.help_cli._handle_error_command(args)
        
        self.assertEqual(result, 0)
        expected_context = {"project_name": "test", "step_id": 1}
        self.mock_guidance_service.get_error_guidance.assert_called_once_with('test error', expected_context)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_error_command_invalid_context(self, mock_stdout):
        """Test error command with invalid JSON context."""
        mock_guidance = GuidanceMessage(
            error_code="TEST001",
            title="Test Error",
            description="Test description",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            resolution_steps=["Step 1"]
        )
        self.mock_guidance_service.get_error_guidance.return_value = mock_guidance
        self.mock_guidance_service.format_guidance_message.return_value = "Formatted guidance"
        
        args = argparse.Namespace(command='error', error_message='test error', context='invalid json')
        result = self.help_cli._handle_error_command(args)
        
        self.assertEqual(result, 0)
        # Should call with None context due to invalid JSON
        self.mock_guidance_service.get_error_guidance.assert_called_once_with('test error', None)
        output = mock_stdout.getvalue()
        self.assertIn('Invalid context JSON', output)
    
    @patch('builtins.input', side_effect=['exit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_interactive_command_exit(self, mock_stdout, mock_input):
        """Test interactive command with immediate exit."""
        args = argparse.Namespace(command='interactive')
        result = self.help_cli._handle_interactive_command(args)
        
        self.assertEqual(result, 0)
        output = mock_stdout.getvalue()
        self.assertIn('Welcome to Interactive Help', output)
        self.assertIn('Goodbye', output)
    
    @patch('builtins.input', side_effect=['menu', 'exit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_interactive_command_menu(self, mock_stdout, mock_input):
        """Test interactive command with menu display."""
        args = argparse.Namespace(command='interactive')
        result = self.help_cli._handle_interactive_command(args)
        
        self.assertEqual(result, 0)
        output = mock_stdout.getvalue()
        self.assertIn('Interactive Help Menu', output)
    
    @patch('builtins.input', side_effect=['topic test-topic', 'exit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_interactive_command_topic(self, mock_stdout, mock_input):
        """Test interactive command with topic request."""
        mock_topic_info = {
            'title': 'Test Topic',
            'description': 'Test description',
            'sections': []
        }
        self.mock_guidance_service.get_help_for_topic.return_value = mock_topic_info
        
        args = argparse.Namespace(command='interactive')
        result = self.help_cli._handle_interactive_command(args)
        
        self.assertEqual(result, 0)
        self.mock_guidance_service.get_help_for_topic.assert_called_with('test-topic')
    
    @patch('builtins.input', side_effect=['topics', 'exit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_interactive_command_topics_list(self, mock_stdout, mock_input):
        """Test interactive command with topics list."""
        self.mock_guidance_service.list_help_topics.return_value = ['topic1', 'topic2']
        self.mock_guidance_service.get_help_for_topic.side_effect = [
            {'description': 'Description 1'},
            {'description': 'Description 2'}
        ]
        
        args = argparse.Namespace(command='interactive')
        result = self.help_cli._handle_interactive_command(args)
        
        self.assertEqual(result, 0)
        self.mock_guidance_service.list_help_topics.assert_called()
    
    @patch('builtins.input', side_effect=['unknown command', 'exit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_interactive_command_search(self, mock_stdout, mock_input):
        """Test interactive command with search functionality."""
        mock_guidance = GuidanceMessage(
            error_code="GENERIC",
            title="Generic Error",
            description="Generic description",
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=["Step 1"]
        )
        self.mock_guidance_service.get_error_guidance.return_value = mock_guidance
        self.mock_guidance_service.list_help_topics.return_value = []
        self.mock_guidance_service.list_troubleshooting_guides.return_value = []
        
        args = argparse.Namespace(command='interactive')
        result = self.help_cli._handle_interactive_command(args)
        
        self.assertEqual(result, 0)
        self.mock_guidance_service.get_error_guidance.assert_called_with('unknown command')
    
    @patch('builtins.input', side_effect=[KeyboardInterrupt(), 'exit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_handle_interactive_command_keyboard_interrupt(self, mock_stdout, mock_input):
        """Test interactive command handles keyboard interrupt."""
        args = argparse.Namespace(command='interactive')
        result = self.help_cli._handle_interactive_command(args)
        
        self.assertEqual(result, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Use 'exit' to quit", output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_show_main_help(self, mock_stdout):
        """Test main help display."""
        self.help_cli._show_main_help()
        
        output = mock_stdout.getvalue()
        self.assertIn('EV Analysis Help System', output)
        self.assertIn('Available Commands', output)
        self.assertIn('topic', output)
        self.assertIn('troubleshoot', output)
        self.assertIn('error', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_list_help_topics(self, mock_stdout):
        """Test listing help topics."""
        self.mock_guidance_service.list_help_topics.return_value = ['topic1', 'topic2']
        self.mock_guidance_service.get_help_for_topic.side_effect = [
            {'description': 'Description 1'},
            {'description': 'Description 2'}
        ]
        
        self.help_cli._list_help_topics()
        
        output = mock_stdout.getvalue()
        self.assertIn('Available Help Topics', output)
        self.assertIn('topic1', output)
        self.assertIn('topic2', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_list_troubleshooting_guides(self, mock_stdout):
        """Test listing troubleshooting guides."""
        self.mock_guidance_service.list_troubleshooting_guides.return_value = ['guide1', 'guide2']
        self.mock_guidance_service.get_troubleshooting_guide.side_effect = [
            {'description': 'Guide 1 description'},
            {'description': 'Guide 2 description'}
        ]
        
        self.help_cli._list_troubleshooting_guides()
        
        output = mock_stdout.getvalue()
        self.assertIn('Available Troubleshooting Guides', output)
        self.assertIn('guide1', output)
        self.assertIn('guide2', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_display_help_topic(self, mock_stdout):
        """Test displaying help topic."""
        topic_info = {
            'title': 'Test Topic',
            'description': 'Test description',
            'sections': [
                {
                    'title': 'Section 1',
                    'content': ['Item 1', 'Item 2']
                },
                {
                    'title': 'Section 2',
                    'content': 'Single content item'
                }
            ]
        }
        
        self.help_cli._display_help_topic(topic_info)
        
        output = mock_stdout.getvalue()
        self.assertIn('Test Topic', output)
        self.assertIn('Test description', output)
        self.assertIn('Section 1', output)
        self.assertIn('Item 1', output)
        self.assertIn('Section 2', output)
        self.assertIn('Single content item', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_display_troubleshooting_guide(self, mock_stdout):
        """Test displaying troubleshooting guide."""
        guide = {
            'title': 'Test Guide',
            'description': 'Test guide description',
            'symptoms': ['Symptom 1', 'Symptom 2'],
            'diagnosis_steps': ['Diagnosis 1', 'Diagnosis 2'],
            'solutions': ['Solution 1', 'Solution 2']
        }
        
        self.help_cli._display_troubleshooting_guide(guide)
        
        output = mock_stdout.getvalue()
        self.assertIn('Test Guide', output)
        self.assertIn('Test guide description', output)
        self.assertIn('Symptoms', output)
        self.assertIn('Symptom 1', output)
        self.assertIn('Diagnosis Steps', output)
        self.assertIn('Diagnosis 1', output)
        self.assertIn('Solutions', output)
        self.assertIn('Solution 1', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_search_help_error_match(self, mock_stdout):
        """Test search help with error match."""
        mock_guidance = GuidanceMessage(
            error_code="NET001",
            title="Network Error",
            description="Network error description",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            resolution_steps=["Step 1"]
        )
        self.mock_guidance_service.get_error_guidance.return_value = mock_guidance
        self.mock_guidance_service.format_guidance_message.return_value = "Formatted guidance"
        
        self.help_cli._search_help('connection failed')
        
        output = mock_stdout.getvalue()
        self.assertIn('Found matching error guidance', output)
        self.assertIn('Formatted guidance', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_search_help_topic_match(self, mock_stdout):
        """Test search help with topic match."""
        mock_guidance = GuidanceMessage(
            error_code="GENERIC",
            title="Generic",
            description="Generic",
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=["Step 1"]
        )
        self.mock_guidance_service.get_error_guidance.return_value = mock_guidance
        self.mock_guidance_service.list_help_topics.return_value = ['getting-started', 'github-setup']
        self.mock_guidance_service.get_help_for_topic.side_effect = [
            {'description': 'Getting started guide'},
            {'description': 'GitHub setup guide'}
        ]
        
        self.help_cli._search_help('github')
        
        output = mock_stdout.getvalue()
        self.assertIn('Found matching help topics', output)
        self.assertIn('github-setup', output)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_search_help_no_match(self, mock_stdout):
        """Test search help with no matches."""
        mock_guidance = GuidanceMessage(
            error_code="GENERIC",
            title="Generic",
            description="Generic",
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.MEDIUM,
            resolution_steps=["Step 1"]
        )
        self.mock_guidance_service.get_error_guidance.return_value = mock_guidance
        self.mock_guidance_service.list_help_topics.return_value = []
        self.mock_guidance_service.list_troubleshooting_guides.return_value = []
        
        self.help_cli._search_help('nonexistent')
        
        output = mock_stdout.getvalue()
        self.assertIn('No specific help found', output)
        self.assertIn('Try one of these options', output)
    
    def test_execute_command_exception_handling(self):
        """Test execute command handles exceptions."""
        args = argparse.Namespace(command='topic', topic_name='test')
        self.mock_guidance_service.get_help_for_topic.side_effect = Exception("Test exception")
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = self.help_cli.execute_command(args)
        
        self.assertEqual(result, 1)
        output = mock_stdout.getvalue()
        self.assertIn('Help command failed', output)


if __name__ == '__main__':
    unittest.main()