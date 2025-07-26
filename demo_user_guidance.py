#!/usr/bin/env python3
"""
Demonstration of the enhanced User Guidance System.
This script shows the various features and capabilities of the user guidance system.
"""

from src.services.user_guidance import UserGuidanceService


def demonstrate_error_guidance():
    """Demonstrate error guidance functionality."""
    print("=" * 60)
    print("ERROR GUIDANCE DEMONSTRATION")
    print("=" * 60)
    
    guidance_service = UserGuidanceService()
    
    # Test various error scenarios
    error_scenarios = [
        {
            'message': 'GitHub API rate limit exceeded',
            'context': {'user_id': 'demo_user', 'project': 'ev-analysis'}
        },
        {
            'message': 'Notebook validation failed: missing data analysis section',
            'context': {'notebook_path': '/project/analysis.ipynb', 'step_id': 3}
        },
        {
            'message': 'LMS submission failed: connection timeout',
            'context': {'submission_id': '12345', 'deadline': '2024-01-15'}
        },
        {
            'message': 'Some unknown error occurred',
            'context': None
        }
    ]
    
    for i, scenario in enumerate(error_scenarios, 1):
        print(f"\n{i}. Error Scenario:")
        print(f"   Message: {scenario['message']}")
        if scenario['context']:
            print(f"   Context: {scenario['context']}")
        
        guidance = guidance_service.get_error_guidance(
            scenario['message'], 
            scenario['context']
        )
        
        formatted_guidance = guidance_service.format_guidance_message(guidance)
        print(f"\n   Guidance:\n{formatted_guidance}")
        print("-" * 50)


def demonstrate_help_system():
    """Demonstrate help system functionality."""
    print("\n" + "=" * 60)
    print("HELP SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    guidance_service = UserGuidanceService()
    
    # List available help topics
    print("\nAvailable Help Topics:")
    topics = guidance_service.list_help_topics()
    for topic in topics:
        print(f"  - {topic}")
    
    # Show detailed help for a specific topic
    print(f"\nDetailed Help for 'getting-started':")
    help_info = guidance_service.get_help_for_topic('getting-started')
    if help_info:
        print(f"Title: {help_info['title']}")
        print(f"Description: {help_info['description']}")
        for section in help_info['sections']:
            print(f"\n  {section['title']}:")
            for item in section['content']:
                print(f"    • {item}")


def demonstrate_troubleshooting_guides():
    """Demonstrate troubleshooting guides functionality."""
    print("\n" + "=" * 60)
    print("TROUBLESHOOTING GUIDES DEMONSTRATION")
    print("=" * 60)
    
    guidance_service = UserGuidanceService()
    
    # List available guides
    print("\nAvailable Troubleshooting Guides:")
    guides = guidance_service.list_troubleshooting_guides()
    for guide in guides:
        print(f"  - {guide}")
    
    # Show detailed guide
    print(f"\nDetailed Guide for 'github-authentication':")
    guide_info = guidance_service.get_troubleshooting_guide('github-authentication')
    if guide_info:
        print(f"Title: {guide_info['title']}")
        print(f"Description: {guide_info['description']}")
        
        if 'symptoms' in guide_info:
            print("\nSymptoms:")
            for symptom in guide_info['symptoms']:
                print(f"  • {symptom}")
        
        if 'diagnosis_steps' in guide_info:
            print("\nDiagnosis Steps:")
            for step in guide_info['diagnosis_steps']:
                print(f"  • {step}")
        
        if 'solutions' in guide_info:
            print("\nSolutions:")
            for solution in guide_info['solutions']:
                print(f"  • {solution}")


def demonstrate_interactive_help():
    """Demonstrate interactive help functionality."""
    print("\n" + "=" * 60)
    print("INTERACTIVE HELP DEMONSTRATION")
    print("=" * 60)
    
    guidance_service = UserGuidanceService()
    
    # Test interactive help search
    search_queries = ['github', 'notebook', 'submission']
    
    for query in search_queries:
        print(f"\nSearching for: '{query}'")
        results = guidance_service.get_interactive_help(query)
        
        print(f"Total results: {results['total_results']}")
        
        if results['help_topics']:
            print("  Help Topics:")
            for topic in results['help_topics']:
                print(f"    • {topic['title']} ({topic['name']})")
        
        if results['troubleshooting_guides']:
            print("  Troubleshooting Guides:")
            for guide in results['troubleshooting_guides']:
                print(f"    • {guide['title']} ({guide['name']})")
        
        if results['error_guidance']:
            print("  Error Guidance:")
            for error in results['error_guidance']:
                print(f"    • {error['title']} ({error['code']})")


def demonstrate_quick_help():
    """Demonstrate quick help functionality."""
    print("\n" + "=" * 60)
    print("QUICK HELP DEMONSTRATION")
    print("=" * 60)
    
    guidance_service = UserGuidanceService()
    
    # Test quick help for common topics
    quick_topics = ['start', 'github', 'notebook', 'validation', 'unknown_topic']
    
    for topic in quick_topics:
        help_text = guidance_service.get_quick_help(topic)
        print(f"\nQuick help for '{topic}':")
        print(f"  {help_text}")


def demonstrate_next_steps():
    """Demonstrate next steps suggestions."""
    print("\n" + "=" * 60)
    print("NEXT STEPS SUGGESTIONS DEMONSTRATION")
    print("=" * 60)
    
    guidance_service = UserGuidanceService()
    
    # Test next steps for different workflow states
    print("\nNormal workflow progression:")
    for step in range(1, 6):
        suggestions = guidance_service.suggest_next_steps(step, error_occurred=False)
        print(f"\nStep {step} suggestions:")
        for suggestion in suggestions:
            print(f"  • {suggestion}")
    
    print("\nError recovery suggestions:")
    error_suggestions = guidance_service.suggest_next_steps(3, error_occurred=True)
    print("When error occurs at step 3:")
    for suggestion in error_suggestions:
        print(f"  • {suggestion}")


def main():
    """Main demonstration function."""
    print("AICTE Project Workflow - User Guidance System Demo")
    print("This demonstration shows the enhanced user guidance capabilities.")
    
    try:
        demonstrate_error_guidance()
        demonstrate_help_system()
        demonstrate_troubleshooting_guides()
        demonstrate_interactive_help()
        demonstrate_quick_help()
        demonstrate_next_steps()
        
        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("The user guidance system provides comprehensive support for:")
        print("• Intelligent error classification and resolution")
        print("• Detailed help topics and documentation")
        print("• Step-by-step troubleshooting guides")
        print("• Interactive help search")
        print("• Quick help for common issues")
        print("• Context-aware next step suggestions")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()