import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Test direct import
try:
    import src.services.github_service as gh
    print("Module imported successfully")
    
    # Check if GitHubService exists
    if hasattr(gh, 'GitHubService'):
        print("GitHubService class found")
        service = gh.GitHubService()
        print("GitHubService instantiated successfully")
    else:
        print("GitHubService class not found")
        print("Available attributes:", [attr for attr in dir(gh) if not attr.startswith('_')])
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()