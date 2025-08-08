# EV Vehicle Charge Demand Analysis Tool

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/G0OZE/EV-Vehicle-charge-demand)

A comprehensive machine learning tool for analyzing and predicting EV vehicle charge demand patterns. This tool provides automated data processing, analysis workflows, and predictive modeling capabilities for electric vehicle charging infrastructure planning.

## 🔋 EV Charge Demand Analysis

This project includes advanced ML models that can identify and predict EV vehicle charge demand patterns, making it perfect for infrastructure planning, energy management, and electric vehicle adoption analysis.

## 🚀 Features

- **Automated Project Setup**: Initialize project environments with proper structure
- **Dataset Management**: Automatic download and validation of project datasets
- **Jupyter Notebook Generation**: Create notebooks from templates with starter code
- **GitHub Integration**: Automated repository creation and file uploads
- **Progress Tracking**: Step-by-step workflow with validation and error handling
- **LMS Integration**: Direct submission to Learning Management Systems
- **User Guidance**: Interactive CLI with helpful prompts and error recovery

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Examples](#examples)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## 🛠 Installation

### Prerequisites

- Python 3.8 or higher
- Git installed and configured
- GitHub account with personal access token
- Internet connection for API calls

### Quick Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/G0OZE/EV-Vehicle-charge-demand.git
   cd EV-Vehicle-charge-demand
   ```

2. **Run the installation script**:
   ```bash
   python scripts/install.py
   ```

3. **Or install manually**:
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

### Configuration

1. **Set up GitHub credentials**:
   ```bash
   # Copy configuration template
   cp config/config.development.json config.json
   ```

2. **Edit `config.json`** with your GitHub token:
   ```json
   {
     "github": {
       "token": "your_github_personal_access_token",
       "username": "your_github_username"
     }
   }
   ```

3. **Get GitHub Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` and `user:email` scopes
   - Copy the token to your configuration

## 🚀 Quick Start

### Basic Workflow

```bash
# Start a new EV analysis project
python -m src.cli.workflow_cli start --project "my-ev-analysis"

# Resume an existing analysis
python -m src.cli.workflow_cli resume --project "my-ev-analysis"

# Check analysis progress
python -m src.cli.workflow_cli status --project "my-ev-analysis"

# Validate analysis completion
python -m src.cli.workflow_cli validate --project "my-ev-analysis"
```

### Demo Examples

**EV Dataset Analysis Demo**:
```bash
python demo_ev_workflow.py
```

**User Guidance System Demo**:
```bash
python demo_user_guidance.py
```

**Simple Test Run**:
```bash
python simple_test.py
```

## 📖 Usage

### Command Line Interface

The tool provides a comprehensive CLI for managing your EV analysis projects:

```bash
# Show all available commands
python -m src.cli.workflow_cli --help

# Initialize a new EV analysis project
python -m src.cli.workflow_cli init --name "ev-demand-analysis" --dataset "ev_data.csv"

# Upload analysis to GitHub
python -m src.cli.workflow_cli upload --project "ev-demand-analysis" --repo "ev-analysis-repo"

# Generate analysis report
python -m src.cli.workflow_cli report --project "ev-demand-analysis"
```

### Programmatic Usage

```python
from src.services.workflow_core import WorkflowCore
from src.services.github_service import GitHubService

# Initialize workflow
workflow = WorkflowCore()

# Create and setup EV analysis project
project_result = workflow.initialize_project("ev-analysis", "ev_dataset.csv")

# Upload to GitHub
github_service = GitHubService()
repo_url = github_service.create_repository("ev-analysis", "EV Charge Demand Analysis")
```

### Dashboard

Launch the Streamlit dashboard to monitor workflow progress:

```bash
streamlit run src/ui/dashboard.py
```

## ⚙️ Configuration

### Configuration Files

- `config.json`: Main configuration file
- `.env`: Environment variables (optional)
- `config/config.development.json`: Development template
- `config/config.production.json`: Production template

### Key Configuration Options

```json
{
  "github": {
    "token": "your_token",
    "username": "your_username",
    "timeout_seconds": 30,
    "max_retries": 3
  },
  "workflow": {
    "project_directory": "./projects",
    "backup_enabled": true,
    "auto_cleanup_days": 30
  },
  "logging": {
    "level": "INFO",
    "file": "logs/workflow.log"
  }
}
```

## 📁 Project Structure

```
ev-charge-demand-tool/
├── src/
│   ├── cli/                    # Command-line interface
│   │   ├── workflow_cli.py     # Main CLI commands
│   │   └── base_cli.py         # Base CLI functionality
│   ├── services/               # Core business logic
│   │   ├── workflow_core.py    # Main workflow orchestration
│   │   ├── github_service.py   # GitHub API integration
│   │   ├── file_manager.py     # File operations
│   │   ├── validation_service.py # Input validation
│   │   ├── progress_store.py   # Progress tracking
│   │   └── lms_integration.py  # LMS submission
│   ├── models/                 # Data models
│   │   └── workflow_models.py  # Workflow data structures
│   └── utils/                  # Utility functions
│       ├── config.py           # Configuration management
│       └── logging_config.py   # Logging setup
├── tests/                      # Test suite
├── docs/                       # Documentation
├── scripts/                    # Installation and deployment
├── config/                     # Configuration templates
└── examples/                   # Usage examples
```

## 🎯 Examples

### Example 1: EV Dataset Analysis

```python
# This example shows how to analyze an EV dataset
from src.services.file_manager import FileManager

fm = FileManager(base_directory="./projects")
project_name = "ev_analysis"

# Validate dataset
validation = fm.validate_dataset_file("ev_data.csv")
if validation['valid']:
    # Copy to project
    fm.copy_local_file("ev_data.csv", project_name, "dataset.csv")
    
    # Create analysis notebook
    fm.create_notebook_from_template("", project_name, {
        'description': 'EV Adoption Analysis',
        'requirements': ['Analyze EV trends', 'Create visualizations']
    })
```

### Example 2: GitHub Repository Creation

```python
from src.services.github_service import GitHubService

github = GitHubService()

# Create repository
repo_info = github.create_repository(
    name="my-ev-analysis",
    description="EV Charge Demand Analysis Project"
)

# Upload files
github.upload_file(
    repo_name="my-ev-analysis",
    file_path="ev_analysis.ipynb",
    file_content=notebook_content
)
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_workflow_core.py

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service integration testing
- **End-to-End Tests**: Complete workflow testing
- **Performance Tests**: Load and performance testing

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest`
5. Submit a pull request

### Core Team

- **G0OZE** - Project Lead & Architecture
- **GANTA PRANEETH REDDY** - Co-Developer & ML Models

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all public functions
- Maintain test coverage above 80%

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [User Guide](docs/USER_GUIDE.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## 🐛 Troubleshooting

### Common Issues

**"GitHub API authentication failed"**
- Verify your GitHub token is correct and has proper scopes
- Check if the token hasn't expired

**"Module not found" errors**
- Ensure you're in the correct virtual environment
- Run `pip install -r requirements.txt`

**Network/proxy issues**
- Configure proxy settings in your environment
- Check firewall settings for API access

For more help, check the [troubleshooting guide](docs/TROUBLESHOOTING.md) or [open an issue](https://github.com/G0OZE/EV-Vehicle-charge-demand/issues).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors & Contributors

- **G0OZE** - Lead Developer
- **GANTA PRANEETH REDDY** - Collaborator & Co-Developer

## 🙏 Acknowledgments

- Electric vehicle industry data providers
- Contributors and maintainers
- Open source libraries used in this project

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/G0OZE/EV-Vehicle-charge-demand/issues)
- **Discussions**: [GitHub Discussions](https://github.com/G0OZE/EV-Vehicle-charge-demand/discussions)

---

**Made with ❤️ for EV infrastructure planning by G0OZE & GANTA PRANEETH REDDY**

