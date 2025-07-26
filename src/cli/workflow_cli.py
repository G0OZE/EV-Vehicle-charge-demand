"""
Main CLI interface for the AICTE Project Workflow Automation.
"""
import argparse
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path

from .base_cli import BaseCLI
from ..services.workflow_core import WorkflowCore
from ..services.progress_store import ProgressStore
from ..utils.config import ConfigManager


class WorkflowCLI(BaseCLI):
    """Main CLI interface for workflow automation."""
    
    def __init__(self):
        super().__init__()
        self.workflow_core = None
        self.progress_store = None
        self.config = None
    
    def setup_parser(self) -> None:
        """Setup command line argument parser."""
        self.parser.add_argument(
            '--version', 
            action='version', 
            version='AICTE Workflow Automation 1.0.0'
        )
        
        # Create subparsers for different commands
        subparsers = self.parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )
        
        # Start workflow command
        start_parser = subparsers.add_parser(
            'start',
            help='Start a new project workflow'
        )
        start_parser.add_argument(
            '--project',
            type=str,
            help='Project name or ID to initialize'
        )
        start_parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
        
        # Resume workflow command
        resume_parser = subparsers.add_parser(
            'resume',
            help='Resume an interrupted workflow'
        )
        resume_parser.add_argument(
            '--project',
            type=str,
            help='Project name to resume'
        )
        
        # Show progress command
        progress_parser = subparsers.add_parser(
            'progress',
            help='Show current workflow progress'
        )
        progress_parser.add_argument(
            '--project',
            type=str,
            help='Project name to check progress for'
        )
        progress_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed progress information'
        )
        
        # Validate submission command
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate submission completeness'
        )
        validate_parser.add_argument(
            '--project',
            type=str,
            help='Project name to validate'
        )
        
        # List projects command
        list_parser = subparsers.add_parser(
            'list',
            help='List available projects and their status'
        )
        
        # Reset workflow command
        reset_parser = subparsers.add_parser(
            'reset',
            help='Reset workflow progress for a project'
        )
        reset_parser.add_argument(
            'project',
            type=str,
            help='Project name to reset'
        )
        reset_parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt'
        )
    
    def execute_command(self, args: argparse.Namespace) -> int:
        """Execute the parsed command."""
        try:
            # Initialize services
            self._initialize_services(args)
            
            # Route to appropriate command handler
            if args.command == 'start':
                return self._handle_start_command(args)
            elif args.command == 'resume':
                return self._handle_resume_command(args)
            elif args.command == 'progress':
                return self._handle_progress_command(args)
            elif args.command == 'validate':
                return self._handle_validate_command(args)
            elif args.command == 'list':
                return self._handle_list_command(args)
            elif args.command == 'reset':
                return self._handle_reset_command(args)
            else:
                self.parser.print_help()
                return 0
                
        except Exception as e:
            self.display_error(f"Command execution failed: {str(e)}")
            return 1
    
    def _initialize_services(self, args: argparse.Namespace) -> None:
        """Initialize required services."""
        # Load configuration
        config_path = getattr(args, 'config', None)
        self.config = ConfigManager(config_path or "config.json")
        
        # Initialize progress store
        self.progress_store = ProgressStore()
        
        # Initialize workflow core
        self.workflow_core = WorkflowCore(
            config=self.config,
            progress_store=self.progress_store
        )
    
    def _handle_start_command(self, args: argparse.Namespace) -> int:
        """Handle start workflow command."""
        self.display_info("🚀 Starting AICTE Project Workflow...")
        
        # Get project selection
        project_name = args.project
        if not project_name:
            project_name = self._prompt_project_selection()
            if not project_name:
                self.display_error("No project selected. Aborting.")
                return 1
        
        # Validate project name
        if not self._validate_project_name(project_name):
            self.display_error(f"Invalid project name: {project_name}")
            return 1
        
        # Check if project already exists
        if self.progress_store.has_progress(project_name):
            if not self.confirm_action(
                f"restart workflow for project '{project_name}'",
                "This will overwrite existing progress"
            ):
                self.display_info("Use 'resume' command to continue existing workflow.")
                return 0
        
        try:
            # Show initialization progress
            self.display_spinner(f"Initializing project: {project_name}", duration=1.5)
            
            # Create initial workflow state
            workflow_state = {
                'project_name': project_name,
                'current_step': 1,
                'completed_steps': [],
                'total_steps': 5,
                'status': 'in_progress',
                'progress_percentage': 0.0,
                'created_at': self._get_current_timestamp(),
                'updated_at': self._get_current_timestamp()
            }
            
            # Save initial progress
            self.progress_store.save_progress(project_name, workflow_state)
            
            # Display success and next steps
            self.display_success(f"Workflow started for project: {project_name}")
            
            # Show initial step progress
            self.display_step_progress(1, 5, "Project Setup", "pending")
            
            next_step = {
                'title': 'Project Setup',
                'description': 'Complete Skills4Future portal login and profile setup',
                'actions': [
                    'Login to Skills4Future portal',
                    'Complete your profile information',
                    'Mark attendance as present',
                    'Select your project dataset'
                ]
            }
            self._display_next_steps(next_step)
            
            self.display_help_section("Next Steps", [
                f"Use 'resume --project {project_name}' to continue the workflow",
                f"Use 'progress --project {project_name}' to check status",
                "Use 'list' to see all projects"
            ])
            
            return 0
                
        except Exception as e:
            self.display_error(f"Failed to start workflow: {str(e)}")
            return 1
    
    def _handle_resume_command(self, args: argparse.Namespace) -> int:
        """Handle resume workflow command."""
        self.display_info("🔄 Resuming AICTE Project Workflow...")
        
        # Get project selection
        project_name = args.project
        if not project_name:
            project_name = self._prompt_existing_project_selection()
            if not project_name:
                self.display_error("No project selected. Aborting.")
                return 1
        
        # Check if project exists
        if not self.progress_store.has_progress(project_name):
            self.display_error(
                f"No existing workflow found for project: {project_name}",
                ["Use 'start' command to begin a new workflow",
                 "Use 'list' command to see available projects"]
            )
            return 1
        
        try:
            # Show loading progress
            self.display_spinner(f"Loading project: {project_name}", duration=1.0)
            
            # Load existing progress
            progress_data = self.progress_store.load_progress(project_name)
            current_step = progress_data.get('current_step', 1)
            total_steps = progress_data.get('total_steps', 5)
            
            self.display_info(f"Resuming project: {project_name}")
            
            # Show current step progress
            self.display_step_progress(current_step, total_steps, 
                                     self._get_step_title(current_step), "in_progress")
            
            # Update timestamp
            progress_data['updated_at'] = self._get_current_timestamp()
            self.progress_store.save_progress(project_name, progress_data)
            
            # Display current status
            self._display_project_progress(progress_data, detailed=True)
            
            # Determine next step based on current progress
            next_step = self._get_next_step_info(current_step)
            if next_step:
                self._display_next_steps(next_step)
            
            self.display_help_section("Available Actions", [
                f"Use 'progress --project {project_name} --detailed' for detailed status",
                f"Use 'validate --project {project_name}' to check submission readiness",
                "Continue with the actions listed above"
            ])
            
            self.display_success(f"Workflow resumed for project: {project_name}")
            return 0
                
        except Exception as e:
            self.display_error(f"Failed to resume workflow: {str(e)}")
            return 1
    
    def _handle_progress_command(self, args: argparse.Namespace) -> int:
        """Handle show progress command."""
        project_name = args.project
        
        if project_name:
            # Show progress for specific project
            if not self.progress_store.has_progress(project_name):
                self.display_error(f"No workflow found for project: {project_name}")
                return 1
            
            progress_data = self.progress_store.load_progress(project_name)
            self._display_project_progress(progress_data, args.detailed)
        else:
            # Show progress for all projects
            self._display_all_projects_progress(args.detailed)
        
        return 0
    
    def _handle_validate_command(self, args: argparse.Namespace) -> int:
        """Handle validate submission command."""
        project_name = args.project
        if not project_name:
            project_name = self._prompt_existing_project_selection()
            if not project_name:
                self.display_error("No project selected. Aborting.")
                return 1
        
        try:
            result = self.workflow_core.validate_submission(project_name)
            
            if result.get('valid'):
                self.display_success("✅ Submission validation passed!")
                print(f"Repository URL: {result.get('repository_url', 'N/A')}")
            else:
                self.display_warning("❌ Submission validation failed")
                issues = result.get('issues', [])
                if issues:
                    print("Issues found:")
                    for i, issue in enumerate(issues, 1):
                        print(f"  {i}. {issue}")
                return 1
            
            return 0
            
        except Exception as e:
            self.display_error(f"Validation failed: {str(e)}")
            return 1
    
    def _handle_list_command(self, args: argparse.Namespace) -> int:
        """Handle list projects command."""
        projects = self.progress_store.list_projects()
        
        if not projects:
            self.display_info("No projects found.")
            return 0
        
        # Prepare table data
        headers = ["Status", "Project Name", "Progress", "Last Updated"]
        rows = []
        
        for project in projects:
            status_icon = self._get_status_icon(project.get('status'))
            rows.append([
                status_icon,
                project['name'],
                f"{project.get('progress', 0):.1f}%",
                project.get('updated_at', 'Unknown')
            ])
        
        self.display_table(headers, rows, "📋 Available Projects")
        print(f"Total projects: {len(projects)}")
        return 0
    
    def _handle_reset_command(self, args: argparse.Namespace) -> int:
        """Handle reset workflow command."""
        project_name = args.project
        
        if not self.progress_store.has_progress(project_name):
            self.display_error(f"No workflow found for project: {project_name}")
            return 1
        
        # Confirm reset unless --confirm flag is used
        if not args.confirm:
            if not self.confirm_action(
                f"reset workflow for '{project_name}'",
                "This will delete all progress and cannot be undone"
            ):
                self.display_info("Reset cancelled.")
                return 0
        
        try:
            self.display_spinner("Resetting workflow progress", duration=1.0)
            self.progress_store.reset_progress(project_name)
            self.display_success(f"Workflow reset for project: {project_name}")
            return 0
        except Exception as e:
            self.display_error(f"Failed to reset workflow: {str(e)}")
            return 1
    
    def _prompt_project_selection(self) -> Optional[str]:
        """Prompt user to select a project."""
        # This would typically load from a configuration or API
        available_projects = [
            "ev-analysis-project",
            "data-visualization-project", 
            "machine-learning-basics",
            "web-scraping-project"
        ]
        
        return self.prompt_choice("📚 Select a project to work with:", available_projects)
    
    def _prompt_existing_project_selection(self) -> Optional[str]:
        """Prompt user to select from existing projects."""
        projects = self.progress_store.list_projects()
        
        if not projects:
            self.display_info("No existing projects found.")
            return None
        
        # Create formatted choices for display
        project_choices = []
        for project in projects:
            status_icon = self._get_status_icon(project.get('status'))
            progress = project.get('progress', 0)
            choice_text = f"{status_icon} {project['name']} ({progress:.1f}%)"
            project_choices.append(choice_text)
        
        selected_choice = self.prompt_choice("📋 Select an existing project:", project_choices)
        
        if selected_choice:
            # Extract project name from the formatted choice
            for i, choice in enumerate(project_choices):
                if choice == selected_choice:
                    return projects[i]['name']
        
        return None
    
    def _display_next_steps(self, next_step: Optional[Dict[str, Any]]) -> None:
        """Display next steps information."""
        if not next_step:
            return
        
        print(f"\n📋 Next Step: {next_step.get('title', 'Unknown')}")
        if next_step.get('description'):
            print(f"   {next_step['description']}")
        
        if next_step.get('actions'):
            print("\n   Actions required:")
            for action in next_step['actions']:
                print(f"   • {action}")
    
    def _display_project_progress(self, progress_data: Dict[str, Any], detailed: bool = False) -> None:
        """Display progress for a specific project."""
        self.display_status(progress_data)
        
        if detailed and progress_data.get('steps'):
            print("\n📋 Step Details:")
            for step in progress_data['steps']:
                status_icon = "✅" if step.get('completed') else "⏳"
                print(f"  {status_icon} {step.get('title', 'Unknown Step')}")
                if step.get('error'):
                    print(f"     ❌ Error: {step['error']}")
    
    def _display_all_projects_progress(self, detailed: bool = False) -> None:
        """Display progress for all projects."""
        projects = self.progress_store.list_projects()
        
        if not projects:
            print("No projects found.")
            return
        
        print("\n📊 All Projects Progress:")
        print("=" * 60)
        
        for project in projects:
            if detailed:
                progress_data = self.progress_store.load_progress(project['name'])
                self._display_project_progress(progress_data, detailed=False)
                print("-" * 40)
            else:
                status_icon = self._get_status_icon(project.get('status'))
                print(f"{status_icon} {project['name']:<25} {project.get('progress', 0):>6.1f}%")
    
    def _get_status_icon(self, status: Optional[str]) -> str:
        """Get status icon for display."""
        status_icons = {
            'completed': '✅',
            'in_progress': '⏳',
            'failed': '❌',
            'pending': '⏸️'
        }
        return status_icons.get(status, '❓')
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _validate_project_name(self, project_name: str) -> bool:
        """Validate project name format and availability."""
        if not project_name:
            return False
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', project_name):
            return False
        
        # Check length constraints
        if len(project_name) < 3 or len(project_name) > 50:
            return False
        
        return True
    
    def _get_step_title(self, step_number: int) -> str:
        """Get the title for a specific step number."""
        step_titles = {
            1: "Project Setup",
            2: "Dataset Download", 
            3: "Code Development",
            4: "GitHub Repository",
            5: "LMS Submission"
        }
        return step_titles.get(step_number, f"Step {step_number}")
    
    def _get_next_step_info(self, current_step: int) -> Optional[Dict[str, Any]]:
        """Get information about the next step based on current progress."""
        step_info = {
            1: {
                'title': 'Project Setup',
                'description': 'Complete Skills4Future portal login and profile setup',
                'actions': [
                    'Login to Skills4Future portal',
                    'Complete your profile information',
                    'Mark attendance as present',
                    'Select your project dataset'
                ]
            },
            2: {
                'title': 'Dataset Download',
                'description': 'Download and prepare project dataset',
                'actions': [
                    'Download the project dataset',
                    'Verify dataset integrity',
                    'Create Google Colab notebook',
                    'Upload dataset to Colab environment'
                ]
            },
            3: {
                'title': 'Code Development',
                'description': 'Implement project code and analysis',
                'actions': [
                    'Populate notebook with code templates',
                    'Implement data analysis logic',
                    'Add visualizations and insights',
                    'Test and validate results'
                ]
            },
            4: {
                'title': 'GitHub Repository',
                'description': 'Create and populate GitHub repository',
                'actions': [
                    'Create GitHub repository',
                    'Initialize with README',
                    'Upload notebook and dataset',
                    'Generate repository URL'
                ]
            },
            5: {
                'title': 'LMS Submission',
                'description': 'Submit project to LMS portal',
                'actions': [
                    'Validate submission completeness',
                    'Generate submission summary',
                    'Submit repository link to LMS',
                    'Confirm submission receipt'
                ]
            }
        }
        
        return step_info.get(current_step)


def main():
    """Main entry point for the CLI."""
    cli = WorkflowCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())