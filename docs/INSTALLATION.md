# AICTE Project Workflow Tool - Installation Guide

This guide provides comprehensive instructions for installing and setting up the AICTE Project Workflow Automation Tool.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Manual Installation](#manual-installation)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+, CentOS 7+)
- **Python**: Version 3.8 or higher
- **Memory**: 512 MB RAM minimum, 1 GB recommended
- **Storage**: 100 MB free disk space
- **Network**: Internet connection for GitHub API and dataset downloads

### Recommended Requirements

- **Python**: Version 3.9 or higher
- **Memory**: 2 GB RAM or more
- **Storage**: 500 MB free disk space
- **Git**: Latest version installed and configured

### Dependencies

The tool requires the following Python packages (automatically installed):

- `requests>=2.25.0` - HTTP library for API calls
- `click>=8.0.0` - Command-line interface framework
- `colorama>=0.4.4` - Cross-platform colored terminal text
- `python-dotenv>=0.19.0` - Environment variable management
- `cryptography>=3.4.0` - Security and encryption utilities
- `psutil>=5.8.0` - System and process utilities

## Quick Installation

### Using the Installation Script (Recommended)

1. **Download or clone the repository**:
   ```bash
   git clone https://github.com/your-org/aicte-workflow-tool.git
   cd aicte-workflow-tool
   ```

2. **Run the installation script**:
   ```bash
   python scripts/install.py
   ```

3. **For development installation** (includes testing tools):
   ```bash
   python scripts/install.py --dev
   ```

4. **Follow the prompts** and configure your GitHub credentials when prompted.

### Using pip (if packaged)

```bash
pip install aicte-workflow-tool
```

## Manual Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/aicte-workflow-tool.git
cd aicte-workflow-tool
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install required packages
pip install -r requirements.txt

# For development (optional)
pip install -r requirements-dev.txt
```

### Step 4: Create Directories

```bash
mkdir -p logs projects temp backups
```

### Step 5: Setup Configuration

```bash
# Copy configuration template
cp config/config.development.json config.json

# Create environment file
cp .env.template .env
```

## Configuration

### Basic Configuration

1. **Edit the configuration file** (`config.json`):
   ```json
   {
     "github": {
       "token": "your_github_personal_access_token",
       "username": "your_github_username"
     },
     "workflow": {
       "project_directory": "./projects"
     },
     "logging": {
       "level": "INFO",
       "file": "logs/workflow.log"
     }
   }
   ```

2. **Set up environment variables** (`.env` file):
   ```bash
   GITHUB_TOKEN=your_github_token_here
   GITHUB_USERNAME=your_github_username
   LOG_LEVEL=INFO
   ```

### GitHub Token Setup

1. **Go to GitHub Settings** → **Developer settings** → **Personal access tokens**
2. **Click "Generate new token"**
3. **Select the following scopes**:
   - `repo` (Full control of private repositories)
   - `user:email` (Access user email addresses)
4. **Copy the generated token** and add it to your configuration

### Advanced Configuration

For production deployments, use `config/config.production.json` as a template:

```json
{
  "github": {
    "token": "",
    "username": "",
    "timeout_seconds": 30,
    "max_retries": 3,
    "rate_limit_buffer": 100
  },
  "workflow": {
    "project_directory": "./projects",
    "backup_enabled": true,
    "backup_interval_hours": 24,
    "auto_cleanup_days": 30
  },
  "logging": {
    "level": "INFO",
    "file": "logs/workflow.log",
    "max_file_size_mb": 10,
    "backup_count": 5
  },
  "security": {
    "encrypt_progress_files": true,
    "validate_file_types": true,
    "max_file_size_mb": 100
  },
  "performance": {
    "concurrent_uploads": 3,
    "connection_pool_size": 10,
    "cache_enabled": true
  }
}
```

## Verification

### Test Installation

1. **Check if the tool is properly installed**:
   ```bash
   python -m src.cli.workflow_cli --help
   ```

2. **Run the built-in diagnostics**:
   ```bash
   python -m src.cli.workflow_cli validate
   ```

3. **Test GitHub connectivity**:
   ```bash
   python -c "from src.services.github_service import GitHubService; print('GitHub service OK')"
   ```

### Launch Scripts

After installation, you can use the convenient launch scripts:

**Windows**:
```cmd
workflow.bat --help
quickstart.bat
```

**macOS/Linux**:
```bash
./workflow.sh --help
./quickstart.sh
```

## Platform-Specific Instructions

### Windows

1. **Install Python** from [python.org](https://python.org) or Microsoft Store
2. **Add Python to PATH** during installation
3. **Open Command Prompt or PowerShell** as Administrator (if needed)
4. **Follow the Quick Installation steps**

### macOS

1. **Install Python** using Homebrew:
   ```bash
   brew install python
   ```
2. **Install Git** (if not already installed):
   ```bash
   brew install git
   ```
3. **Follow the Quick Installation steps**

### Linux (Ubuntu/Debian)

1. **Update package list**:
   ```bash
   sudo apt update
   ```
2. **Install Python and pip**:
   ```bash
   sudo apt install python3 python3-pip python3-venv git
   ```
3. **Follow the Quick Installation steps**

### Linux (CentOS/RHEL)

1. **Install Python and Git**:
   ```bash
   sudo yum install python3 python3-pip git
   ```
2. **Follow the Quick Installation steps**

## Troubleshooting

### Common Issues

#### "Python not found" Error

**Solution**: Ensure Python is installed and added to your system PATH.

```bash
# Check Python installation
python --version
# or
python3 --version
```

#### "Permission denied" Error

**Solution**: 
- On Windows: Run Command Prompt as Administrator
- On macOS/Linux: Use `sudo` for system-wide installation or use virtual environment

#### "GitHub API authentication failed"

**Solution**:
1. Verify your GitHub token is correct
2. Check token permissions include `repo` scope
3. Ensure token hasn't expired

#### "Module not found" Error

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Network/Proxy Issues

**Solution**:
```bash
# Configure pip for proxy
pip install --proxy http://proxy.server:port package_name

# Or set environment variables
export HTTP_PROXY=http://proxy.server:port
export HTTPS_PROXY=http://proxy.server:port
```

### Log Analysis

Check the log files for detailed error information:

```bash
# View recent logs
tail -f logs/workflow.log

# View error logs only
grep ERROR logs/workflow.log

# Generate log analysis report
python -c "from src.utils.logging_config import LogAnalyzer; print(LogAnalyzer().generate_report())"
```

### Getting Help

1. **Check the logs** in the `logs/` directory
2. **Run diagnostics**: `python -m src.cli.workflow_cli validate`
3. **Check GitHub Issues** for known problems
4. **Contact support** with log files and system information

## Uninstallation

### Using the Installation Script

```bash
python scripts/install.py --uninstall
```

### Manual Uninstallation

1. **Remove the project directory**:
   ```bash
   rm -rf /path/to/aicte-workflow-tool
   ```

2. **Remove virtual environment** (if used):
   ```bash
   rm -rf .venv
   ```

3. **Remove configuration files** (optional):
   ```bash
   rm ~/.aicte-workflow-config.json
   ```

4. **Uninstall pip packages** (if installed globally):
   ```bash
   pip uninstall aicte-workflow-tool
   ```

## Next Steps

After successful installation:

1. **Read the [User Guide](USER_GUIDE.md)** for detailed usage instructions
2. **Try the [Quick Start Tutorial](QUICK_START.md)** 
3. **Configure your first project** using the CLI
4. **Join the community** for support and updates

## Support

- **Documentation**: [docs/](../docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/aicte-workflow-tool/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/aicte-workflow-tool/discussions)
- **Email**: killerfantom23@gmail.com