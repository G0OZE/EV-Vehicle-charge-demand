"""
Base CLI interface for the AICTE Project Workflow Automation.
"""
import argparse
import sys
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseCLI(ABC):
    """Abstract base class for CLI interfaces."""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="AICTE Project Workflow Automation Tool"
        )
        self.setup_parser()
    
    @abstractmethod
    def setup_parser(self) -> None:
        """Setup command line argument parser."""
        pass
    
    @abstractmethod
    def execute_command(self, args: argparse.Namespace) -> int:
        """Execute the parsed command."""
        pass
    
    def run(self, argv: Optional[List[str]] = None) -> int:
        """Parse arguments and execute command."""
        try:
            args = self.parser.parse_args(argv)
            return self.execute_command(args)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def prompt_user(self, message: str, default: Optional[str] = None) -> str:
        """Prompt user for input with optional default value."""
        if default:
            prompt = f"{message} [{default}]: "
        else:
            prompt = f"{message}: "
        
        try:
            response = input(prompt).strip()
            return response if response else (default or "")
        except (EOFError, KeyboardInterrupt):
            return default or ""
    
    def prompt_yes_no(self, message: str, default: bool = False) -> bool:
        """Prompt user for yes/no confirmation."""
        default_str = "Y/n" if default else "y/N"
        response = self.prompt_user(f"{message} ({default_str})")
        
        if not response:
            return default
        
        return response.lower().startswith('y')
    
    def display_progress(self, current: int, total: int, message: str = "") -> None:
        """Display progress bar."""
        if total == 0:
            percentage = 0
        else:
            percentage = (current / total) * 100
        
        bar_length = 40
        filled_length = int(bar_length * current // total) if total > 0 else 0
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f'\r{message} |{bar}| {percentage:.1f}% ({current}/{total})', end='')
        
        if current == total:
            print()  # New line when complete
    
    def display_status(self, status_data: Dict[str, Any]) -> None:
        """Display workflow status information."""
        print("\n=== Workflow Status ===")
        print(f"Project: {status_data.get('project_name', 'Unknown')}")
        print(f"Current Step: {status_data.get('current_step', 'N/A')}")
        print(f"Progress: {status_data.get('progress_percentage', 0):.1f}%")
        print(f"Completed Steps: {status_data.get('completed_steps', 0)}/{status_data.get('total_steps', 0)}")
        
        if status_data.get('github_repo'):
            print(f"GitHub Repository: {status_data['github_repo']}")
        
        if status_data.get('submission_link'):
            print(f"Submission Link: {status_data['submission_link']}")
        
        print(f"Last Updated: {status_data.get('updated_at', 'Unknown')}")
        print("=" * 25)
    
    def display_error(self, error_message: str, suggestions: Optional[List[str]] = None) -> None:
        """Display error message with optional suggestions."""
        print(f"\n❌ Error: {error_message}")
        
        if suggestions:
            print("\n💡 Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        print()
    
    def display_success(self, message: str) -> None:
        """Display success message."""
        print(f"\n✅ {message}\n")
    
    def display_warning(self, message: str) -> None:
        """Display warning message."""
        print(f"\n⚠️  Warning: {message}\n")
    
    def prompt_choice(self, message: str, choices: List[str], default: Optional[int] = None) -> Optional[str]:
        """Prompt user to select from a list of choices."""
        print(f"\n{message}")
        for i, choice in enumerate(choices, 1):
            marker = " (default)" if default == i else ""
            print(f"  {i}. {choice}{marker}")
        
        while True:
            try:
                if default:
                    prompt = f"\nSelect option (1-{len(choices)}) [{default}]: "
                else:
                    prompt = f"\nSelect option (1-{len(choices)}): "
                
                response = input(prompt).strip()
                
                if not response and default:
                    return choices[default - 1]
                
                if response.isdigit():
                    idx = int(response) - 1
                    if 0 <= idx < len(choices):
                        return choices[idx]
                
                print("Invalid selection. Please try again.")
                
            except (EOFError, KeyboardInterrupt):
                return None
    
    def display_spinner(self, message: str, duration: float = 2.0) -> None:
        """Display a spinner animation for long-running operations."""
        spinner_chars = "|/-\\"
        end_time = time.time() + duration
        i = 0
        
        try:
            while time.time() < end_time:
                print(f"\r{message} {spinner_chars[i % len(spinner_chars)]}", end="", flush=True)
                time.sleep(0.1)
                i += 1
            print(f"\r{message} ✓", flush=True)
        except KeyboardInterrupt:
            print(f"\r{message} ✗ (cancelled)", flush=True)
    
    def display_step_progress(self, step_number: int, total_steps: int, step_title: str, status: str = "in_progress") -> None:
        """Display progress for individual workflow steps."""
        status_icons = {
            "completed": "✅",
            "in_progress": "⏳",
            "failed": "❌",
            "pending": "⏸️"
        }
        
        icon = status_icons.get(status, "❓")
        percentage = (step_number / total_steps) * 100
        
        print(f"{icon} Step {step_number}/{total_steps}: {step_title} ({percentage:.0f}%)")
    
    def display_help_section(self, title: str, items: List[str]) -> None:
        """Display a formatted help section."""
        print(f"\n{title}:")
        print("-" * len(title))
        for item in items:
            print(f"  • {item}")
        print()
    
    def confirm_action(self, action: str, warning: Optional[str] = None) -> bool:
        """Confirm a potentially destructive action."""
        print(f"\n⚠️  You are about to: {action}")
        
        if warning:
            print(f"⚠️  Warning: {warning}")
        
        return self.prompt_yes_no("Are you sure you want to continue?", default=False)
    
    def display_table(self, headers: List[str], rows: List[List[str]], title: Optional[str] = None) -> None:
        """Display data in a formatted table."""
        if title:
            print(f"\n{title}")
            print("=" * len(title))
        
        if not rows:
            print("No data to display.")
            return
        
        # Calculate column widths
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Print header
        header_row = " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers))
        print(f"\n{header_row}")
        print("-" * len(header_row))
        
        # Print rows
        for row in rows:
            formatted_row = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            print(formatted_row)
        print()
    
    def display_info(self, message: str) -> None:
        """Display informational message."""
        print(f"\nℹ️  {message}\n")