"""
Unit tests for CLI interface components.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import argparse
import sys
from io import StringIO

from src.cli.base_cli import BaseCLI
from src.cli.workflow_cli import WorkflowCLI


class TestBaseCLI(unittest.TestCase):
    """Test cases for BaseCLI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a concrete implementation for testing
        class TestCLI(BaseCLI):
            def setup_parser(self):
                self.parser.add_argument('--test', action='store_true')
            
            def execute_command(self, args):
                return 0 if args.test else 1
        
        self.cli = TestCLI()
    
    def test_parser_initialization(self):
        """Test that parser is properly initialized."""
        self.assertIsInstance(self.cli.parser, argparse.ArgumentParser)
        self.assertEqual(
            self.cli.parser.description,
            "AICTE Project Workflow Automation Tool"
        )
    
    @patch('builtins.input', return_value='test response')
    def test_prompt_user_basic(self, mock_input):
        """Test basic user prompting."""
        result = self.cli.prompt_user("Enter something")
        self.assertEqual(result, "test response")
        mock_input.assert_called_once_with("Enter something: ")
    
    @patch('builtins.input', return_value='')
    def test_prompt_user_with_default(self, mock_input):
        """Test user prompting with default value."""
        result = self.cli.prompt_user("Enter something", default="default_value")
        self.assertEqual(result, "default_value")
        mock_input.assert_called_once_with("Enter something [default_value]: ")
    
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_prompt_user_keyboard_interrupt(self, mock_input):
        """Test user prompting handles keyboard interrupt."""
        result = self.cli.prompt_user("Enter something", default="default")
        self.assertEqual(result, "default")
    
    @patch('builtins.input', return_value='y')
    def test_prompt_yes_no_yes(self, mock_input):
        """Test yes/no prompting with yes response."""
        result = self.cli.prompt_yes_no("Continue?")
        self.assertTrue(result)
    
    @patch('builtins.input', return_value='n')
    def test_prompt_yes_no_no(self, mock_input):
        """Test yes/no prompting with no response."""
        result = self.cli.prompt_yes_no("Continue?")
        self.assertFalse(result)
    
    @patch('builtins.input', return_value='')
    def test_prompt_yes_no_default_true(self, mock_input):
        """Test yes/no prompting with default true."""
        result = self.cli.prompt_yes_no("Continue?", default=True)
        self.assertTrue(result)
    
    @patch('builtins.input', return_value='')
    def test_prompt_yes_no_default_false(self, mock_input):
        """Test yes/no prompting with default false."""
        result = self.cli.prompt_yes_no("Continue?", default=False)
        self.assertFalse(result)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_progress(self, mock_stdout):
        """Test progress display."""
        self.cli.display_progress(5, 10, "Processing")
        output = mock_stdout.getvalue()
        self.assertIn("Processing", output)
        self.assertIn("50.0%", output)
        self.assertIn("(5/10)", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_progress_complete(self, mock_stdout):
        """Test progress display when complete."""
        self.cli.display_progress(10, 10, "Complete")
        output = mock_stdout.getvalue()
        self.assertIn("100.0%", output)
        self.assertIn("(10/10)", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_status(self, mock_stdout):
        """Test status display."""
        status_data = {
            'project_name': 'test-project',
            'current_step': 'Step 1',
            'progress_percentage': 75.5,
            'completed_steps': 3,
            'total_steps': 4,
            'github_repo': 'https://github.com/user/repo',
            'submission_link': 'https://lms.example.com/submit',
            'updated_at': '2024-01-01 12:00:00'
        }
        
        self.cli.display_status(status_data)
        output = mock_stdout.getvalue()
        
        self.assertIn("test-project", output)
        self.assertIn("Step 1", output)
        self.assertIn("75.5%", output)
        self.assertIn("3/4", output)
        self.assertIn("github.com/user/repo", output)
        self.assertIn("lms.example.com/submit", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_error(self, mock_stdout):
        """Test error display."""
        suggestions = ["Try this", "Or this"]
        self.cli.display_error("Something went wrong", suggestions)
        output = mock_stdout.getvalue()
        
        self.assertIn("❌ Error: Something went wrong", output)
        self.assertIn("💡 Suggestions:", output)
        self.assertIn("1. Try this", output)
        self.assertIn("2. Or this", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_success(self, mock_stdout):
        """Test success display."""
        self.cli.display_success("Operation completed")
        output = mock_stdout.getvalue()
        self.assertIn("✅ Operation completed", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_warning(self, mock_stdout):
        """Test warning display."""
        self.cli.display_warning("Be careful")
        output = mock_stdout.getvalue()
        self.assertIn("⚠️  Warning: Be careful", output)
    
    def test_run_success(self):
        """Test successful command execution."""
        result = self.cli.run(['--test'])
        self.assertEqual(result, 0)
    
    def test_run_failure(self):
        """Test failed command execution."""
        result = self.cli.run([])
        self.assertEqual(result, 1)
    
    @patch('builtins.print')
    def test_run_keyboard_interrupt(self, mock_print):
        """Test keyboard interrupt handling."""
        with patch.object(self.cli.parser, 'parse_args', side_effect=KeyboardInterrupt):
            result = self.cli.run([])
            self.assertEqual(result, 1)
            mock_print.assert_called_with("\nOperation cancelled by user.")
    
    @patch('builtins.input', return_value='2')
    @patch('builtins.print')
    def test_prompt_choice_by_number(self, mock_print, mock_input):
        """Test choice prompting with number selection."""
        choices = ['Option A', 'Option B', 'Option C']
        result = self.cli.prompt_choice("Select an option", choices)
        self.assertEqual(result, "Option B")
    
    @patch('builtins.input', return_value='')
    @patch('builtins.print')
    def test_prompt_choice_with_default(self, mock_print, mock_input):
        """Test choice prompting with default selection."""
        choices = ['Option A', 'Option B', 'Option C']
        result = self.cli.prompt_choice("Select an option", choices, default=1)
        self.assertEqual(result, "Option A")
    
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    @patch('builtins.print')
    def test_prompt_choice_cancelled(self, mock_print, mock_input):
        """Test choice prompting cancellation."""
        choices = ['Option A', 'Option B']
        result = self.cli.prompt_choice("Select an option", choices)
        self.assertIsNone(result)
    
    @patch('time.time', side_effect=[0, 0.5, 1.0, 1.5, 2.1])
    @patch('time.sleep')
    @patch('builtins.print')
    def test_display_spinner(self, mock_print, mock_sleep, mock_time):
        """Test spinner display."""
        self.cli.display_spinner("Processing", duration=2.0)
        # Verify that spinner characters were displayed
        self.assertTrue(mock_print.called)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_step_progress(self, mock_stdout):
        """Test step progress display."""
        self.cli.display_step_progress(3, 5, "Setup Database", "completed")
        output = mock_stdout.getvalue()
        self.assertIn("✅ Step 3/5: Setup Database (60%)", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_help_section(self, mock_stdout):
        """Test help section display."""
        items = ["First item", "Second item", "Third item"]
        self.cli.display_help_section("Available Commands", items)
        output = mock_stdout.getvalue()
        
        self.assertIn("Available Commands:", output)
        self.assertIn("• First item", output)
        self.assertIn("• Second item", output)
        self.assertIn("• Third item", output)
    
    @patch.object(BaseCLI, 'prompt_yes_no', return_value=True)
    @patch('builtins.print')
    def test_confirm_action_confirmed(self, mock_print, mock_prompt):
        """Test action confirmation when user confirms."""
        result = self.cli.confirm_action("delete all data", "This cannot be undone")
        self.assertTrue(result)
        mock_prompt.assert_called_once_with("Are you sure you want to continue?", default=False)
    
    @patch.object(BaseCLI, 'prompt_yes_no', return_value=False)
    @patch('builtins.print')
    def test_confirm_action_cancelled(self, mock_print, mock_prompt):
        """Test action confirmation when user cancels."""
        result = self.cli.confirm_action("delete all data")
        self.assertFalse(result)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_table(self, mock_stdout):
        """Test table display."""
        headers = ["Name", "Status", "Progress"]
        rows = [
            ["Project A", "Active", "75%"],
            ["Project B", "Complete", "100%"]
        ]
        
        self.cli.display_table(headers, rows, "Project Status")
        output = mock_stdout.getvalue()
        
        self.assertIn("Project Status", output)
        self.assertIn("Name", output)
        self.assertIn("Status", output)
        self.assertIn("Progress", output)
        self.assertIn("Project A", output)
        self.assertIn("Project B", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_table_empty(self, mock_stdout):
        """Test table display with no data."""
        headers = ["Name", "Status"]
        rows = []
        
        self.cli.display_table(headers, rows)
        output = mock_stdout.getvalue()
        self.assertIn("No data to display.", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_info(self, mock_stdout):
        """Test info display."""
        self.cli.display_info("This is an informational message")
        output = mock_stdout.getvalue()
        self.assertIn("ℹ️  This is an informational message", output)


class TestWorkflowCLI(unittest.TestCase):
    """Test cases for WorkflowCLI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cli = WorkflowCLI()
    
    def test_parser_setup(self):
        """Test that parser is properly set up with all commands."""
        # Test that subparsers are created
        self.assertIsNotNone(self.cli.parser._subparsers)
        
        # Test help output contains expected commands
        help_output = self.cli.parser.format_help()
        expected_commands = ['start', 'resume', 'progress', 'validate', 'list', 'reset']
        
        for command in expected_commands:
            self.assertIn(command, help_output)
    
    def test_version_argument(self):
        """Test version argument."""
        with self.assertRaises(SystemExit):
            self.cli.parser.parse_args(['--version'])
    
    @patch('src.cli.workflow_cli.WorkflowCore')
    @patch('src.cli.workflow_cli.ProgressStore')
    @patch('src.cli.workflow_cli.ConfigManager')
    def test_initialize_services(self, mock_config, mock_progress_store, mock_workflow_core):
        """Test service initialization."""
        args = argparse.Namespace(config=None)
        self.cli._initialize_services(args)
        
        mock_config.assert_called_once_with('config.json')
        mock_progress_store.assert_called_once()
        mock_workflow_core.assert_called_once()
    
    @patch.object(WorkflowCLI, '_initialize_services')
    @patch.object(WorkflowCLI, '_handle_start_command', return_value=0)
    def test_execute_start_command(self, mock_handle_start, mock_init):
        """Test start command execution."""
        args = argparse.Namespace(command='start', project='test-project', config=None)
        result = self.cli.execute_command(args)
        
        self.assertEqual(result, 0)
        mock_init.assert_called_once_with(args)
        mock_handle_start.assert_called_once_with(args)
    
    @patch.object(WorkflowCLI, '_initialize_services')
    @patch.object(WorkflowCLI, '_handle_resume_command', return_value=0)
    def test_execute_resume_command(self, mock_handle_resume, mock_init):
        """Test resume command execution."""
        args = argparse.Namespace(command='resume', project='test-project')
        result = self.cli.execute_command(args)
        
        self.assertEqual(result, 0)
        mock_init.assert_called_once_with(args)
        mock_handle_resume.assert_called_once_with(args)
    
    @patch.object(WorkflowCLI, '_initialize_services')
    @patch.object(WorkflowCLI, '_handle_progress_command', return_value=0)
    def test_execute_progress_command(self, mock_handle_progress, mock_init):
        """Test progress command execution."""
        args = argparse.Namespace(command='progress', project='test-project', detailed=False)
        result = self.cli.execute_command(args)
        
        self.assertEqual(result, 0)
        mock_init.assert_called_once_with(args)
        mock_handle_progress.assert_called_once_with(args)
    
    @patch.object(WorkflowCLI, '_initialize_services')
    @patch.object(WorkflowCLI, '_handle_validate_command', return_value=0)
    def test_execute_validate_command(self, mock_handle_validate, mock_init):
        """Test validate command execution."""
        args = argparse.Namespace(command='validate', project='test-project')
        result = self.cli.execute_command(args)
        
        self.assertEqual(result, 0)
        mock_init.assert_called_once_with(args)
        mock_handle_validate.assert_called_once_with(args)
    
    @patch.object(WorkflowCLI, '_initialize_services')
    @patch.object(WorkflowCLI, '_handle_list_command', return_value=0)
    def test_execute_list_command(self, mock_handle_list, mock_init):
        """Test list command execution."""
        args = argparse.Namespace(command='list')
        result = self.cli.execute_command(args)
        
        self.assertEqual(result, 0)
        mock_init.assert_called_once_with(args)
        mock_handle_list.assert_called_once_with(args)
    
    @patch.object(WorkflowCLI, '_initialize_services')
    @patch.object(WorkflowCLI, '_handle_reset_command', return_value=0)
    def test_execute_reset_command(self, mock_handle_reset, mock_init):
        """Test reset command execution."""
        args = argparse.Namespace(command='reset', project='test-project', confirm=False)
        result = self.cli.execute_command(args)
        
        self.assertEqual(result, 0)
        mock_init.assert_called_once_with(args)
        mock_handle_reset.assert_called_once_with(args)
    
    @patch.object(WorkflowCLI, '_initialize_services')
    def test_execute_no_command(self, mock_init):
        """Test execution with no command shows help."""
        args = argparse.Namespace(command=None)
        with patch.object(self.cli.parser, 'print_help') as mock_help:
            result = self.cli.execute_command(args)
            self.assertEqual(result, 0)
            mock_help.assert_called_once()
    
    @patch('builtins.input', return_value='1')
    @patch('builtins.print')
    def test_prompt_project_selection(self, mock_print, mock_input):
        """Test project selection prompt."""
        result = self.cli._prompt_project_selection()
        self.assertEqual(result, "ev-analysis-project")
    
    @patch.object(WorkflowCLI, 'prompt_choice', return_value='ev-analysis-project')
    def test_prompt_project_selection_by_name(self, mock_prompt_choice):
        """Test project selection by choice method."""
        result = self.cli._prompt_project_selection()
        self.assertEqual(result, "ev-analysis-project")
        mock_prompt_choice.assert_called_once()
    
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    @patch('builtins.print')
    def test_prompt_project_selection_cancelled(self, mock_print, mock_input):
        """Test project selection cancellation."""
        result = self.cli._prompt_project_selection()
        self.assertIsNone(result)
    
    def test_get_status_icon(self):
        """Test status icon mapping."""
        self.assertEqual(self.cli._get_status_icon('completed'), '✅')
        self.assertEqual(self.cli._get_status_icon('in_progress'), '⏳')
        self.assertEqual(self.cli._get_status_icon('failed'), '❌')
        self.assertEqual(self.cli._get_status_icon('pending'), '⏸️')
        self.assertEqual(self.cli._get_status_icon('unknown'), '❓')
        self.assertEqual(self.cli._get_status_icon(None), '❓')
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_next_steps(self, mock_stdout):
        """Test next steps display."""
        next_step = {
            'title': 'Setup Project',
            'description': 'Initialize project structure',
            'actions': ['Create repository', 'Download dataset']
        }
        
        self.cli._display_next_steps(next_step)
        output = mock_stdout.getvalue()
        
        self.assertIn("Setup Project", output)
        self.assertIn("Initialize project structure", output)
        self.assertIn("Create repository", output)
        self.assertIn("Download dataset", output)
    
    def test_display_next_steps_none(self):
        """Test next steps display with None input."""
        # Should not raise exception
        self.cli._display_next_steps(None)
    
    @patch('src.cli.workflow_cli.ProgressStore')
    @patch('builtins.print')
    def test_handle_start_command_with_project(self, mock_print, mock_progress_store):
        """Test start command with project specified."""
        # Setup mocks
        mock_progress_instance = Mock()
        mock_progress_instance.has_progress.return_value = False
        mock_progress_store.return_value = mock_progress_instance
        
        self.cli.progress_store = mock_progress_instance
        
        args = argparse.Namespace(project='test-project', config=None)
        result = self.cli._handle_start_command(args)
        
        self.assertEqual(result, 0)
        mock_progress_instance.save_progress.assert_called_once()
    
    @patch('src.cli.workflow_cli.ProgressStore')
    @patch.object(WorkflowCLI, 'prompt_yes_no', return_value=False)
    @patch('builtins.print')
    def test_handle_start_command_existing_project_no_restart(self, mock_print, mock_prompt, mock_progress_store):
        """Test start command with existing project, user chooses not to restart."""
        # Setup mocks
        mock_progress_instance = Mock()
        mock_progress_instance.has_progress.return_value = True
        mock_progress_store.return_value = mock_progress_instance
        
        self.cli.progress_store = mock_progress_instance
        
        args = argparse.Namespace(project='test-project', config=None)
        result = self.cli._handle_start_command(args)
        
        self.assertEqual(result, 0)
        mock_prompt.assert_called_once()
    
    @patch('src.cli.workflow_cli.ProgressStore')
    @patch('builtins.print')
    def test_handle_resume_command_success(self, mock_print, mock_progress_store):
        """Test successful resume command."""
        # Setup mocks
        mock_progress_instance = Mock()
        mock_progress_instance.has_progress.return_value = True
        mock_progress_instance.load_progress.return_value = {
            'project_name': 'test-project',
            'current_step': 2,
            'status': 'in_progress'
        }
        mock_progress_store.return_value = mock_progress_instance
        
        self.cli.progress_store = mock_progress_instance
        
        args = argparse.Namespace(project='test-project')
        result = self.cli._handle_resume_command(args)
        
        self.assertEqual(result, 0)
        mock_progress_instance.load_progress.assert_called_once_with('test-project')
    
    @patch('src.cli.workflow_cli.ProgressStore')
    def test_handle_resume_command_no_project(self, mock_progress_store):
        """Test resume command with no existing project."""
        # Setup mocks
        mock_progress_instance = Mock()
        mock_progress_instance.has_progress.return_value = False
        mock_progress_store.return_value = mock_progress_instance
        
        self.cli.progress_store = mock_progress_instance
        
        args = argparse.Namespace(project='nonexistent-project')
        result = self.cli._handle_resume_command(args)
        
        self.assertEqual(result, 1)
    
    @patch('src.cli.workflow_cli.ProgressStore')
    @patch('builtins.print')
    def test_handle_progress_command_specific_project(self, mock_print, mock_progress_store):
        """Test progress command for specific project."""
        # Setup mocks
        mock_progress_instance = Mock()
        mock_progress_instance.has_progress.return_value = True
        mock_progress_instance.load_progress.return_value = {
            'project_name': 'test-project',
            'current_step': 2,
            'progress_percentage': 40.0
        }
        mock_progress_store.return_value = mock_progress_instance
        
        self.cli.progress_store = mock_progress_instance
        
        args = argparse.Namespace(project='test-project', detailed=False)
        result = self.cli._handle_progress_command(args)
        
        self.assertEqual(result, 0)
        mock_progress_instance.load_progress.assert_called_once_with('test-project')
    
    @patch('src.cli.workflow_cli.ProgressStore')
    @patch('builtins.print')
    def test_handle_list_command_with_projects(self, mock_print, mock_progress_store):
        """Test list command with existing projects."""
        # Setup mocks
        mock_progress_instance = Mock()
        mock_progress_instance.list_projects.return_value = [
            {'name': 'project1', 'status': 'in_progress', 'progress': 50.0},
            {'name': 'project2', 'status': 'completed', 'progress': 100.0}
        ]
        mock_progress_store.return_value = mock_progress_instance
        
        self.cli.progress_store = mock_progress_instance
        
        args = argparse.Namespace()
        result = self.cli._handle_list_command(args)
        
        self.assertEqual(result, 0)
        mock_progress_instance.list_projects.assert_called_once()
    
    @patch('src.cli.workflow_cli.ProgressStore')
    @patch.object(WorkflowCLI, 'display_info')
    def test_handle_list_command_no_projects(self, mock_display_info, mock_progress_store):
        """Test list command with no projects."""
        # Setup mocks
        mock_progress_instance = Mock()
        mock_progress_instance.list_projects.return_value = []
        mock_progress_store.return_value = mock_progress_instance
        
        self.cli.progress_store = mock_progress_instance
        
        args = argparse.Namespace()
        result = self.cli._handle_list_command(args)
        
        self.assertEqual(result, 0)
        mock_display_info.assert_called_with("No projects found.")
    
    @patch('src.cli.workflow_cli.ProgressStore')
    @patch.object(WorkflowCLI, 'prompt_yes_no', return_value=True)
    def test_handle_reset_command_confirmed(self, mock_prompt, mock_progress_store):
        """Test reset command with user confirmation."""
        # Setup mocks
        mock_progress_instance = Mock()
        mock_progress_instance.has_progress.return_value = True
        mock_progress_store.return_value = mock_progress_instance
        
        self.cli.progress_store = mock_progress_instance
        
        args = argparse.Namespace(project='test-project', confirm=False)
        result = self.cli._handle_reset_command(args)
        
        self.assertEqual(result, 0)
        mock_progress_instance.reset_progress.assert_called_once_with('test-project')
    
    @patch('src.cli.workflow_cli.ProgressStore')
    def test_handle_reset_command_with_confirm_flag(self, mock_progress_store):
        """Test reset command with --confirm flag."""
        # Setup mocks
        mock_progress_instance = Mock()
        mock_progress_instance.has_progress.return_value = True
        mock_progress_store.return_value = mock_progress_instance
        
        self.cli.progress_store = mock_progress_instance
        
        args = argparse.Namespace(project='test-project', confirm=True)
        result = self.cli._handle_reset_command(args)
        
        self.assertEqual(result, 0)
        mock_progress_instance.reset_progress.assert_called_once_with('test-project')
    
    def test_get_current_timestamp(self):
        """Test timestamp generation."""
        timestamp = self.cli._get_current_timestamp()
        self.assertIsInstance(timestamp, str)
        self.assertRegex(timestamp, r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    
    def test_get_next_step_info(self):
        """Test next step information retrieval."""
        step_1 = self.cli._get_next_step_info(1)
        self.assertIsNotNone(step_1)
        self.assertEqual(step_1['title'], 'Project Setup')
        self.assertIn('actions', step_1)
        
        step_5 = self.cli._get_next_step_info(5)
        self.assertIsNotNone(step_5)
        self.assertEqual(step_5['title'], 'LMS Submission')
        
        step_invalid = self.cli._get_next_step_info(99)
        self.assertIsNone(step_invalid)
    
    def test_validate_project_name(self):
        """Test project name validation."""
        # Valid project names
        self.assertTrue(self.cli._validate_project_name("valid-project"))
        self.assertTrue(self.cli._validate_project_name("project_123"))
        self.assertTrue(self.cli._validate_project_name("MyProject"))
        
        # Invalid project names
        self.assertFalse(self.cli._validate_project_name(""))  # Empty
        self.assertFalse(self.cli._validate_project_name("ab"))  # Too short
        self.assertFalse(self.cli._validate_project_name("a" * 51))  # Too long
        self.assertFalse(self.cli._validate_project_name("project with spaces"))  # Spaces
        self.assertFalse(self.cli._validate_project_name("project@special"))  # Special chars
        self.assertFalse(self.cli._validate_project_name(None))  # None
    
    def test_get_step_title(self):
        """Test step title retrieval."""
        self.assertEqual(self.cli._get_step_title(1), "Project Setup")
        self.assertEqual(self.cli._get_step_title(2), "Dataset Download")
        self.assertEqual(self.cli._get_step_title(3), "Code Development")
        self.assertEqual(self.cli._get_step_title(4), "GitHub Repository")
        self.assertEqual(self.cli._get_step_title(5), "LMS Submission")
        self.assertEqual(self.cli._get_step_title(99), "Step 99")  # Unknown step


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI components."""
    
    @patch('src.cli.workflow_cli.WorkflowCore')
    @patch('src.cli.workflow_cli.ProgressStore')
    @patch('src.cli.workflow_cli.ConfigManager')
    def test_full_start_workflow(self, mock_config, mock_progress_store, mock_workflow_core):
        """Test full start workflow integration."""
        # Setup mocks
        mock_progress_instance = Mock()
        mock_progress_instance.has_progress.return_value = False
        mock_progress_store.return_value = mock_progress_instance
        
        mock_workflow_instance = Mock()
        mock_workflow_core.return_value = mock_workflow_instance
        
        cli = WorkflowCLI()
        
        # Test start command
        with patch('sys.stdout', new_callable=StringIO):
            result = cli.run(['start', '--project', 'test-project'])
            self.assertEqual(result, 0)
            # Verify that progress was saved for the project
            mock_progress_instance.save_progress.assert_called_once()
    
    @patch('src.cli.workflow_cli.WorkflowCore')
    @patch('src.cli.workflow_cli.ProgressStore')
    @patch('src.cli.workflow_cli.ConfigManager')
    def test_error_handling(self, mock_config, mock_progress_store, mock_workflow_core):
        """Test error handling in CLI."""
        # Setup mocks to raise exception
        mock_workflow_core.side_effect = Exception("Test error")
        
        cli = WorkflowCLI()
        
        with patch('sys.stdout', new_callable=StringIO):
            result = cli.run(['start', '--project', 'test-project'])
            self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()