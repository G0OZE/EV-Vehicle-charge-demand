# User Guidance System Documentation

## Overview

The User Guidance System provides comprehensive error handling, help documentation, and troubleshooting support for the AICTE Project Workflow Automation tool. It helps students understand and resolve issues that may occur during the project submission process.

## Features

### 1. Intelligent Error Classification

The system automatically classifies errors into categories and provides specific guidance:

- **Network Errors**: Connection issues, timeouts, API rate limits
- **Authentication Errors**: GitHub token issues, permission problems
- **Validation Errors**: Notebook validation, dataset validation failures
- **File System Errors**: Permission denied, file not found issues
- **GitHub API Errors**: Repository creation, file upload failures
- **Configuration Errors**: Invalid config files, missing settings
- **Dependency Errors**: Missing packages, import failures
- **Workflow Errors**: Step failures, progress state issues
- **LMS Integration Errors**: Submission failures
- **Project Errors**: Invalid project selection

### 2. Structured Error Messages

Each error provides:
- **Error Code**: Unique identifier for the error type
- **Title**: Clear, descriptive error title
- **Description**: Detailed explanation of the issue
- **Category**: Error classification for better understanding
- **Severity Level**: Impact assessment (Low, Medium, High, Critical)
- **Resolution Steps**: Step-by-step instructions to fix the issue
- **Troubleshooting Tips**: Additional helpful information
- **Related Links**: Documentation and external resources

### 3. Comprehensive Help System

#### Available Help Topics

1. **getting-started**: Basic setup and first steps
2. **github-setup**: GitHub configuration and token setup
3. **troubleshooting**: Common issues and solutions
4. **workflow-commands**: Complete command reference
5. **project-requirements**: Understanding project validation
6. **error-recovery**: Error recovery strategies

#### Help Topic Structure

Each help topic includes:
- Title and description
- Multiple sections with specific content
- Step-by-step instructions
- Examples and use cases

### 4. Troubleshooting Guides

#### Available Guides

1. **workflow-stuck**: When workflow appears frozen
2. **github-authentication**: GitHub token and permission issues
3. **notebook-validation**: Notebook validation failures
4. **dataset-issues**: Dataset loading and processing problems
5. **submission-deadline**: Deadline and timing issues
6. **repository-access**: GitHub repository access problems
7. **environment-setup**: Python environment and dependencies
8. **performance-optimization**: Performance and resource issues

#### Guide Structure

Each guide provides:
- **Symptoms**: How to identify the issue
- **Diagnosis Steps**: How to investigate the problem
- **Solutions**: Step-by-step resolution instructions

## Usage

### Getting Error Guidance

```python
from src.services.user_guidance import UserGuidanceService

guidance_service = UserGuidanceService()

# Get guidance for an error
error_message = "Connection failed"
guidance = guidance_service.get_error_guidance(error_message)

# Format and display the guidance
formatted_message = guidance_service.format_guidance_message(guidance)
print(formatted_message)
```

### Getting Help for Topics

```python
# List available help topics
topics = guidance_service.list_help_topics()
print("Available topics:", topics)

# Get help for specific topic
help_info = guidance_service.get_help_for_topic("getting-started")
if help_info:
    print(f"Title: {help_info['title']}")
    print(f"Description: {help_info['description']}")
    for section in help_info['sections']:
        print(f"\n{section['title']}:")
        for item in section['content']:
            print(f"  - {item}")
```

### Getting Troubleshooting Guides

```python
# List available guides
guides = guidance_service.list_troubleshooting_guides()
print("Available guides:", guides)

# Get specific troubleshooting guide
guide = guidance_service.get_troubleshooting_guide("workflow-stuck")
if guide:
    print(f"Title: {guide['title']}")
    print(f"Description: {guide['description']}")
    
    if 'symptoms' in guide:
        print("\nSymptoms:")
        for symptom in guide['symptoms']:
            print(f"  - {symptom}")
    
    if 'solutions' in guide:
        print("\nSolutions:")
        for solution in guide['solutions']:
            print(f"  - {solution}")
```

