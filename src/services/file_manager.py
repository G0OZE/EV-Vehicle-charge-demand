"""
File management utilities for dataset handling and notebook operations.
"""
import os
import csv
import json
import shutil
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from urllib.parse import urlparse
import tempfile
import zipfile
from datetime import datetime


class FileManager:
    """Handles local file operations, dataset downloads, and notebook generation."""
    
    def __init__(self, base_directory: str = "./projects"):
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(parents=True, exist_ok=True)
        self.temp_directory = Path(tempfile.gettempdir()) / "aicte_workflow"
        self.temp_directory.mkdir(parents=True, exist_ok=True)
    
    def download_dataset(self, dataset_url: str, project_name: str) -> Dict[str, Any]:
        """
        Download dataset from URL and save to project directory.
        
        Args:
            dataset_url: URL to download dataset from
            project_name: Name of the project for organizing files
            
        Returns:
            Dict containing download result information
        """
        try:
            # Validate URL
            if not self._is_valid_url(dataset_url):
                return {
                    'success': False,
                    'error': 'Invalid dataset URL provided'
                }
            
            # Create project directory
            project_dir = self.base_directory / project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract filename from URL
            parsed_url = urlparse(dataset_url)
            filename = Path(parsed_url.path).name
            if not filename:
                filename = "dataset.csv"  # Default filename
            
            # Download file
            response = requests.get(dataset_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save to project directory
            file_path = project_dir / filename
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Validate downloaded file
            validation_result = self.validate_dataset_file(str(file_path))
            
            return {
                'success': True,
                'file_path': str(file_path),
                'filename': filename,
                'file_size': file_path.stat().st_size,
                'validation': validation_result
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Failed to download dataset: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error during download: {str(e)}'
            }
    
    def validate_dataset_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate dataset file format and content.
        
        Args:
            file_path: Path to the dataset file
            
        Returns:
            Dict containing validation results
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'valid': False,
                    'error': 'File does not exist'
                }
            
            # Check file extension
            if file_path.suffix.lower() not in ['.csv', '.json', '.xlsx', '.txt']:
                return {
                    'valid': False,
                    'error': f'Unsupported file format: {file_path.suffix}'
                }
            
            # Validate CSV files
            if file_path.suffix.lower() == '.csv':
                return self._validate_csv_file(file_path)
            
            # Validate JSON files
            elif file_path.suffix.lower() == '.json':
                return self._validate_json_file(file_path)
            
            # Basic validation for other formats
            else:
                return {
                    'valid': True,
                    'format': file_path.suffix.lower(),
                    'size': file_path.stat().st_size,
                    'message': 'Basic validation passed'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation failed: {str(e)}'
            }
    
    def _validate_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate CSV file structure and content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.reader(f, delimiter=delimiter)
                
                # Read header
                header = next(reader)
                if not header:
                    return {
                        'valid': False,
                        'error': 'CSV file has no header row'
                    }
                
                # Count rows and validate structure
                row_count = 0
                column_count = len(header)
                inconsistent_rows = []
                
                for i, row in enumerate(reader, start=2):  # Start from 2 (header is row 1)
                    row_count += 1
                    if len(row) != column_count:
                        inconsistent_rows.append(i)
                    
                    # Stop after checking first 100 rows for performance
                    if row_count >= 100:
                        break
                
                return {
                    'valid': True,
                    'format': 'csv',
                    'columns': header,
                    'column_count': column_count,
                    'row_count': row_count,
                    'delimiter': delimiter,
                    'inconsistent_rows': inconsistent_rows[:10],  # First 10 problematic rows
                    'file_size': file_path.stat().st_size
                }
                
        except UnicodeDecodeError:
            return {
                'valid': False,
                'error': 'File encoding not supported (not UTF-8)'
            }
        except csv.Error as e:
            return {
                'valid': False,
                'error': f'CSV parsing error: {str(e)}'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Unexpected error validating CSV: {str(e)}'
            }
    
    def _validate_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate JSON file structure and content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Analyze JSON structure
            data_type = type(data).__name__
            
            if isinstance(data, list):
                item_count = len(data)
                sample_keys = list(data[0].keys()) if data and isinstance(data[0], dict) else []
            elif isinstance(data, dict):
                item_count = len(data)
                sample_keys = list(data.keys())
            else:
                item_count = 1
                sample_keys = []
            
            return {
                'valid': True,
                'format': 'json',
                'data_type': data_type,
                'item_count': item_count,
                'sample_keys': sample_keys[:10],  # First 10 keys
                'file_size': file_path.stat().st_size
            }
            
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'error': f'Invalid JSON format: {str(e)}'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Unexpected error validating JSON: {str(e)}'
            }
    
    def create_notebook_from_template(self, template_path: str, project_name: str, 
                                    project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Jupyter notebook from template with project-specific content.
        
        Args:
            template_path: Path to notebook template
            project_name: Name of the project
            project_data: Project-specific data to inject into template
            
        Returns:
            Dict containing notebook creation result
        """
        try:
            # Create project directory
            project_dir = self.base_directory / project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate notebook content
            notebook_content = self._generate_notebook_content(project_name, project_data)
            
            # Save notebook
            notebook_path = project_dir / f"{project_name}.ipynb"
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(notebook_content, f, indent=2)
            
            return {
                'success': True,
                'notebook_path': str(notebook_path),
                'filename': f"{project_name}.ipynb"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create notebook: {str(e)}'
            }
    
    def _generate_notebook_content(self, project_name: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Jupyter notebook content with project-specific code."""
        
        # Basic notebook structure
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"# {project_name}\n",
                        "\n",
                        f"**Project Description:** {project_data.get('description', 'AICTE Internship Project')}\n",
                        "\n",
                        f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                        "\n",
                        "## Project Requirements\n",
                        "\n"
                    ] + [f"- {req}\n" for req in project_data.get('requirements', [])]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# Import required libraries\n",
                        "import pandas as pd\n",
                        "import numpy as np\n",
                        "import matplotlib.pyplot as plt\n",
                        "import seaborn as sns\n",
                        "from sklearn.model_selection import train_test_split\n",
                        "from sklearn.preprocessing import StandardScaler\n",
                        "\n",
                        "# Set display options\n",
                        "pd.set_option('display.max_columns', None)\n",
                        "plt.style.use('default')\n",
                        "sns.set_palette('husl')\n"
                    ]
                },
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "## Data Loading and Exploration\n"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# Load the dataset\n",
                        "# TODO: Update the file path to match your dataset\n",
                        "data = pd.read_csv('dataset.csv')\n",
                        "\n",
                        "# Display basic information about the dataset\n",
                        "print(\"Dataset Shape:\", data.shape)\n",
                        "print(\"\\nColumn Names:\")\n",
                        "print(data.columns.tolist())\n",
                        "\n",
                        "# Display first few rows\n",
                        "data.head()\n"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# Data exploration\n",
                        "print(\"Dataset Info:\")\n",
                        "data.info()\n",
                        "\n",
                        "print(\"\\nMissing Values:\")\n",
                        "print(data.isnull().sum())\n",
                        "\n",
                        "print(\"\\nBasic Statistics:\")\n",
                        "data.describe()\n"
                    ]
                },
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "## Data Analysis and Visualization\n"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# TODO: Add your data analysis code here\n",
                        "# Example visualization\n",
                        "plt.figure(figsize=(12, 6))\n",
                        "\n",
                        "# Add your specific analysis based on the dataset\n",
                        "# This is a template - modify according to your project requirements\n",
                        "\n",
                        "plt.tight_layout()\n",
                        "plt.show()\n"
                    ]
                },
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "## Model Development\n"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# TODO: Add your model development code here\n",
                        "# This section should include:\n",
                        "# - Feature selection/engineering\n",
                        "# - Model training\n",
                        "# - Model evaluation\n",
                        "\n",
                        "# Example template:\n",
                        "# X = data.drop('target_column', axis=1)  # Features\n",
                        "# y = data['target_column']  # Target\n",
                        "\n",
                        "# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n"
                    ]
                },
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "## Results and Conclusions\n"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# TODO: Add your results and conclusions here\n",
                        "# Include:\n",
                        "# - Model performance metrics\n",
                        "# - Key insights from the analysis\n",
                        "# - Recommendations or next steps\n"
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "codemirror_mode": {
                        "name": "ipython",
                        "version": 3
                    },
                    "file_extension": ".py",
                    "mimetype": "text/x-python",
                    "name": "python",
                    "nbconvert_exporter": "python",
                    "pygments_lexer": "ipython3",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        return notebook
    
    def prepare_upload_bundle(self, project_name: str) -> Dict[str, Any]:
        """
        Prepare files for upload to GitHub repository.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict containing bundle preparation result
        """
        try:
            project_dir = self.base_directory / project_name
            
            if not project_dir.exists():
                return {
                    'success': False,
                    'error': 'Project directory does not exist'
                }
            
            # Find files to upload
            files_to_upload = []
            
            # Look for notebook files
            for notebook_file in project_dir.glob("*.ipynb"):
                files_to_upload.append({
                    'type': 'notebook',
                    'path': str(notebook_file),
                    'filename': notebook_file.name,
                    'size': notebook_file.stat().st_size
                })
            
            # Look for dataset files
            for data_file in project_dir.glob("*.csv"):
                files_to_upload.append({
                    'type': 'dataset',
                    'path': str(data_file),
                    'filename': data_file.name,
                    'size': data_file.stat().st_size
                })
            
            # Look for other relevant files
            for other_file in project_dir.glob("*.json"):
                files_to_upload.append({
                    'type': 'data',
                    'path': str(other_file),
                    'filename': other_file.name,
                    'size': other_file.stat().st_size
                })
            
            return {
                'success': True,
                'project_directory': str(project_dir),
                'files': files_to_upload,
                'total_files': len(files_to_upload),
                'total_size': sum(f['size'] for f in files_to_upload)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to prepare upload bundle: {str(e)}'
            }
    
    def copy_local_file(self, source_path: str, project_name: str, 
                       new_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Copy a local file to the project directory.
        
        Args:
            source_path: Path to the source file
            project_name: Name of the project
            new_filename: Optional new filename for the copied file
            
        Returns:
            Dict containing copy operation result
        """
        try:
            source_path = Path(source_path)
            
            if not source_path.exists():
                return {
                    'success': False,
                    'error': 'Source file does not exist'
                }
            
            # Create project directory
            project_dir = self.base_directory / project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine destination filename
            filename = new_filename if new_filename else source_path.name
            dest_path = project_dir / filename
            
            # Copy file
            shutil.copy2(source_path, dest_path)
            
            # Validate copied file
            validation_result = self.validate_dataset_file(str(dest_path))
            
            return {
                'success': True,
                'source_path': str(source_path),
                'dest_path': str(dest_path),
                'filename': filename,
                'file_size': dest_path.stat().st_size,
                'validation': validation_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to copy file: {str(e)}'
            }
    
    def get_project_files(self, project_name: str) -> Dict[str, Any]:
        """
        Get list of all files in a project directory.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dict containing project files information
        """
        try:
            project_dir = self.base_directory / project_name
            
            if not project_dir.exists():
                return {
                    'success': False,
                    'error': 'Project directory does not exist'
                }
            
            files = []
            for file_path in project_dir.iterdir():
                if file_path.is_file():
                    files.append({
                        'filename': file_path.name,
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'extension': file_path.suffix,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
            
            return {
                'success': True,
                'project_directory': str(project_dir),
                'files': files,
                'total_files': len(files),
                'total_size': sum(f['size'] for f in files)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get project files: {str(e)}'
            }
    
    def cleanup_temp_files(self) -> bool:
        """Clean up temporary files."""
        try:
            if self.temp_directory.exists():
                shutil.rmtree(self.temp_directory)
                self.temp_directory.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {e}")
            return False
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        if not url or not isinstance(url, str):
            return False
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False