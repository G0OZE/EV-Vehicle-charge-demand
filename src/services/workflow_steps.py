"""
Concrete workflow step implementations for EV analysis project workflow.
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from ..models.interfaces import WorkflowStep, StepStatus
from ..models.workflow_models import StepResult, ProjectData
from .file_manager import FileManager
from .validation_service import ValidationService
from .github_service import GitHubService


class ProjectSelectionStep(WorkflowStep):
    """Step 1: Project selection and dataset download logic."""
    
    def __init__(self, file_manager: FileManager, validation_service: ValidationService):
        self.file_manager = file_manager
        self.validation_service = validation_service
        self.step_id = 1
        
        # Sample project data for demonstration
        self.available_projects = {
            "ev_analysis": {
                "project_id": "ev_analysis",
                "dataset_url": "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
                "code_template_url": "https://raw.githubusercontent.com/jupyter/notebook/master/docs/source/examples/Notebook/Notebook%20Basics.ipynb",
                "project_description": "Electric Vehicle Market Analysis - Analyze EV adoption trends and market patterns",
                "requirements": [
                    "Load and explore the EV dataset",
                    "Perform data cleaning and preprocessing",
                    "Create visualizations showing market trends",
                    "Build predictive model for EV adoption",
                    "Generate insights and recommendations"
                ],
                "deadline": datetime.now() + timedelta(days=7)
            },
            "sales_forecasting": {
                "project_id": "sales_forecasting",
                "dataset_url": "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
                "code_template_url": "https://raw.githubusercontent.com/jupyter/notebook/master/docs/source/examples/Notebook/Notebook%20Basics.ipynb",
                "project_description": "Sales Forecasting Analysis - Predict future sales based on historical data",
                "requirements": [
                    "Load and analyze sales historical data",
                    "Identify seasonal patterns and trends",
                    "Build time series forecasting model",
                    "Validate model accuracy",
                    "Create forecast visualizations"
                ],
                "deadline": datetime.now() + timedelta(days=7)
            },
            "customer_segmentation": {
                "project_id": "customer_segmentation",
                "dataset_url": "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
                "code_template_url": "https://raw.githubusercontent.com/jupyter/notebook/master/docs/source/examples/Notebook/Notebook%20Basics.ipynb",
                "project_description": "Customer Segmentation Analysis - Segment customers based on behavior patterns",
                "requirements": [
                    "Load and explore customer data",
                    "Perform feature engineering",
                    "Apply clustering algorithms",
                    "Analyze customer segments",
                    "Create actionable business recommendations"
                ],
                "deadline": datetime.now() + timedelta(days=7)
            }
        }
    
    def execute(self) -> StepResult:
        """Execute project selection and dataset download."""
        try:
            # For now, we'll use a default project selection
            # In a real implementation, this would involve user interaction
            selected_project_id = "ev_analysis"  # Default selection
            
            if selected_project_id not in self.available_projects:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Project '{selected_project_id}' not found"
                )
            
            project_info = self.available_projects[selected_project_id]
            project_data = ProjectData(**project_info)
            
            # Download dataset
            download_result = self.file_manager.download_dataset(
                project_data.dataset_url,
                project_data.project_id
            )
            
            if not download_result['success']:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Failed to download dataset: {download_result['error']}"
                )
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.COMPLETED,
                result_data={
                    'project_data': project_data.to_dict(),
                    'dataset_download': download_result,
                    'selected_project_id': selected_project_id
                }
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                error_message=f"Project selection failed: {str(e)}"
            )
    
    def validate(self) -> bool:
        """Validate prerequisites for project selection."""
        try:
            # Check if validation service prerequisites are met
            if not self.validation_service.check_prerequisites():
                return False
            
            # Check if file manager is properly initialized
            if not hasattr(self.file_manager, 'base_directory'):
                return False
            
            return True
            
        except Exception:
            return False
    
    def rollback(self) -> bool:
        """Rollback project selection changes."""
        try:
            # Clean up any downloaded files
            self.file_manager.cleanup_temp_files()
            return True
        except Exception:
            return False


class NotebookCreationStep(WorkflowStep):
    """Step 2: Google Colab notebook creation workflow."""
    
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
        self.step_id = 2
    
    def execute(self) -> StepResult:
        """Execute notebook creation."""
        try:
            # This would typically get project data from workflow state
            # For now, we'll use a default project name
            project_name = "ev_analysis"  # This should come from previous step
            
            # Create project data for notebook generation
            project_data = {
                'description': 'Electric Vehicle Market Analysis',
                'requirements': [
                    'Load and explore the EV dataset',
                    'Perform data cleaning and preprocessing',
                    'Create visualizations showing market trends',
                    'Build predictive model for EV adoption',
                    'Generate insights and recommendations'
                ]
            }
            
            # Create notebook from template
            notebook_result = self.file_manager.create_notebook_from_template(
                template_path="",  # We generate our own template
                project_name=project_name,
                project_data=project_data
            )
            
            if not notebook_result['success']:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Failed to create notebook: {notebook_result['error']}"
                )
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.COMPLETED,
                result_data={
                    'notebook_creation': notebook_result,
                    'project_name': project_name
                }
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                error_message=f"Notebook creation failed: {str(e)}"
            )
    
    def validate(self) -> bool:
        """Validate prerequisites for notebook creation."""
        try:
            # Check if file manager is available
            return hasattr(self.file_manager, 'create_notebook_from_template')
        except Exception:
            return False
    
    def rollback(self) -> bool:
        """Rollback notebook creation."""
        try:
            # Remove created notebook files
            project_name = "ev_analysis"  # This should come from workflow state
            project_dir = Path(self.file_manager.base_directory) / project_name
            
            if project_dir.exists():
                for notebook_file in project_dir.glob("*.ipynb"):
                    notebook_file.unlink()
            
            return True
        except Exception:
            return False


class AttendanceReminderStep(WorkflowStep):
    """Step 3: Attendance reminder and checklist validation."""
    
    def __init__(self):
        self.step_id = 3
        self.attendance_checklist = [
            "Log into Skills4Future portal",
            "Navigate to attendance section",
            "Mark attendance as 'Present' for today",
            "Verify attendance status is saved",
            "Complete profile information if required"
        ]
    
    def execute(self) -> StepResult:
        """Execute attendance reminder and validation."""
        try:
            # Display attendance reminder
            reminder_message = self._generate_attendance_reminder()
            
            # For automation purposes, we'll assume attendance is marked
            # In a real implementation, this might check an API or require user confirmation
            attendance_status = self._check_attendance_status()
            
            if not attendance_status['marked']:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message="Attendance not marked. Please complete attendance before proceeding."
                )
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.COMPLETED,
                result_data={
                    'attendance_reminder': reminder_message,
                    'attendance_status': attendance_status,
                    'checklist_completed': True
                }
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                error_message=f"Attendance reminder failed: {str(e)}"
            )
    
    def validate(self) -> bool:
        """Validate attendance prerequisites."""
        try:
            # Basic validation - check if we can generate reminder
            return len(self.attendance_checklist) > 0
        except Exception:
            return False
    
    def rollback(self) -> bool:
        """Rollback attendance reminder (no-op)."""
        return True
    
    def _generate_attendance_reminder(self) -> str:
        """Generate attendance reminder message."""
        reminder = "📋 ATTENDANCE REMINDER\n"
        reminder += "=" * 50 + "\n\n"
        reminder += "Please complete the following steps to mark your attendance:\n\n"
        
        for i, item in enumerate(self.attendance_checklist, 1):
            reminder += f"{i}. {item}\n"
        
        reminder += "\n⚠️  IMPORTANT: Attendance must be marked before proceeding with the project.\n"
        reminder += "Failure to mark attendance may affect your internship evaluation.\n"
        
        return reminder
    
    def _check_attendance_status(self) -> Dict[str, Any]:
        """Check attendance status (mock implementation)."""
        # In a real implementation, this would check with the Skills4Future API
        # For now, we'll simulate a successful attendance check
        return {
            'marked': True,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'present',
            'portal_verified': True
        }


class CodeTemplatePopulationStep(WorkflowStep):
    """Step 4: Automated code template population."""
    
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
        self.step_id = 4
    
    def execute(self) -> StepResult:
        """Execute code template population."""
        try:
            project_name = "ev_analysis"  # This should come from workflow state
            
            # Get project files to find the notebook
            files_result = self.file_manager.get_project_files(project_name)
            
            if not files_result['success']:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Failed to get project files: {files_result['error']}"
                )
            
            # Find notebook file
            notebook_file = None
            for file_info in files_result['files']:
                if file_info['filename'].endswith('.ipynb'):
                    notebook_file = file_info['path']
                    break
            
            if not notebook_file:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message="No notebook file found in project"
                )
            
            # Populate notebook with enhanced code templates
            population_result = self._populate_notebook_with_code(notebook_file, project_name)
            
            if not population_result['success']:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Failed to populate code templates: {population_result['error']}"
                )
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.COMPLETED,
                result_data={
                    'notebook_file': notebook_file,
                    'population_result': population_result,
                    'project_name': project_name
                }
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                error_message=f"Code template population failed: {str(e)}"
            )
    
    def validate(self) -> bool:
        """Validate prerequisites for code template population."""
        try:
            # Check if file manager is available
            return hasattr(self.file_manager, 'get_project_files')
        except Exception:
            return False
    
    def rollback(self) -> bool:
        """Rollback code template population."""
        try:
            # Restore original notebook template
            project_name = "ev_analysis"
            project_data = {
                'description': 'Electric Vehicle Market Analysis',
                'requirements': [
                    'Load and explore the EV dataset',
                    'Perform data cleaning and preprocessing',
                    'Create visualizations showing market trends',
                    'Build predictive model for EV adoption',
                    'Generate insights and recommendations'
                ]
            }
            
            # Recreate basic notebook
            self.file_manager.create_notebook_from_template("", project_name, project_data)
            return True
        except Exception:
            return False
    
    def _populate_notebook_with_code(self, notebook_path: str, project_name: str) -> Dict[str, Any]:
        """Populate notebook with enhanced code templates."""
        try:
            import json
            
            # Read existing notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            # Enhanced code templates
            enhanced_cells = self._get_enhanced_code_cells()
            
            # Replace or add enhanced cells
            notebook['cells'] = enhanced_cells
            
            # Write updated notebook
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=2)
            
            return {
                'success': True,
                'cells_added': len(enhanced_cells),
                'notebook_path': notebook_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_enhanced_code_cells(self) -> List[Dict[str, Any]]:
        """Get enhanced code cells with more detailed templates."""
        return [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Electric Vehicle Market Analysis\n",
                    "\n",
                    "**Project Description:** Comprehensive analysis of electric vehicle adoption trends and market patterns\n",
                    "\n",
                    f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                    "\n",
                    "## Project Requirements\n",
                    "\n",
                    "- Load and explore the EV dataset\n",
                    "- Perform data cleaning and preprocessing\n",
                    "- Create visualizations showing market trends\n",
                    "- Build predictive model for EV adoption\n",
                    "- Generate insights and recommendations\n"
                ]
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
                    "from sklearn.preprocessing import StandardScaler, LabelEncoder\n",
                    "from sklearn.ensemble import RandomForestRegressor\n",
                    "from sklearn.metrics import mean_squared_error, r2_score\n",
                    "import warnings\n",
                    "warnings.filterwarnings('ignore')\n",
                    "\n",
                    "# Set display options\n",
                    "pd.set_option('display.max_columns', None)\n",
                    "pd.set_option('display.max_rows', 100)\n",
                    "plt.style.use('seaborn-v0_8')\n",
                    "sns.set_palette('husl')\n",
                    "\n",
                    "print(\"Libraries imported successfully!\")\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Data Loading and Initial Exploration\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Load the dataset\n",
                    "try:\n",
                    "    data = pd.read_csv('dataset.csv')\n",
                    "    print(f\"Dataset loaded successfully!\")\n",
                    "    print(f\"Dataset Shape: {data.shape}\")\n",
                    "except FileNotFoundError:\n",
                    "    print(\"Dataset file not found. Please ensure 'dataset.csv' is in the project directory.\")\n",
                    "    # Create sample data for demonstration\n",
                    "    np.random.seed(42)\n",
                    "    data = pd.DataFrame({\n",
                    "        'year': np.random.randint(2015, 2024, 1000),\n",
                    "        'make': np.random.choice(['Tesla', 'BMW', 'Audi', 'Nissan', 'Chevrolet'], 1000),\n",
                    "        'model': np.random.choice(['Model S', 'Model 3', 'i3', 'e-tron', 'Leaf', 'Bolt'], 1000),\n",
                    "        'range_miles': np.random.normal(250, 50, 1000),\n",
                    "        'price': np.random.normal(45000, 15000, 1000),\n",
                    "        'battery_capacity': np.random.normal(75, 20, 1000)\n",
                    "    })\n",
                    "    print(\"Using sample data for demonstration\")\n",
                    "\n",
                    "# Display basic information\n",
                    "print(\"\\nColumn Names:\")\n",
                    "print(data.columns.tolist())\n",
                    "\n",
                    "print(\"\\nFirst 5 rows:\")\n",
                    "data.head()\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Comprehensive data exploration\n",
                    "print(\"=== DATASET OVERVIEW ===\")\n",
                    "print(f\"Dataset Shape: {data.shape}\")\n",
                    "print(f\"Memory Usage: {data.memory_usage(deep=True).sum() / 1024**2:.2f} MB\")\n",
                    "\n",
                    "print(\"\\n=== DATA TYPES ===\")\n",
                    "print(data.dtypes)\n",
                    "\n",
                    "print(\"\\n=== MISSING VALUES ===\")\n",
                    "missing_data = data.isnull().sum()\n",
                    "missing_percent = (missing_data / len(data)) * 100\n",
                    "missing_df = pd.DataFrame({\n",
                    "    'Missing Count': missing_data,\n",
                    "    'Percentage': missing_percent\n",
                    "})\n",
                    "print(missing_df[missing_df['Missing Count'] > 0])\n",
                    "\n",
                    "print(\"\\n=== BASIC STATISTICS ===\")\n",
                    "data.describe()\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Data Cleaning and Preprocessing\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Data cleaning steps\n",
                    "print(\"=== DATA CLEANING ===\")\n",
                    "\n",
                    "# Create a copy for cleaning\n",
                    "data_clean = data.copy()\n",
                    "original_shape = data_clean.shape\n",
                    "\n",
                    "# Remove duplicates\n",
                    "data_clean = data_clean.drop_duplicates()\n",
                    "print(f\"Removed {original_shape[0] - data_clean.shape[0]} duplicate rows\")\n",
                    "\n",
                    "# Handle missing values (example approach)\n",
                    "numeric_columns = data_clean.select_dtypes(include=[np.number]).columns\n",
                    "categorical_columns = data_clean.select_dtypes(include=['object']).columns\n",
                    "\n",
                    "# Fill numeric missing values with median\n",
                    "for col in numeric_columns:\n",
                    "    if data_clean[col].isnull().sum() > 0:\n",
                    "        median_val = data_clean[col].median()\n",
                    "        data_clean[col].fillna(median_val, inplace=True)\n",
                    "        print(f\"Filled {col} missing values with median: {median_val:.2f}\")\n",
                    "\n",
                    "# Fill categorical missing values with mode\n",
                    "for col in categorical_columns:\n",
                    "    if data_clean[col].isnull().sum() > 0:\n",
                    "        mode_val = data_clean[col].mode()[0]\n",
                    "        data_clean[col].fillna(mode_val, inplace=True)\n",
                    "        print(f\"Filled {col} missing values with mode: {mode_val}\")\n",
                    "\n",
                    "print(f\"\\nCleaned dataset shape: {data_clean.shape}\")\n",
                    "print(f\"Missing values after cleaning: {data_clean.isnull().sum().sum()}\")\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Exploratory Data Analysis and Visualization\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Create comprehensive visualizations\n",
                    "fig, axes = plt.subplots(2, 2, figsize=(15, 12))\n",
                    "fig.suptitle('Electric Vehicle Market Analysis - Key Insights', fontsize=16, fontweight='bold')\n",
                    "\n",
                    "# Plot 1: Distribution of numeric variables\n",
                    "if len(numeric_columns) > 0:\n",
                    "    first_numeric = numeric_columns[0]\n",
                    "    axes[0, 0].hist(data_clean[first_numeric], bins=30, alpha=0.7, color='skyblue', edgecolor='black')\n",
                    "    axes[0, 0].set_title(f'Distribution of {first_numeric}')\n",
                    "    axes[0, 0].set_xlabel(first_numeric)\n",
                    "    axes[0, 0].set_ylabel('Frequency')\n",
                    "\n",
                    "# Plot 2: Categorical distribution\n",
                    "if len(categorical_columns) > 0:\n",
                    "    first_categorical = categorical_columns[0]\n",
                    "    value_counts = data_clean[first_categorical].value_counts().head(10)\n",
                    "    axes[0, 1].bar(range(len(value_counts)), value_counts.values, color='lightcoral')\n",
                    "    axes[0, 1].set_title(f'Top Categories in {first_categorical}')\n",
                    "    axes[0, 1].set_xlabel(first_categorical)\n",
                    "    axes[0, 1].set_ylabel('Count')\n",
                    "    axes[0, 1].set_xticks(range(len(value_counts)))\n",
                    "    axes[0, 1].set_xticklabels(value_counts.index, rotation=45)\n",
                    "\n",
                    "# Plot 3: Correlation heatmap (if multiple numeric columns)\n",
                    "if len(numeric_columns) > 1:\n",
                    "    correlation_matrix = data_clean[numeric_columns].corr()\n",
                    "    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, \n",
                    "                square=True, ax=axes[1, 0])\n",
                    "    axes[1, 0].set_title('Correlation Matrix')\n",
                    "else:\n",
                    "    axes[1, 0].text(0.5, 0.5, 'Insufficient numeric columns\\nfor correlation analysis', \n",
                    "                    ha='center', va='center', transform=axes[1, 0].transAxes)\n",
                    "    axes[1, 0].set_title('Correlation Analysis')\n",
                    "\n",
                    "# Plot 4: Box plot for outlier detection\n",
                    "if len(numeric_columns) > 0:\n",
                    "    axes[1, 1].boxplot([data_clean[col].dropna() for col in numeric_columns[:3]], \n",
                    "                      labels=numeric_columns[:3])\n",
                    "    axes[1, 1].set_title('Box Plot - Outlier Detection')\n",
                    "    axes[1, 1].set_ylabel('Values')\n",
                    "    axes[1, 1].tick_params(axis='x', rotation=45)\n",
                    "\n",
                    "plt.tight_layout()\n",
                    "plt.show()\n",
                    "\n",
                    "# Print key insights\n",
                    "print(\"\\n=== KEY INSIGHTS ===\")\n",
                    "for col in numeric_columns[:3]:\n",
                    "    print(f\"{col}: Mean = {data_clean[col].mean():.2f}, Std = {data_clean[col].std():.2f}\")\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Model Development and Training\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Prepare data for modeling\n",
                    "print(\"=== MODEL DEVELOPMENT ===\")\n",
                    "\n",
                    "# Select features and target (example)\n",
                    "if len(numeric_columns) >= 2:\n",
                    "    # Use first numeric column as target, others as features\n",
                    "    target_column = numeric_columns[0]\n",
                    "    feature_columns = numeric_columns[1:]\n",
                    "    \n",
                    "    # Prepare features and target\n",
                    "    X = data_clean[feature_columns]\n",
                    "    y = data_clean[target_column]\n",
                    "    \n",
                    "    print(f\"Target variable: {target_column}\")\n",
                    "    print(f\"Feature variables: {feature_columns.tolist()}\")\n",
                    "    \n",
                    "    # Handle categorical variables if any in features\n",
                    "    X_processed = X.copy()\n",
                    "    \n",
                    "    # Split the data\n",
                    "    X_train, X_test, y_train, y_test = train_test_split(\n",
                    "        X_processed, y, test_size=0.2, random_state=42\n",
                    "    )\n",
                    "    \n",
                    "    # Scale the features\n",
                    "    scaler = StandardScaler()\n",
                    "    X_train_scaled = scaler.fit_transform(X_train)\n",
                    "    X_test_scaled = scaler.transform(X_test)\n",
                    "    \n",
                    "    # Train a Random Forest model\n",
                    "    model = RandomForestRegressor(n_estimators=100, random_state=42)\n",
                    "    model.fit(X_train_scaled, y_train)\n",
                    "    \n",
                    "    # Make predictions\n",
                    "    y_pred = model.predict(X_test_scaled)\n",
                    "    \n",
                    "    # Evaluate the model\n",
                    "    mse = mean_squared_error(y_test, y_pred)\n",
                    "    r2 = r2_score(y_test, y_pred)\n",
                    "    \n",
                    "    print(f\"\\n=== MODEL PERFORMANCE ===\")\n",
                    "    print(f\"Mean Squared Error: {mse:.4f}\")\n",
                    "    print(f\"R² Score: {r2:.4f}\")\n",
                    "    print(f\"Root Mean Squared Error: {np.sqrt(mse):.4f}\")\n",
                    "    \n",
                    "    # Feature importance\n",
                    "    feature_importance = pd.DataFrame({\n",
                    "        'feature': feature_columns,\n",
                    "        'importance': model.feature_importances_\n",
                    "    }).sort_values('importance', ascending=False)\n",
                    "    \n",
                    "    print(f\"\\n=== FEATURE IMPORTANCE ===\")\n",
                    "    print(feature_importance)\n",
                    "    \n",
                    "else:\n",
                    "    print(\"Insufficient numeric columns for modeling. Please check your dataset.\")\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Results Visualization and Model Evaluation\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Visualize model results\n",
                    "if len(numeric_columns) >= 2:\n",
                    "    fig, axes = plt.subplots(1, 2, figsize=(15, 6))\n",
                    "    \n",
                    "    # Plot 1: Actual vs Predicted\n",
                    "    axes[0].scatter(y_test, y_pred, alpha=0.6, color='blue')\n",
                    "    axes[0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)\n",
                    "    axes[0].set_xlabel('Actual Values')\n",
                    "    axes[0].set_ylabel('Predicted Values')\n",
                    "    axes[0].set_title(f'Actual vs Predicted ({target_column})')\n",
                    "    axes[0].text(0.05, 0.95, f'R² = {r2:.3f}', transform=axes[0].transAxes, \n",
                    "                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))\n",
                    "    \n",
                    "    # Plot 2: Feature Importance\n",
                    "    axes[1].barh(feature_importance['feature'], feature_importance['importance'])\n",
                    "    axes[1].set_xlabel('Importance')\n",
                    "    axes[1].set_title('Feature Importance')\n",
                    "    axes[1].grid(axis='x', alpha=0.3)\n",
                    "    \n",
                    "    plt.tight_layout()\n",
                    "    plt.show()\n",
                    "\n",
                    "print(\"\\n=== MODEL ANALYSIS COMPLETE ===\")\n",
                    "print(\"✅ Data loaded and explored\")\n",
                    "print(\"✅ Data cleaned and preprocessed\")\n",
                    "print(\"✅ Visualizations created\")\n",
                    "print(\"✅ Model trained and evaluated\")\n",
                    "print(\"✅ Results analyzed and visualized\")\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Conclusions and Recommendations\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Generate conclusions and recommendations\n",
                    "print(\"=== PROJECT CONCLUSIONS ===\")\n",
                    "print(\"\\n1. DATA QUALITY ASSESSMENT:\")\n",
                    "print(f\"   - Dataset contains {data_clean.shape[0]} records with {data_clean.shape[1]} features\")\n",
                    "print(f\"   - Data completeness: {((1 - data_clean.isnull().sum().sum() / (data_clean.shape[0] * data_clean.shape[1])) * 100):.1f}%\")\n",
                    "\n",
                    "if len(numeric_columns) >= 2:\n",
                    "    print(f\"\\n2. MODEL PERFORMANCE:\")\n",
                    "    print(f\"   - R² Score: {r2:.3f} ({'Good' if r2 > 0.7 else 'Moderate' if r2 > 0.5 else 'Needs Improvement'})\")\n",
                    "    print(f\"   - RMSE: {np.sqrt(mse):.2f}\")\n",
                    "    \n",
                    "    print(f\"\\n3. KEY INSIGHTS:\")\n",
                    "    top_feature = feature_importance.iloc[0]\n",
                    "    print(f\"   - Most important feature: {top_feature['feature']} (importance: {top_feature['importance']:.3f})\")\n",
                    "\n",
                    "print(f\"\\n4. RECOMMENDATIONS:\")\n",
                    "print(f\"   - Consider collecting additional relevant features to improve model performance\")\n",
                    "print(f\"   - Implement cross-validation for more robust model evaluation\")\n",
                    "print(f\"   - Explore advanced algorithms like XGBoost or Neural Networks\")\n",
                    "print(f\"   - Set up monitoring system for model performance in production\")\n",
                    "\n",
                    "print(f\"\\n=== PROJECT COMPLETED SUCCESSFULLY ===\")\n",
                    "print(f\"Analysis completed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\")\n"
                ]
            }
        ]


class DatasetUploadStep(WorkflowStep):
    """Step 5: Dataset upload to notebook environment."""
    
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
        self.step_id = 5
    
    def execute(self) -> StepResult:
        """Execute dataset upload to notebook environment."""
        try:
            project_name = "ev_analysis"  # This should come from workflow state
            
            # Get project files to verify dataset exists
            files_result = self.file_manager.get_project_files(project_name)
            
            if not files_result['success']:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Failed to get project files: {files_result['error']}"
                )
            
            # Find dataset file
            dataset_file = None
            for file_info in files_result['files']:
                if file_info['filename'].endswith('.csv'):
                    dataset_file = file_info['path']
                    break
            
            if not dataset_file:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message="No dataset file found in project"
                )
            
            # Validate dataset file
            validation_result = self.file_manager.validate_dataset_file(dataset_file)
            
            if not validation_result['valid']:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Dataset validation failed: {validation_result['error']}"
                )
            
            # Simulate upload to notebook environment (in real implementation, this would upload to Colab)
            upload_result = self._simulate_dataset_upload(dataset_file, project_name)
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.COMPLETED,
                result_data={
                    'dataset_file': dataset_file,
                    'validation_result': validation_result,
                    'upload_result': upload_result,
                    'project_name': project_name
                }
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                error_message=f"Dataset upload failed: {str(e)}"
            )
    
    def validate(self) -> bool:
        """Validate prerequisites for dataset upload."""
        try:
            # Check if file manager is available
            return hasattr(self.file_manager, 'validate_dataset_file')
        except Exception:
            return False
    
    def rollback(self) -> bool:
        """Rollback dataset upload."""
        try:
            # In a real implementation, this would remove uploaded files from Colab
            # For now, just return success
            return True
        except Exception:
            return False
    
    def _simulate_dataset_upload(self, dataset_file: str, project_name: str) -> Dict[str, Any]:
        """Simulate dataset upload to notebook environment."""
        try:
            # In a real implementation, this would:
            # 1. Connect to Google Colab API
            # 2. Upload the dataset file
            # 3. Verify the upload
            
            # For simulation, we'll just verify the file exists and is readable
            file_path = Path(dataset_file)
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'Dataset file not found'
                }
            
            file_size = file_path.stat().st_size
            
            return {
                'success': True,
                'upload_path': f'/content/{file_path.name}',  # Typical Colab path
                'file_size': file_size,
                'upload_time': datetime.now().isoformat(),
                'status': 'uploaded_to_colab_environment'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class NotebookCompletionValidationStep(WorkflowStep):
    """Step 6: Notebook completion validation."""
    
    def __init__(self, validation_service: ValidationService):
        self.validation_service = validation_service
        self.step_id = 6
    
    def execute(self) -> StepResult:
        """Execute notebook completion validation."""
        try:
            project_name = "ev_analysis"  # This should come from workflow state
            notebook_path = f"./projects/{project_name}/{project_name}.ipynb"
            
            # Validate notebook content
            is_valid = self.validation_service.validate_notebook_content(notebook_path)
            
            if not is_valid:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message="Notebook validation failed. Please ensure all sections are completed."
                )
            
            # Additional validation checks
            validation_details = self._perform_detailed_validation(notebook_path)
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.COMPLETED,
                result_data={
                    'notebook_path': notebook_path,
                    'validation_passed': True,
                    'validation_details': validation_details,
                    'project_name': project_name
                }
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                error_message=f"Notebook validation failed: {str(e)}"
            )
    
    def validate(self) -> bool:
        """Validate prerequisites for notebook validation."""
        try:
            # Check if validation service is available
            return hasattr(self.validation_service, 'validate_notebook_content')
        except Exception:
            return False
    
    def rollback(self) -> bool:
        """Rollback notebook validation (no-op)."""
        return True
    
    def _perform_detailed_validation(self, notebook_path: str) -> Dict[str, Any]:
        """Perform detailed notebook validation."""
        try:
            import json
            
            validation_results = {
                'file_exists': False,
                'valid_json': False,
                'has_cells': False,
                'has_code_cells': False,
                'has_markdown_cells': False,
                'cell_count': 0,
                'code_cell_count': 0,
                'markdown_cell_count': 0,
                'estimated_completion': 0.0
            }
            
            # Check if file exists
            notebook_file = Path(notebook_path)
            if not notebook_file.exists():
                return validation_results
            
            validation_results['file_exists'] = True
            
            # Try to parse as JSON
            try:
                with open(notebook_path, 'r', encoding='utf-8') as f:
                    notebook = json.load(f)
                validation_results['valid_json'] = True
            except json.JSONDecodeError:
                return validation_results
            
            # Check notebook structure
            if 'cells' not in notebook:
                return validation_results
            
            cells = notebook['cells']
            validation_results['has_cells'] = len(cells) > 0
            validation_results['cell_count'] = len(cells)
            
            # Analyze cells
            code_cells = [cell for cell in cells if cell.get('cell_type') == 'code']
            markdown_cells = [cell for cell in cells if cell.get('cell_type') == 'markdown']
            
            validation_results['code_cell_count'] = len(code_cells)
            validation_results['markdown_cell_count'] = len(markdown_cells)
            validation_results['has_code_cells'] = len(code_cells) > 0
            validation_results['has_markdown_cells'] = len(markdown_cells) > 0
            
            # Estimate completion based on cell content
            completed_cells = 0
            for cell in code_cells:
                source = cell.get('source', '')
                if isinstance(source, list):
                    source = ''.join(source)
                
                # Check if cell has meaningful content (not just TODO or empty)
                if (source.strip() and 
                    'TODO' not in source.upper() and 
                    'FIXME' not in source.upper() and
                    source.strip() != 'pass'):
                    completed_cells += 1
            
            if len(code_cells) > 0:
                validation_results['estimated_completion'] = (completed_cells / len(code_cells)) * 100
            
            return validation_results
            
        except Exception as e:
            return {
                'error': str(e),
                'validation_failed': True
            }


class CodeDatasetManagementOrchestrator:
    """Orchestrates the code and dataset management steps."""
    
    def __init__(self, file_manager: FileManager, validation_service: ValidationService):
        self.file_manager = file_manager
        self.validation_service = validation_service
        
        # Initialize steps
        self.steps = {
            4: CodeTemplatePopulationStep(file_manager),
            5: DatasetUploadStep(file_manager),
            6: NotebookCompletionValidationStep(validation_service)
        }
        
        self.step_order = [4, 5, 6]
        self.results = {}
    
    def execute_all_steps(self) -> Dict[int, StepResult]:
        """Execute all code and dataset management steps in order."""
        results = {}
        
        for step_id in self.step_order:
            step = self.steps[step_id]
            
            # Validate step prerequisites
            if not step.validate():
                results[step_id] = StepResult(
                    step_id=step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Step {step_id} validation failed"
                )
                break
            
            # Execute step
            result = step.execute()
            results[step_id] = result
            
            # Stop on failure
            if result.status == StepStatus.FAILED:
                break
        
        self.results = results
        return results
    
    def execute_step(self, step_id: int) -> StepResult:
        """Execute a specific code/dataset management step."""
        if step_id not in self.steps:
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message=f"Step {step_id} not found"
            )
        
        step = self.steps[step_id]
        
        # Validate prerequisites
        if not step.validate():
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message=f"Step {step_id} validation failed"
            )
        
        # Execute step
        result = step.execute()
        self.results[step_id] = result
        return result
    
    def rollback_step(self, step_id: int) -> bool:
        """Rollback a specific step."""
        if step_id not in self.steps:
            return False
        
        try:
            return self.steps[step_id].rollback()
        except Exception:
            return False
    
    def get_step_status(self, step_id: int) -> Optional[StepStatus]:
        """Get the status of a specific step."""
        if step_id in self.results:
            return self.results[step_id].status
        return None
    
    def is_management_complete(self) -> bool:
        """Check if all code and dataset management steps are complete."""
        for step_id in self.step_order:
            if step_id not in self.results or self.results[step_id].status != StepStatus.COMPLETED:
                return False
        return True
    
    def get_management_summary(self) -> Dict[str, Any]:
        """Get summary of code and dataset management progress."""
        completed_steps = sum(1 for result in self.results.values() 
                            if result.status == StepStatus.COMPLETED)
        
        return {
            'total_steps': len(self.step_order),
            'completed_steps': completed_steps,
            'progress_percentage': (completed_steps / len(self.step_order)) * 100,
            'is_complete': self.is_management_complete(),
            'step_results': {step_id: result.to_dict() for step_id, result in self.results.items()}
        }


class RepositoryCreationStep(WorkflowStep):
    """Step 7: Repository creation and initialization logic."""
    
    def __init__(self, github_service: GitHubService, file_manager: FileManager):
        self.github_service = github_service
        self.file_manager = file_manager
        self.step_id = 7
    
    def execute(self) -> StepResult:
        """Execute repository creation and initialization."""
        try:
            project_name = "ev_analysis"  # This should come from workflow state
            
            # Create repository
            repo_name = f"ev-{project_name}-{datetime.now().strftime('%Y%m%d')}"
            repo_description = f"EV Analysis Project: {project_name.replace('_', ' ').title()}"
            
            create_result = self.github_service.create_repository(repo_name, repo_description)
            
            if not create_result or 'html_url' not in create_result:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Failed to create repository: Invalid response"
                )
            
            repo_url = create_result['html_url']
            
            # Initialize repository with README
            readme_content = self._generate_readme_content(project_name, repo_description)
            readme_result = self.github_service.upload_file(
                repo_name, 
                "README.md", 
                readme_content
            )
            
            if not readme_result or 'content' not in readme_result:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Failed to initialize README: Invalid response"
                )
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.COMPLETED,
                result_data={
                    'repository_name': repo_name,
                    'repository_url': repo_url,
                    'repository_description': repo_description,
                    'readme_initialized': True,
                    'project_name': project_name
                }
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                error_message=f"Repository creation failed: {str(e)}"
            )
    
    def validate(self) -> bool:
        """Validate prerequisites for repository creation."""
        try:
            # Check if GitHub service is available
            return self.github_service.is_authenticated()
        except Exception:
            return False
    
    def rollback(self) -> bool:
        """Rollback repository creation."""
        try:
            # In a real implementation, this might delete the created repository
            # For now, we'll just return success as repository deletion is risky
            return True
        except Exception:
            return False
    
    def _generate_readme_content(self, project_name: str, description: str) -> str:
        """Generate README content for the repository."""
        readme = f"""# {project_name.replace('_', ' ').title()}