### Context-Aware Guidance

The system can provide context-specific guidance:

```python
context = {
    'project_name': 'ev-analysis',
    'step_id': 3,
    'file_path': '/path/to/dataset.csv'
}

guidance = guidance_service.get_error_guidance("File not found", context)
# Guidance will include project-specific information
```

## Error Codes Reference

### Network Errors (NET)
- **NET001**: Internet Connection Failed
- **NET002**: GitHub API Rate Limit Exceeded

### Authentication Errors (AUTH)
- **AUTH001**: GitHub Token Missing or Invalid

### Validation Errors (VAL)
- **VAL001**: Notebook Validation Failed
- **VAL002**: Dataset File Invalid

### File System Errors (FS)
- **FS001**: File Permission Denied

### GitHub API Errors (GH)
- **GH001**: Repository Creation Failed

### Configuration Errors (CFG)
- **CFG001**: Configuration File Missing or Invalid

### Dependency Errors (DEP)
- **DEP001**: Required Package Missing

### Workflow Errors (WF)
- **WF001**: Workflow Step Failed
- **WF002**: Progress State Corrupted
- **WF003**: Submission Validation Failed

### LMS Integration Errors (LMS)
- **LMS001**: LMS Submission Failed

### Project Errors (PRJ)
- **PRJ001**: Project Selection Invalid

## Severity Levels

- **🚨 Critical**: System cannot continue, immediate action required
- **❌ High**: Major functionality affected, high priority fix needed
- **⚠️ Medium**: Some functionality affected, should be addressed
- **ℹ️ Low**: Minor issue, informational

## Best Practices

### For Users

1. **Read Error Messages Carefully**: Error messages contain specific guidance
2. **Follow Resolution Steps**: Steps are ordered by likelihood of success
3. **Use Help System**: Comprehensive help is available for all topics
4. **Check Prerequisites**: Ensure all requirements are met before starting
5. **Keep Tokens Updated**: Regularly refresh GitHub tokens

### For Developers

1. **Provide Context**: Include relevant context when getting error guidance
2. **Use Appropriate Severity**: Match severity to actual impact
3. **Keep Messages Updated**: Regularly review and update error messages
4. **Test Error Scenarios**: Ensure error handling works correctly
5. **Document New Errors**: Add new error patterns to the catalog

## Integration with CLI

The user guidance system is integrated with the CLI interface:

```bash
# Get help for specific topic
python -m src.cli.workflow_cli help getting-started

# Get troubleshooting guide
python -m src.cli.workflow_cli troubleshoot workflow-stuck

# List available help topics
python -m src.cli.workflow_cli help --list

# List troubleshooting guides
python -m src.cli.workflow_cli troubleshoot --list
```

## Customization

### Adding New Error Types

1. Add error code to `_build_error_catalog()` method
2. Update `_classify_error()` method to recognize the error pattern
3. Add corresponding unit tests
4. Update documentation

### Adding Help Topics

1. Add topic to `_build_help_topics()` method
2. Follow the standard structure with title, description, and sections
3. Add unit tests for the new topic
4. Update documentation

### Adding Troubleshooting Guides

1. Add guide to `_build_troubleshooting_guides()` method
2. Include symptoms, diagnosis steps, and solutions
3. Add unit tests for the new guide
4. Update documentation

## Testing

The user guidance system includes comprehensive unit tests covering:

- Error classification accuracy
- Message formatting
- Help topic retrieval
- Troubleshooting guide access
- Context-aware customization
- Edge cases and error conditions

Run tests with:
```bash
python -m pytest tests/test_user_guidance.py -v
```

## Future Enhancements

1. **Interactive Troubleshooting**: Step-by-step interactive problem solving
2. **Machine Learning**: Learn from user interactions to improve guidance
3. **Multilingual Support**: Support for multiple languages
4. **Visual Guides**: Include diagrams and screenshots
5. **Community Contributions**: Allow users to contribute solutions
6. **Analytics**: Track common issues and improve documentation