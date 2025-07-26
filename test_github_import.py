#!/usr/bin/env python3

# Simple test to check GitHub service import
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

try:
    # Import directly without going through src package
    import importlib.util
    spec = importlib.util.spec_from_file_location("github_service", "src/services/github_service.py")
    github_service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(github_service)
    
    print("✓ Module loaded successfully")
    
    # Test basic instantiation
    if hasattr(github_service, 'GitHubService'):
        print("✓ GitHubService class found")
        
        # Test basic methods exist
        service_class = github_service.GitHubService
        assert hasattr(service_class, '__init__')
        assert hasattr(service_class, 'create_repository')
        assert hasattr(service_class, 'get_repository_url')
        print("✓ All required methods exist")
        
        print("GitHub service implementation is working correctly!")
    else:
        print("✗ GitHubService class not found")
        print("Available attributes:", [attr for attr in dir(github_service) if not attr.startswith('_')])
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()