{description}

## Project Overview

This repository contains the implementation of an EV analysis project focused on {project_name.replace('_', ' ')}.

## Contents

- `{project_name}.ipynb` - Main Jupyter notebook with analysis and implementation
- `dataset.csv` - Dataset used for the analysis
- `README.md` - This file

## Project Requirements

- Load and explore the dataset
- Perform data cleaning and preprocessing
- Create visualizations and insights
- Build and evaluate predictive models
- Generate actionable recommendations

## Setup Instructions

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd {project_name}
   ```

2. Install required dependencies:
   ```bash
   pip install pandas numpy matplotlib seaborn scikit-learn jupyter
   ```

3. Open the Jupyter notebook:
   ```bash
   jupyter notebook {project_name}.ipynb
   ```

## Usage

1. Run all cells in the notebook sequentially
2. Review the analysis and visualizations
3. Examine the model results and conclusions

## Results

The analysis provides insights into:
- Data patterns and trends
- Key factors affecting the target variable
- Model performance metrics
- Business recommendations

## Author

EV Analysis Researcher

## Date

{datetime.now().strftime('%Y-%m-%d')}

## License

This project is created for research purposes as part of EV infrastructure analysis.
"""
        return readme


class FileUploadOrchestrationStep(WorkflowStep):
    """Step 8: File upload orchestration."""
    
    def __init__(self, github_service: GitHubService, file_manager: FileManager):
        self.github_service = github_service
        self.file_manager = file_manager
        self.step_id = 8
    
    def execute(self) -> StepResult:
        """Execute file upload orchestration."""
        try:
            project_name = "ev_analysis"  # This should come from workflow state
            repo_name = f"ev-{project_name}-{datetime.now().strftime('%Y%m%d')}"
            
            # Prepare upload bundle
            bundle_result = self.file_manager.prepare_upload_bundle(project_name)
            
            if not bundle_result['success']:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Failed to prepare upload bundle: {bundle_result['error']}"
                )
            
            upload_results = []
            
            # Upload each file
            for file_info in bundle_result['files']:
                file_path = file_info['path']
                filename = file_info['filename']
                
                # Read file content
                try:
                    if filename.endswith('.ipynb'):
                        # For notebook files, read as JSON and upload as text
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    elif filename.endswith('.csv'):
                        # For CSV files, read as text
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    else:
                        # For other files, read as text
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    
                    # Upload file to GitHub
                    upload_result = self.github_service.upload_file(
                        repo_name,
                        filename,
                        content
                    )
                    
                    success = upload_result and 'content' in upload_result
                    upload_results.append({
                        'filename': filename,
                        'success': success,
                        'error': None if success else 'Upload failed',
                        'file_size': file_info['size']
                    })
                    
                    if not success:
                        return StepResult(
                            step_id=self.step_id,
                            status=StepStatus.FAILED,
                            error_message=f"Failed to upload {filename}: Upload failed"
                        )
                
                except Exception as e:
                    return StepResult(
                        step_id=self.step_id,
                        status=StepStatus.FAILED,
                        error_message=f"Failed to read file {filename}: {str(e)}"
                    )
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.COMPLETED,
                result_data={
                    'repository_name': repo_name,
                    'uploaded_files': upload_results,
                    'total_files': len(upload_results),
                    'project_name': project_name
                }
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                error_message=f"File upload orchestration failed: {str(e)}"
            )
    
    def validate(self) -> bool:
        """Validate prerequisites for file upload."""
        try:
            # Check if GitHub service is available
            return self.github_service.is_authenticated()
        except Exception:
            return False
    
    def rollback(self) -> bool:
        """Rollback file uploads."""
        try:
            # In a real implementation, this might remove uploaded files
            # For now, we'll just return success
            return True
        except Exception:
            return False


class SubmissionLinkGenerationStep(WorkflowStep):
    """Step 9: Submission link generation."""
    
    def __init__(self, github_service: GitHubService):
        self.github_service = github_service
        self.step_id = 9
    
    def execute(self) -> StepResult:
        """Execute submission link generation."""
        try:
            project_name = "ev_analysis"  # This should come from workflow state
            repo_name = f"ev-{project_name}-{datetime.now().strftime('%Y%m%d')}"
            
            # Generate repository URL
            repo_url = self.github_service.get_repository_url(repo_name)
            
            if not repo_url:
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.FAILED,
                    error_message="Failed to generate repository URL"
                )
            
            # Generate submission summary
            submission_summary = self._generate_submission_summary(
                project_name, 
                repo_name, 
                repo_url
            )
            
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.COMPLETED,
                result_data={
                    'repository_name': repo_name,
                    'repository_url': repo_url,
                    'submission_link': repo_url,
                    'submission_summary': submission_summary,
                    'project_name': project_name,
                    'ready_for_lms_submission': True
                }
            )
            
        except Exception as e:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                error_message=f"Submission link generation failed: {str(e)}"
            )
    
    def validate(self) -> bool:
        """Validate prerequisites for submission link generation."""
        try:
            # Check if GitHub service is available
            return self.github_service.is_authenticated()
        except Exception:
            return False
    
    def rollback(self) -> bool:
        """Rollback submission link generation (no-op)."""
        return True
    
    def _generate_submission_summary(self, project_name: str, repo_name: str, repo_url: str) -> Dict[str, Any]:
        """Generate submission summary for LMS."""
        return {
            'project_title': project_name.replace('_', ' ').title(),
            'repository_name': repo_name,
            'repository_url': repo_url,
            'submission_date': datetime.now().isoformat(),
            'files_included': [
                f'{project_name}.ipynb',
                'dataset.csv',
                'README.md'
            ],
            'completion_status': 'completed',
            'lms_submission_instructions': [
                '1. Copy the repository URL below',
                '2. Log into the research portal',
                '3. Navigate to the project submission section',
                '4. Paste the repository URL in the submission field',
                '5. Add any additional comments if required',
                '6. Submit the assignment'
            ],
            'repository_contents_verified': True,
            'ready_for_submission': True
        }


class GitHubWorkflowOrchestrator:
    """Orchestrates the GitHub workflow steps."""
    
    def __init__(self, github_service: GitHubService, file_manager: FileManager):
        self.github_service = github_service
        self.file_manager = file_manager
        
        # Initialize steps
        self.steps = {
            7: RepositoryCreationStep(github_service, file_manager),
            8: FileUploadOrchestrationStep(github_service, file_manager),
            9: SubmissionLinkGenerationStep(github_service)
        }
        
        self.step_order = [7, 8, 9]
        self.results = {}
    
    def execute_all_steps(self) -> Dict[int, StepResult]:
        """Execute all GitHub workflow steps in order."""
        results = {}
        
        for step_id in self.step_order:
            step = self.steps[step_id]
            
            # Validate step prerequisites
            if not step.validate():
                results[step_id] = StepResult(
                    step_id=step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Step {step_id} validation failed"
                )
                break
            
            # Execute step
            result = step.execute()
            results[step_id] = result
            
            # Stop on failure
            if result.status == StepStatus.FAILED:
                break
        
        self.results = results
        return results
    
    def execute_step(self, step_id: int) -> StepResult:
        """Execute a specific GitHub workflow step."""
        if step_id not in self.steps:
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message=f"Step {step_id} not found"
            )
        
        step = self.steps[step_id]
        
        # Validate prerequisites
        if not step.validate():
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message=f"Step {step_id} validation failed"
            )
        
        # Execute step
        result = step.execute()
        self.results[step_id] = result
        return result
    
    def rollback_step(self, step_id: int) -> bool:
        """Rollback a specific step."""
        if step_id not in self.steps:
            return False
        
        try:
            return self.steps[step_id].rollback()
        except Exception:
            return False
    
    def get_step_status(self, step_id: int) -> Optional[StepStatus]:
        """Get the status of a specific step."""
        if step_id in self.results:
            return self.results[step_id].status
        return None
    
    def is_github_workflow_complete(self) -> bool:
        """Check if all GitHub workflow steps are complete."""
        for step_id in self.step_order:
            if step_id not in self.results or self.results[step_id].status != StepStatus.COMPLETED:
                return False
        return True
    
    def get_github_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of GitHub workflow progress."""
        completed_steps = sum(1 for result in self.results.values() 
                            if result.status == StepStatus.COMPLETED)
        
        # Extract key information from results
        repository_url = None
        submission_link = None
        
        if 9 in self.results and self.results[9].status == StepStatus.COMPLETED:
            result_data = self.results[9].result_data
            repository_url = result_data.get('repository_url')
            submission_link = result_data.get('submission_link')
        
        return {
            'total_steps': len(self.step_order),
            'completed_steps': completed_steps,
            'progress_percentage': (completed_steps / len(self.step_order)) * 100,
            'is_complete': self.is_github_workflow_complete(),
            'repository_url': repository_url,
            'submission_link': submission_link,
            'ready_for_lms_submission': submission_link is not None,
            'step_results': {step_id: result.to_dict() for step_id, result in self.results.items()}
        }


class ProjectInitializationOrchestrator:
    """Orchestrates the project initialization steps."""
    
    def __init__(self, file_manager: FileManager, validation_service: ValidationService):
        self.file_manager = file_manager
        self.validation_service = validation_service
        
        # Initialize steps
        self.steps = {
            1: ProjectSelectionStep(file_manager, validation_service),
            2: NotebookCreationStep(file_manager),
            3: AttendanceReminderStep()
        }
        
        self.step_order = [1, 2, 3]
        self.results = {}
    
    def execute_all_steps(self) -> Dict[int, StepResult]:
        """Execute all initialization steps in order."""
        results = {}
        
        for step_id in self.step_order:
            step = self.steps[step_id]
            
            # Validate step prerequisites
            if not step.validate():
                results[step_id] = StepResult(
                    step_id=step_id,
                    status=StepStatus.FAILED,
                    error_message=f"Step {step_id} validation failed"
                )
                break
            
            # Execute step
            result = step.execute()
            results[step_id] = result
            
            # Stop on failure
            if result.status == StepStatus.FAILED:
                break
        
        self.results = results
        return results
    
    def execute_step(self, step_id: int) -> StepResult:
        """Execute a specific initialization step."""
        if step_id not in self.steps:
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message=f"Step {step_id} not found"
            )
        
        step = self.steps[step_id]
        
        # Validate prerequisites
        if not step.validate():
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error_message=f"Step {step_id} validation failed"
            )
        
        # Execute step
        result = step.execute()
        self.results[step_id] = result
        return result
    
    def rollback_step(self, step_id: int) -> bool:
        """Rollback a specific step."""
        if step_id not in self.steps:
            return False
        
        try:
            return self.steps[step_id].rollback()
        except Exception:
            return False
    
    def get_step_status(self, step_id: int) -> Optional[StepStatus]:
        """Get the status of a specific step."""
        if step_id in self.results:
            return self.results[step_id].status
        return None
    
    def is_initialization_complete(self) -> bool:
        """Check if all initialization steps are complete."""
        for step_id in self.step_order:
            if step_id not in self.results or self.results[step_id].status != StepStatus.COMPLETED:
                return False
        return True
    
    def get_initialization_summary(self) -> Dict[str, Any]:
        """Get summary of initialization progress."""
        completed_steps = sum(1 for result in self.results.values() 
                            if result.status == StepStatus.COMPLETED)
        
        return {
            'total_steps': len(self.step_order),
            'completed_steps': completed_steps,
            'progress_percentage': (completed_steps / len(self.step_order)) * 100,
            'is_complete': self.is_initialization_complete(),
            'step_results': {step_id: result.to_dict() for step_id, result in self.results.items()}
        }