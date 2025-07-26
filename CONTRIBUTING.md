# Contributing to AICTE Workflow Tool

Thank you for your interest in contributing to the AICTE Workflow Tool! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the issue template** when available
3. **Provide detailed information** including:
   - Operating system and Python version
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Error messages and logs
   - Screenshots if applicable

### Suggesting Features

We welcome feature suggestions! Please:

1. **Check existing feature requests** first
2. **Describe the use case** and why it's valuable
3. **Provide examples** of how it would work
4. **Consider implementation complexity** and maintenance burden

### Code Contributions

#### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/aicte-workflow-tool.git
   cd aicte-workflow-tool
   ```

3. **Set up development environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Development Guidelines

##### Code Style

- **Follow PEP 8** guidelines
- **Use type hints** for function parameters and return values
- **Write docstrings** for all public functions and classes
- **Keep functions small** and focused on a single responsibility
- **Use meaningful variable names** and avoid abbreviations

##### Code Quality Tools

We use several tools to maintain code quality:

```bash
# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/

# Run all quality checks
python scripts/quality_check.py
```

##### Testing

- **Write tests** for all new functionality
- **Maintain test coverage** above 80%
- **Use descriptive test names** that explain what is being tested
- **Follow the AAA pattern**: Arrange, Act, Assert

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_workflow_core.py

# Run tests with verbose output
python -m pytest -v
```

##### Documentation

- **Update documentation** for any user-facing changes
- **Add docstrings** to new functions and classes
- **Update README.md** if adding new features
- **Include examples** for new functionality

#### Pull Request Process

1. **Ensure your code follows** the style guidelines
2. **Add or update tests** for your changes
3. **Update documentation** as needed
4. **Run the full test suite** and ensure all tests pass
5. **Create a pull request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots for UI changes
   - Breaking changes noted

##### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## 🏗️ Development Setup

### Prerequisites

- Python 3.8+
- Git
- GitHub account
- Text editor or IDE

### Development Dependencies

Install additional development tools:

```bash
pip install -r requirements-dev.txt
```

This includes:
- `pytest` - Testing framework
- `black` - Code formatter
- `isort` - Import sorter
- `flake8` - Linter
- `mypy` - Type checker
- `coverage` - Test coverage

### Project Structure

Understanding the project structure helps with contributions:

```
src/
├── cli/                    # Command-line interface
├── services/               # Core business logic
├── models/                 # Data models
└── utils/                  # Utility functions

tests/                      # Test suite
├── unit/                   # Unit tests
├── integration/            # Integration tests
└── fixtures/               # Test data

docs/                       # Documentation
scripts/                    # Development scripts
config/                     # Configuration templates
```

### Running Development Scripts

```bash
# Setup development environment
python scripts/setup_dev.py

# Run quality checks
python scripts/quality_check.py

# Generate documentation
python scripts/generate_docs.py

# Run performance tests
python scripts/performance_test.py
```

## 🧪 Testing Guidelines

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test service interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Test performance characteristics

### Writing Good Tests

```python
def test_github_service_creates_repository():
    """Test that GitHubService can create a repository successfully."""
    # Arrange
    github_service = GitHubService(token="test_token")
    repo_name = "test-repo"
    
    # Act
    result = github_service.create_repository(repo_name, "Test description")
    
    # Assert
    assert result['success'] is True
    assert result['repo_name'] == repo_name
    assert 'repo_url' in result
```

### Test Data

- Use **fixtures** for reusable test data
- **Mock external services** to avoid API calls during testing
- **Clean up** test data after tests complete

## 📋 Code Review Guidelines

### For Contributors

- **Keep PRs focused** on a single feature or fix
- **Write clear commit messages** following conventional commits
- **Respond promptly** to review feedback
- **Test thoroughly** before requesting review

### For Reviewers

- **Be constructive** and helpful in feedback
- **Focus on code quality** and maintainability
- **Check for security issues** and edge cases
- **Verify tests** cover the changes adequately

## 🚀 Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Update documentation
5. Create release tag
6. Deploy to package repositories

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Email**: killerfantom23@gmail.com for private matters

### Development Questions

If you have questions about:

- **Architecture decisions**: Check the design documents in `docs/`
- **Code style**: Refer to this contributing guide
- **Testing**: Look at existing tests for examples
- **APIs**: Check the API documentation

## 🏆 Recognition

Contributors are recognized in:

- **README.md**: Major contributors listed
- **CHANGELOG.md**: Contributors noted for each release
- **GitHub**: Contributor graphs and statistics

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the AICTE Workflow Tool! 🎉