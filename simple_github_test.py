#!/usr/bin/env python3

# Test GitHub service import without package structure
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

try:
    # Try to import the module directly
    import importlib.util
    
    # Load the module
    spec = importlib.util.spec_from_file_location("github_service", "src/services/github_service.py")
    github_module = importlib.util.module_from_spec(spec)
    
    # Execute the module
    spec.loader.exec_module(github_module)
    
    print("Module executed successfully")
    
    # Check what's in the module
    print("Module attributes:", [attr for attr in dir(github_module) if not attr.startswith('_')])
    
    # Try to access the classes
    if hasattr(github_module, 'GitHubService'):
        print("✓ GitHubService found!")
        service_class = getattr(github_module, 'GitHubService')
        print(f"GitHubService class: {service_class}")
    else:
        print("✗ GitHubService not found")
    
    if hasattr(github_module, 'GitHubAPIError'):
        print("✓ GitHubAPIError found!")
    else:
        print("✗ GitHubAPIError not found")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()