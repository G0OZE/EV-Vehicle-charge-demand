"""
Validation service for AICTE project workflow.
"""
import os
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from urllib.parse import urlparse

# Optional imports with fallbacks
try:
    import nbformat
    HAS_NBFORMAT = True
except ImportError:
    HAS_NBFORMAT = False
    nbformat = None

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None

from ..models.interfaces import ValidationService as ValidationServiceInterface
from ..models.workflow_models import ProjectData, WorkflowState


class ValidationService(ValidationServiceInterface):
    """Service for validating workflow steps and requirements."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize validation service with configuration."""
        self.config = config or {}
        self.required_files = [
            'README.md',
            'requirements.txt',
            'dataset.csv'
        ]
        self.required_notebook_sections = [
            'data_loading',
            'data_preprocessing', 
            'model_training',
            'evaluation'
        ]
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met for starting workflow."""
        try:
            # Check Python environment
            if not self._check_python_environment():
                return False
            
            # Check required packages
            if not self._check_required_packages():
                return False
            
            # Check internet connectivity
            if not self._check_internet_connectivity():
                return False
            
            # Check GitHub configuration
            if not self._check_github_config():
                return False
            
            return True
            
        except Exception as e:
            print(f"Error checking prerequisites: {e}")
            return False
    
    def validate_notebook_content(self, notebook_path: str) -> bool:
        """Validate notebook content completeness."""
        try:
            if not os.path.exists(notebook_path):
                print(f"Notebook file not found: {notebook_path}")
                return False
            
            if not HAS_NBFORMAT:
                print("nbformat package not available, skipping detailed notebook validation")
                return True
            
            # Load and parse notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = nbformat.read(f, as_version=4)
            
            # Check notebook structure
            if not self._validate_notebook_structure(notebook):
                return False
            
            # Check required sections
            if not self._validate_notebook_sections(notebook):
                return False
            
            # Check code completeness
            if not self._validate_code_completeness(notebook):
                return False
            
            # Check outputs exist
            if not self._validate_notebook_outputs(notebook):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating notebook content: {e}")
            return False
    
    def verify_repository_structure(self, repo_path: str) -> bool:
        """Verify repository has proper structure."""
        try:
            repo_path = Path(repo_path)
            
            if not repo_path.exists():
                print(f"Repository path does not exist: {repo_path}")
                return False
            
            # Check required files exist
            missing_files = []
            for required_file in self.required_files:
                file_path = repo_path / required_file
                if not file_path.exists():
                    missing_files.append(required_file)
            
            if missing_files:
                print(f"Missing required files: {', '.join(missing_files)}")
                return False
            
            # Validate README content
            if not self._validate_readme_content(repo_path / 'README.md'):
                return False
            
            # Validate dataset file
            if not self._validate_dataset_file(repo_path / 'dataset.csv'):
                return False
            
            # Check for notebook file
            notebook_files = list(repo_path.glob('*.ipynb'))
            if not notebook_files:
                print("No notebook file found in repository")
                return False
            
            # Validate notebook if present
            for notebook_file in notebook_files:
                if not self.validate_notebook_content(str(notebook_file)):
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error verifying repository structure: {e}")
            return False
    
    def confirm_submission_readiness(self) -> bool:
        """Final validation before submission."""
        try:
            # Check all validation steps
            validation_steps = [
                ("Prerequisites", self.check_prerequisites),
                ("Repository structure", lambda: self.verify_repository_structure(".")),
            ]
            
            failed_steps = []
            for step_name, validation_func in validation_steps:
                try:
                    if not validation_func():
                        failed_steps.append(step_name)
                except Exception as e:
                    print(f"Error in {step_name} validation: {e}")
                    failed_steps.append(step_name)
            
            if failed_steps:
                print(f"Submission not ready. Failed validation steps: {', '.join(failed_steps)}")
                return False
            
            print("All validation checks passed. Submission is ready!")
            return True
            
        except Exception as e:
            print(f"Error confirming submission readiness: {e}")
            return False
    
    def validate_project_data(self, project_data: ProjectData) -> Tuple[bool, List[str]]:
        """Validate project data completeness and correctness."""
        errors = []
        
        try:
            # Validate URLs are accessible
            if not self._check_url_accessibility(project_data.dataset_url):
                errors.append(f"Dataset URL is not accessible: {project_data.dataset_url}")
            
            if not self._check_url_accessibility(project_data.code_template_url):
                errors.append(f"Code template URL is not accessible: {project_data.code_template_url}")
            
            # Validate deadline is reasonable
            from datetime import datetime, timedelta
            if project_data.deadline < datetime.now() + timedelta(hours=1):
                errors.append("Project deadline is too soon (less than 1 hour from now)")
            
            # Validate requirements are specific enough
            if len(project_data.requirements) < 3:
                errors.append("Project should have at least 3 specific requirements")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Error validating project data: {e}")
            return False, errors
    
    def validate_workflow_state(self, workflow_state: WorkflowState) -> Tuple[bool, List[str]]:
        """Validate workflow state consistency."""
        errors = []
        
        try:
            # Check step progression logic
            if workflow_state.current_step < max(workflow_state.completed_steps, default=0):
                errors.append("Current step should not be less than the highest completed step")
            
            # Check project data consistency
            if workflow_state.project_data:
                is_valid, project_errors = self.validate_project_data(workflow_state.project_data)
                if not is_valid:
                    errors.extend(project_errors)
            
            # Check GitHub repo format if present
            if workflow_state.github_repo:
                if not re.match(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$', workflow_state.github_repo):
                    errors.append("GitHub repository format should be 'owner/repo'")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Error validating workflow state: {e}")
            return False, errors
    
    # Private helper methods
    
    def _check_python_environment(self) -> bool:
        """Check if Python environment is properly set up."""
        try:
            import sys
            if sys.version_info < (3, 7):
                print("Python 3.7 or higher is required")
                return False
            return True
        except Exception:
            return False
    
    def _check_required_packages(self) -> bool:
        """Check if required Python packages are installed."""
        required_packages = [
            'json',  # Built-in, should always be available
            'os',    # Built-in, should always be available
        ]
        
        # Optional packages - warn but don't fail
        optional_packages = [
            'requests',
            'nbformat',
            'pandas',
            'numpy'
        ]
        
        missing_optional = []
        for package in optional_packages:
            try:
                __import__(package)
            except ImportError:
                missing_optional.append(package)
        
        if missing_optional:
            print(f"Optional packages not available (some features may be limited): {', '.join(missing_optional)}")
        
        return True  # Don't fail for missing optional packages
    
    def _check_internet_connectivity(self) -> bool:
        """Check if internet connection is available."""
        if not HAS_REQUESTS:
            print("requests package not available, skipping internet connectivity check")
            return True
        
        try:
            response = requests.get('https://httpbin.org/status/200', timeout=5)
            return response.status_code == 200
        except Exception:
            print("No internet connectivity detected")
            return False
    
    def _check_github_config(self) -> bool:
        """Check if GitHub configuration is available."""
        # Check for GitHub token in environment or config
        github_token = os.environ.get('GITHUB_TOKEN') or self.config.get('github_token')
        if not github_token:
            print("GitHub token not found. Please set GITHUB_TOKEN environment variable")
            return False
        
        return True
    
    def _validate_notebook_structure(self, notebook) -> bool:
        """Validate basic notebook structure."""
        if not notebook.cells:
            print("Notebook has no cells")
            return False
        
        # Check for at least one code cell
        code_cells = [cell for cell in notebook.cells if cell.cell_type == 'code']
        if not code_cells:
            print("Notebook has no code cells")
            return False
        
        return True
    
    def _validate_notebook_sections(self, notebook) -> bool:
        """Validate notebook has required sections."""
        # Extract all text from markdown cells
        markdown_text = ""
        for cell in notebook.cells:
            if cell.cell_type == 'markdown':
                markdown_text += cell.source.lower() + "\n"
        
        # Check for required sections
        missing_sections = []
        for section in self.required_notebook_sections:
            if section.replace('_', ' ') not in markdown_text and section not in markdown_text:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"Notebook missing required sections: {', '.join(missing_sections)}")
            return False
        
        return True
    
    def _validate_code_completeness(self, notebook) -> bool:
        """Validate that code cells are not empty or placeholder."""
        code_cells = [cell for cell in notebook.cells if cell.cell_type == 'code']
        
        empty_cells = 0
        placeholder_patterns = [
            r'#\s*TODO',
            r'#\s*FIXME',
            r'#\s*Your code here',
            r'pass\s*$',
            r'^\s*$'
        ]
        
        for cell in code_cells:
            source = cell.source.strip()
            if not source:
                empty_cells += 1
                continue
            
            # Check for placeholder patterns
            for pattern in placeholder_patterns:
                if re.search(pattern, source, re.IGNORECASE | re.MULTILINE):
                    empty_cells += 1
                    break
        
        # Allow some empty cells but not too many
        if empty_cells > len(code_cells) * 0.5:
            print(f"Too many empty or placeholder code cells: {empty_cells}/{len(code_cells)}")
            return False
        
        return True
    
    def _validate_notebook_outputs(self, notebook) -> bool:
        """Validate that notebook has been executed with outputs."""
        code_cells = [cell for cell in notebook.cells if cell.cell_type == 'code']
        
        cells_with_output = 0
        for cell in code_cells:
            if cell.get('outputs') or cell.get('execution_count'):
                cells_with_output += 1
        
        # Require at least 50% of code cells to have outputs
        if cells_with_output < len(code_cells) * 0.5:
            print(f"Notebook appears not to be executed. Only {cells_with_output}/{len(code_cells)} cells have outputs")
            return False
        
        return True
    
    def _validate_readme_content(self, readme_path: Path) -> bool:
        """Validate README file content."""
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content.strip()) < 100:
                print("README file is too short (less than 100 characters)")
                return False
            
            # Check for required sections
            required_sections = ['description', 'installation', 'usage']
            content_lower = content.lower()
            
            missing_sections = []
            for section in required_sections:
                if section not in content_lower:
                    missing_sections.append(section)
            
            if missing_sections:
                print(f"README missing sections: {', '.join(missing_sections)}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating README: {e}")
            return False
    
    def _validate_dataset_file(self, dataset_path: Path) -> bool:
        """Validate dataset file format and content."""
        try:
            if not dataset_path.exists():
                print(f"Dataset file not found: {dataset_path}")
                return False
            
            # Check file size (should not be empty, but not too large)
            file_size = dataset_path.stat().st_size
            if file_size == 0:
                print("Dataset file is empty")
                return False
            
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                print("Dataset file is too large (>100MB)")
                return False
            
            # Try to read as CSV if pandas is available
            if HAS_PANDAS:
                try:
                    df = pd.read_csv(dataset_path, nrows=5)  # Just read first 5 rows for validation
                    
                    if df.empty:
                        print("Dataset file has no data")
                        return False
                    
                    if len(df.columns) < 2:
                        print("Dataset should have at least 2 columns")
                        return False
                        
                except Exception as e:
                    print(f"Dataset file is not a valid CSV: {e}")
                    return False
            else:
                print("pandas not available, skipping detailed CSV validation")
            
            return True
            
        except Exception as e:
            print(f"Error validating dataset file: {e}")
            return False
    
    def _check_url_accessibility(self, url: str) -> bool:
        """Check if URL is accessible."""
        if not HAS_REQUESTS:
            return False
        
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            return response.status_code < 400
        except Exception:
            return False