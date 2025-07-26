"""
CLI help system for AICTE project workflow.
Provides interactive help, troubleshooting guides, and error assistance.
"""
import argparse
from typing import List, Optional, Dict, Any
from ..services.user_guidance import UserGuidanceService, ErrorCategory, ErrorSeverity
from .base_cli import BaseCLI


class HelpSystemCLI(BaseCLI):
    """CLI interface for help system and troubleshooting."""
    
    def __init__(self):
        super().__init__()
        self.guidance_service = UserGuidanceService()
    
    def setup_parser(self) -> None:
        """Setup command line argument parser for help system."""
        self.parser.add_argument(
            '--version', 
            action='version', 
            version='AICTE Workflow Help System 1.0.0'
        )
        
        # Create subparsers for different help commands
        subparsers = self.parser.add_subparsers(
            dest='command',
            help='Available help commands',
            metavar='COMMAND'
        )
        
        # Help topics command
        help_parser = subparsers.add_parser(
            'topic',
            help='Get help on specific topics'
        )
        help_parser.add_argument(
            'topic_name',
            nargs='?',
            help='Name of help topic (use "list" to see all topics)'
        )
        
        # Troubleshooting command
        trouble_parser = subparsers.add_parser(
            'troubleshoot',
            help='Get troubleshooting guides'
        )
        trouble_parser.add_argument(
            'issue',
            nargs='?',
            help='Issue to troubleshoot (use "list" to see all guides)'
        )
        
        # Error help command
        error_parser = subparsers.add_parser(
            'error',
            help='Get help for specific error messages'
        )
        error_parser.add_argument(
            'error_message',
            help='Error message or error code'
        )
        error_parser.add_argument(
            '--context',
            help='Additional context (JSON format)'
        )
        
        # Interactive help command
        interactive_parser = subparsers.add_parser(
            'interactive',
            help='Start interactive help session'
        )
    
    def execute_command(self, args: argparse.Namespace) -> int:
        """Execute the parsed help command."""
        try:
            if args.command == 'topic':
                return self._handle_topic_command(args)
            elif args.command == 'troubleshoot':
                return self._handle_troubleshoot_command(args)
            elif args.command == 'error':
                return self._handle_error_command(args)
            elif args.command == 'interactive':
                return self._handle_interactive_command(args)
            else:
                self._show_main_help()
                return 0
                
        except Exception as e:
            self.display_error(f"Help command failed: {str(e)}")
            return 1
    
    def _handle_topic_command(self, args: argparse.Namespace) -> int:
        """Handle help topic command."""
        if not args.topic_name or args.topic_name == 'list':
            self._list_help_topics()
            return 0
        
        topic_info = self.guidance_service.get_help_for_topic(args.topic_name)
        if not topic_info:
            self.display_error(f"Help topic '{args.topic_name}' not found.")
            self._list_help_topics()
            return 1
        
        self._display_help_topic(topic_info)
        return 0
    
    def _handle_troubleshoot_command(self, args: argparse.Namespace) -> int:
        """Handle troubleshooting command."""
        if not args.issue or args.issue == 'list':
            self._list_troubleshooting_guides()
            return 0
        
        guide = self.guidance_service.get_troubleshooting_guide(args.issue)
        if not guide:
            self.display_error(f"Troubleshooting guide '{args.issue}' not found.")
            self._list_troubleshooting_guides()
            return 1
        
        self._display_troubleshooting_guide(guide)
        return 0
    
    def _handle_error_command(self, args: argparse.Namespace) -> int:
        """Handle error help command."""
        context = None
        if args.context:
            try:
                import json
                context = json.loads(args.context)
            except json.JSONDecodeError:
                self.display_warning("Invalid context JSON format, ignoring context.")
        
        guidance = self.guidance_service.get_error_guidance(args.error_message, context)
        formatted_guidance = self.guidance_service.format_guidance_message(guidance)
        
        print(formatted_guidance)
        return 0
    
    def _handle_interactive_command(self, args: argparse.Namespace) -> int:
        """Handle interactive help session."""
        self.display_info("🤖 Welcome to Interactive Help!")
        print("Type 'exit' to quit, 'menu' to see options.\n")
        
        while True:
            try:
                user_input = input("Help> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    self.display_info("Goodbye!")
                    break
                elif user_input.lower() in ['menu', 'help', '?']:
                    self._show_interactive_menu()
                elif user_input.lower().startswith('topic '):
                    topic_name = user_input[6:].strip()
                    self._show_topic_interactive(topic_name)
                elif user_input.lower().startswith('troubleshoot '):
                    issue = user_input[13:].strip()
                    self._show_troubleshoot_interactive(issue)
                elif user_input.lower().startswith('error '):
                    error_msg = user_input[6:].strip()
                    self._show_error_interactive(error_msg)
                elif user_input.lower() == 'topics':
                    self._list_help_topics()
                elif user_input.lower() == 'guides':
                    self._list_troubleshooting_guides()
                else:
                    # Try to interpret as error message or search term
                    self._search_help(user_input)
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit.")
            except EOFError:
                break
        
        return 0
    
    def _show_main_help(self) -> None:
        """Show main help overview."""
        print("🔧 AICTE Workflow Help System")
        print("=" * 40)
        print()
        print("Available Commands:")
        print("  topic [name]        - Get help on specific topics")
        print("  troubleshoot [issue] - Get troubleshooting guides")
        print("  error <message>     - Get help for error messages")
        print("  interactive         - Start interactive help session")
        print()
        print("Quick Start:")
        print("  help topic getting-started")
        print("  help troubleshoot workflow-stuck")
        print("  help error 'connection failed'")
        print()
        print("For more information, use 'help topic list' to see all available topics.")
    
    def _list_help_topics(self) -> None:
        """List all available help topics."""
        topics = self.guidance_service.list_help_topics()
        
        print("📚 Available Help Topics:")
        print("-" * 30)
        for topic in sorted(topics):
            topic_info = self.guidance_service.get_help_for_topic(topic)
            if topic_info:
                print(f"  {topic:<20} - {topic_info.get('description', 'No description')}")
        print()
        print("Use 'help topic <name>' to get detailed information.")
    
    def _list_troubleshooting_guides(self) -> None:
        """List all available troubleshooting guides."""
        guides = self.guidance_service.list_troubleshooting_guides()
        
        print("🔍 Available Troubleshooting Guides:")
        print("-" * 40)
        for guide in sorted(guides):
            guide_info = self.guidance_service.get_troubleshooting_guide(guide)
            if guide_info:
                print(f"  {guide:<25} - {guide_info.get('description', 'No description')}")
        print()
        print("Use 'help troubleshoot <issue>' to get detailed guide.")
    
    def _display_help_topic(self, topic_info: Dict[str, Any]) -> None:
        """Display detailed help topic information."""
        print(f"📖 {topic_info['title']}")
        print("=" * len(topic_info['title']) + 3)
        print()
        print(topic_info['description'])
        print()
        
        for section in topic_info.get('sections', []):
            print(f"## {section['title']}")
            print("-" * (len(section['title']) + 3))
            
            if isinstance(section['content'], list):
                for item in section['content']:
                    print(f"  • {item}")
            else:
                print(f"  {section['content']}")
            print()
    
    def _display_troubleshooting_guide(self, guide: Dict[str, Any]) -> None:
        """Display troubleshooting guide."""
        print(f"🔧 {guide['title']}")
        print("=" * len(guide['title']) + 3)
        print()
        print(guide['description'])
        print()
        
        if guide.get('symptoms'):
            print("🔍 Symptoms:")
            for symptom in guide['symptoms']:
                print(f"  • {symptom}")
            print()
        
        if guide.get('diagnosis_steps'):
            print("🔬 Diagnosis Steps:")
            for i, step in enumerate(guide['diagnosis_steps'], 1):
                print(f"  {i}. {step}")
            print()
        
        if guide.get('solutions'):
            print("✅ Solutions:")
            for i, solution in enumerate(guide['solutions'], 1):
                print(f"  {i}. {solution}")
            print()
    
    def _show_interactive_menu(self) -> None:
        """Show interactive help menu."""
        print("🤖 Interactive Help Menu:")
        print("-" * 25)
        print("  topic <name>        - Get help on specific topic")
        print("  troubleshoot <issue> - Get troubleshooting guide")
        print("  error <message>     - Get error help")
        print("  topics              - List all help topics")
        print("  guides              - List troubleshooting guides")
        print("  menu                - Show this menu")
        print("  exit                - Quit interactive help")
        print()
        print("You can also type any error message or search term.")
    
    def _show_topic_interactive(self, topic_name: str) -> None:
        """Show help topic in interactive mode."""
        if not topic_name:
            self._list_help_topics()
            return
        
        topic_info = self.guidance_service.get_help_for_topic(topic_name)
        if topic_info:
            self._display_help_topic(topic_info)
        else:
            print(f"❌ Topic '{topic_name}' not found.")
            self._list_help_topics()
    
    def _show_troubleshoot_interactive(self, issue: str) -> None:
        """Show troubleshooting guide in interactive mode."""
        if not issue:
            self._list_troubleshooting_guides()
            return
        
        guide = self.guidance_service.get_troubleshooting_guide(issue)
        if guide:
            self._display_troubleshooting_guide(guide)
        else:
            print(f"❌ Troubleshooting guide '{issue}' not found.")
            self._list_troubleshooting_guides()
    
    def _show_error_interactive(self, error_msg: str) -> None:
        """Show error help in interactive mode."""
        if not error_msg:
            print("❌ Please provide an error message.")
            return
        
        guidance = self.guidance_service.get_error_guidance(error_msg)
        formatted_guidance = self.guidance_service.format_guidance_message(guidance)
        print(formatted_guidance)
    
    def _search_help(self, search_term: str) -> None:
        """Search for help based on user input."""
        print(f"🔍 Searching for help with: '{search_term}'")
        print()
        
        # Try as error message first
        guidance = self.guidance_service.get_error_guidance(search_term)
        if guidance.error_code != "GENERIC":
            print("Found matching error guidance:")
            formatted_guidance = self.guidance_service.format_guidance_message(guidance)
            print(formatted_guidance)
            return
        
        # Search in help topics
        topics = self.guidance_service.list_help_topics()
        matching_topics = [topic for topic in topics if search_term.lower() in topic.lower()]
        
        if matching_topics:
            print("Found matching help topics:")
            for topic in matching_topics:
                topic_info = self.guidance_service.get_help_for_topic(topic)
                if topic_info:
                    print(f"  • {topic} - {topic_info.get('description', 'No description')}")
            print()
            print("Use 'topic <name>' to get detailed information.")
            return
        
        # Search in troubleshooting guides
        guides = self.guidance_service.list_troubleshooting_guides()
        matching_guides = [guide for guide in guides if search_term.lower() in guide.lower()]
        
        if matching_guides:
            print("Found matching troubleshooting guides:")
            for guide in matching_guides:
                guide_info = self.guidance_service.get_troubleshooting_guide(guide)
                if guide_info:
                    print(f"  • {guide} - {guide_info.get('description', 'No description')}")
            print()
            print("Use 'troubleshoot <issue>' to get detailed guide.")
            return
        
        # No matches found
        print("❌ No specific help found for your search term.")
        print("Try one of these options:")
        print("  • Use 'topics' to see all available help topics")
        print("  • Use 'guides' to see all troubleshooting guides")
        print("  • Be more specific with your search term")
        print("  • Try describing the error or issue you're experiencing")


def main():
    """Main entry point for the help system CLI."""
    help_cli = HelpSystemCLI()
    return help_cli.run()


if __name__ == '__main__':
    import sys
    sys.exit(main())