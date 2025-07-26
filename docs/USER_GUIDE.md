# AICTE Project Workflow Tool - User Guide

This comprehensive guide covers all aspects of using the AICTE Project Workflow Automation Tool for your internship projects.

## Table of Contents

- [Getting Started](#getting-started)
- [Command Reference](#command-reference)
- [Workflow Steps](#workflow-steps)
- [Project Management](#project-management)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Advanced Features](#advanced-features)

## Getting Started

### First Time Setup

1. **Ensure installation is complete** (see [INSTALLATION.md](INSTALLATION.md))
2. **Configure your GitHub credentials** in `config.json`
3. **Test the installation**:
   ```bash
   python -m src.cli.workflow_cli --help
   ```

### Starting Your First Project

```bash
# Start a new project
python -m src.cli.workflow_cli start --project my-ev-analysis

# Or use the interactive mode
python -m src.cli.workflow_cli start
```

## Command Reference

### Main Commands

#### `start` - Start a New Project

```bash
python -m src.cli.workflow_cli start [OPTIONS]

Options:
  --project TEXT    Project name (required)
  --config TEXT     Configuration file path
  --help           Show help message
```

**Examples**:
```bash
# Start with specific project name
python -m src.cli.workflow_cli start --project ev-market-analysis

# Start with custom config
python -m src.cli.workflow_cli start --project my-project --config custom-config.json
```

#### `resume` - Resume Existing Project

```bash
python -m src.cli.workflow_cli resume [OPTIONS]

Options:
  --project TEXT    Project name to resume
  --help           Show help message
```

**Examples**:
```bash
# Resume specific project
python -m src.cli.workflow_cli resume --project ev-market-analysis

# Resume with interactive selection
python -m src.cli.workflow_cli resume
```

#### `progress` - Check Project Progress

```bash
python -m src.cli.workflow_cli progress [OPTIONS]

Options:
  --project TEXT    Project name
  --detailed       Show detailed progress information
  --help           Show help message
```

**Examples**:
```bash
# Check progress for specific project
python -m src.cli.workflow_cli progress --project my-project

# Show detailed progress for all projects
python -m src.cli.workflow_cli progress --detailed
```

#### `validate` - Validate Project Status

```bash
python -m src.cli.workflow_cli validate [OPTIONS]

Options:
  --project TEXT    Project name to validate
  --help           Show help message
```

#### `list` - List All Projects

```bash
python -m src.cli.workflow_cli list

# Shows all projects with their current status
```

#### `reset` - Reset Project Progress

```bash
python -m src.cli.workflow_cli reset [OPTIONS]

Options:
  --project TEXT    Project name to reset
  --confirm        Skip confirmation prompt
  --help           Show help message
```

**Examples**:
```bash
# Reset with confirmation
python -m src.cli.workflow_cli reset --project my-project

# Reset without confirmation prompt
python -m src.cli.workflow_cli reset --project my-project --confirm
```

### Global Options

```bash
--version         Show version information
--help           Show help message
--config TEXT    Specify configuration file
```

## Workflow Steps

The tool guides you through a 5-step workflow process:

### Step 1: Project Setup
- **Purpose**: Initialize project environment and validate prerequisites
- **Actions**:
  - Verify GitHub credentials
  - Check system requirements
  - Create project directory structure
  - Validate Skills4Future portal access
- **User Input**: Project name, confirmation of attendance marking

### Step 2: Dataset Download
- **Purpose**: Download and prepare the project dataset
- **Actions**:
  - Download dataset from provided URL
  - Validate file format and integrity
  - Prepare dataset for analysis
- **User Input**: Dataset selection (if multiple options available)

### Step 3: Code Development
- **Purpose**: Set up Google Colab notebook with starter code
- **Actions**:
  - Create notebook from template
  - Populate with project-specific code
  - Upload dataset to Colab environment
  - Validate notebook structure
- **User Input**: Code customization, notebook completion confirmation

### Step 4: GitHub Repository
- **Purpose**: Create and populate GitHub repository
- **Actions**:
  - Create repository with project name
  - Initialize with README file
  - Upload notebook and dataset files
  - Generate repository URL
- **User Input**: Repository name confirmation, file upload verification

### Step 5: LMS Submission
- **Purpose**: Prepare and submit to Learning Management System
- **Actions**:
  - Validate all components are complete
  - Generate submission summary
  - Provide LMS submission link
  - Create final checklist
- **User Input**: Final submission confirmation

## Project Management

### Project Structure

Each project creates the following structure:
```
projects/
└── your-project-name/
    ├── dataset.csv
    ├── notebook.ipynb
    ├── README.md
    ├── progress.json
    └── logs/
        └── project.log
```

### Progress Tracking

The tool automatically tracks:
- **Step completion status**
- **Timestamps for each action**
- **Error logs and recovery attempts**
- **File upload status**
- **GitHub repository information**

### Project States

- **`not_started`**: Project created but no steps completed
- **`in_progress`**: Some steps completed, workflow active
- **`completed`**: All steps finished successfully
- **`failed`**: Workflow stopped due to errors
- **`paused`**: Workflow manually paused

## Configuration

### Basic Configuration

Edit `config.json` for basic settings:

```json
{
  "github": {
    "token": "your_github_token",
    "username": "your_username"
  },
  "workflow": {
    "project_directory": "./projects",
    "max_retries": 3,
    "timeout_seconds": 30
  },
  "logging": {
    "level": "INFO",
    "file": "logs/workflow.log"
  }
}
```

### Environment Variables

Override configuration with environment variables:

```bash
export GITHUB_TOKEN="your_token"
export GITHUB_USERNAME="your_username"
export LOG_LEVEL="DEBUG"
export DEFAULT_PROJECT_DIR="./my_projects"
```

### Advanced Configuration

For production use, configure additional settings:

```json
{
  "security": {
    "encrypt_progress_files": true,
    "validate_file_types": true,
    "max_file_size_mb": 100
  },
  "performance": {
    "concurrent_uploads": 3,
    "connection_pool_size": 10,
    "cache_enabled": true
  },
  "notifications": {
    "enabled": true,
    "email_on_completion": true,
    "webhook_url": "https://your-webhook.com"
  }
}
```

## Troubleshooting

### Common Issues and Solutions

#### Authentication Errors

**Problem**: "GitHub authentication failed"

**Solutions**:
1. Verify your GitHub token is correct and hasn't expired
2. Check token has required permissions (`repo`, `user:email`)
3. Test token manually:
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   ```

#### Network Issues

**Problem**: "Connection timeout" or "Network error"

**Solutions**:
1. Check internet connection
2. Configure proxy settings if behind corporate firewall
3. Increase timeout in configuration:
   ```json
   {"workflow": {"timeout_seconds": 60}}
   ```

#### File Upload Failures

**Problem**: "Failed to upload file to GitHub"

**Solutions**:
1. Check file size (GitHub has 100MB limit)
2. Verify file format is supported
3. Check repository permissions
4. Retry with manual upload if needed

#### Progress Not Saving

**Problem**: Progress lost between sessions

**Solutions**:
1. Check write permissions in project directory
2. Verify `progress.json` file exists and is readable
3. Check disk space availability
4. Review log files for specific errors

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Set debug level logging
export LOG_LEVEL=DEBUG

# Enable verbose output
python -m src.cli.workflow_cli start --project test-debug
```

### Log Analysis

Analyze logs for issues:

```bash
# View recent errors
grep ERROR logs/workflow.log | tail -10

# Generate analysis report
python -c "
from src.utils.logging_config import LogAnalyzer
analyzer = LogAnalyzer()
print(analyzer.generate_report())
"
```

## Best Practices

### Project Naming

- Use descriptive, kebab-case names: `ev-market-analysis-2024`
- Avoid spaces and special characters
- Keep names under 50 characters
- Include year or version if relevant

### GitHub Repository Management

- Use meaningful commit messages
- Keep repositories public for AICTE requirements
- Include comprehensive README files
- Tag releases for major milestones

### Data Management

- Validate datasets before processing
- Keep original datasets unchanged
- Document data sources and transformations
- Use appropriate file formats (CSV for tabular data)

### Error Handling

- Always check logs when issues occur
- Use retry mechanisms for transient failures
- Keep backups of important progress files
- Document custom configurations

### Performance Optimization

- Use appropriate chunk sizes for large files
- Enable caching for repeated operations
- Limit concurrent operations based on system resources
- Monitor memory usage for large datasets

## Advanced Features

### Batch Processing

Process multiple projects:

```bash
# Create batch script
cat > batch_projects.txt << EOF
project-1
project-2
project-3
EOF

# Process batch
while read project; do
  python -m src.cli.workflow_cli start --project "$project"
done < batch_projects.txt
```

### Custom Templates

Create custom notebook templates:

1. Create template file in `templates/custom_template.ipynb`
2. Configure in `config.json`:
   ```json
   {"workflow": {"notebook_template": "templates/custom_template.ipynb"}}
   ```

### Webhook Integration

Set up webhooks for notifications:

```json
{
  "notifications": {
    "webhook_url": "https://hooks.slack.com/your-webhook",
    "webhook_events": ["step_complete", "workflow_complete", "error"]
  }
}
```

### API Integration

Use the tool programmatically:

```python
from src.services.workflow_core import WorkflowCore
from src.services.progress_store import FileProgressStore

# Initialize workflow
progress_store = FileProgressStore("./projects")
workflow = WorkflowCore(progress_store)

# Start project
workflow.initialize_workflow("my-api-project")

# Execute steps
for step_id in range(1, 6):
    result = workflow.execute_step(step_id)
    print(f"Step {step_id}: {result.status}")
```

### Custom Validation Rules

Add custom validation:

```python
# In config.json
{
  "validation": {
    "custom_rules": [
      {"type": "file_size", "max_mb": 50},
      {"type": "file_format", "allowed": [".csv", ".json", ".ipynb"]},
      {"type": "notebook_cells", "min_count": 5}
    ]
  }
}
```

## Support and Resources

### Getting Help

1. **Check logs**: `logs/workflow.log` for detailed information
2. **Run diagnostics**: `python -m src.cli.workflow_cli validate`
3. **Review documentation**: All guides in `docs/` directory
4. **Search issues**: Check GitHub issues for similar problems

### Community Resources

- **GitHub Repository**: [Link to repository]
- **Discussion Forum**: [Link to discussions]
- **Video Tutorials**: [Link to tutorials]
- **FAQ**: [Link to FAQ]

### Reporting Issues

When reporting issues, include:
- Command that failed
- Complete error message
- Log file contents (relevant sections)
- System information (OS, Python version)
- Configuration file (remove sensitive data)

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Contributing code
- Improving documentation