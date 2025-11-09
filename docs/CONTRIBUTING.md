# Contributing to Voyce

Thank you for your interest in contributing to Voyce! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Be respectful and considerate
- Use welcoming and inclusive language
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling or insulting/derogatory comments
- Public or private harassment
- Publishing others' private information
- Other unprofessional conduct

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Git
- Databricks account (for data platform features)
- Familiarity with FastAPI, SQLAlchemy, React

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/voyce.git
cd voyce

# Add upstream remote
git remote add upstream https://github.com/suryasai87/voyce.git
```

### Setup Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Copy environment file
cp .env.example .env

# Setup database
createdb voyce_dev
python scripts/init_db.py
```

### Run Locally

```bash
# Start backend
python main.py

# In another terminal, start frontend (if applicable)
cd frontend
npm install
npm run dev
```

## Development Workflow

### Branch Naming Convention

```bash
# Feature
feature/add-user-authentication
feature/voice-upload-api

# Bug fix
fix/database-connection-error
fix/cors-issue

# Documentation
docs/update-api-documentation
docs/add-setup-guide

# Refactoring
refactor/optimize-database-queries
refactor/improve-error-handling
```

### Workflow Steps

1. **Sync with upstream**
   ```bash
   git checkout main
   git pull upstream main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes**
   - Write code
   - Add tests
   - Update documentation

4. **Commit changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Go to GitHub
   - Click "New Pull Request"
   - Fill in template
   - Request review

## Coding Standards

### Python Style Guide

Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these specifics:

```python
# Line length: 100 characters
# Indentation: 4 spaces
# Quotes: Double quotes for strings

# Good
def process_submission(submission_id: str, user_id: str) -> dict:
    """
    Process voice submission and return results.

    Args:
        submission_id: UUID of the submission
        user_id: UUID of the user

    Returns:
        dict: Processing results with status and data

    Raises:
        ValueError: If submission not found
    """
    if not submission_id:
        raise ValueError("Submission ID is required")

    result = service.process(submission_id, user_id)
    return result
```

### Code Formatting

Use **Black** for automatic formatting:

```bash
# Format all files
black .

# Check without modifying
black --check .
```

### Linting

Use **Flake8** for linting:

```bash
# Run flake8
flake8 backend/

# With configuration
flake8 --max-line-length=100 --ignore=E203,W503 backend/
```

### Type Hints

Use type hints for all functions:

```python
from typing import Optional, List, Dict

def get_submissions(
    user_id: str,
    page: int = 1,
    limit: int = 20
) -> Dict[str, any]:
    """Get user submissions with pagination."""
    pass
```

### Imports

Order imports as follows:

```python
# Standard library
import os
import sys
from datetime import datetime

# Third-party packages
from fastapi import FastAPI, HTTPException
from sqlalchemy import Column, String
import numpy as np

# Local imports
from backend.models.user import User
from backend.services.auth import AuthService
from backend.utils.logger import setup_logger
```

## Testing

### Test Requirements

- Unit tests for all new functions
- Integration tests for API endpoints
- Minimum 80% code coverage
- All tests must pass before PR

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test
pytest tests/unit/test_auth.py::TestAuthService::test_login
```

### Writing Tests

```python
# tests/unit/test_service.py
import pytest
from backend.services.voice_processor import VoiceProcessor


class TestVoiceProcessor:
    """Test VoiceProcessor service"""

    @pytest.fixture
    def processor(self):
        return VoiceProcessor()

    def test_validate_audio_format_success(self, processor):
        """Test audio format validation with valid format"""
        assert processor.validate_format("test.wav") is True
        assert processor.validate_format("test.mp3") is True

    def test_validate_audio_format_failure(self, processor):
        """Test audio format validation with invalid format"""
        assert processor.validate_format("test.txt") is False
        assert processor.validate_format("test.pdf") is False

    @pytest.mark.asyncio
    async def test_process_audio(self, processor, sample_audio_file):
        """Test audio processing"""
        result = await processor.process(sample_audio_file)

        assert result is not None
        assert "duration" in result
        assert "sample_rate" in result
```

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def analyze_sentiment(text: str, model: str = "default") -> dict:
    """
    Analyze sentiment of the given text.

    Performs sentiment analysis using the specified model and returns
    a detailed breakdown of sentiment scores.

    Args:
        text: The text to analyze
        model: Model name to use for analysis (default: "default")

    Returns:
        A dictionary containing:
            - sentiment (str): Overall sentiment (positive/negative/neutral)
            - score (float): Sentiment score from -1 to 1
            - confidence (float): Confidence score from 0 to 1
            - breakdown (dict): Detailed sentiment breakdown

    Raises:
        ValueError: If text is empty or None
        ModelNotFoundError: If specified model doesn't exist

    Example:
        >>> result = analyze_sentiment("I love this product!")
        >>> print(result["sentiment"])
        'positive'
    """
    pass
```

### README Updates

Update relevant README files when adding:
- New features
- Configuration options
- Dependencies
- API endpoints

### API Documentation

Update OpenAPI/Swagger docs:

```python
@app.post("/api/submissions/upload", tags=["Submissions"])
async def upload_submission(
    file: UploadFile = File(..., description="Audio file to upload"),
    title: str = Form(None, description="Submission title"),
    category: str = Form(None, description="Submission category")
) -> SubmissionResponse:
    """
    Upload a voice submission.

    Accepts audio files in WAV, MP3, M4A, OGG, or FLAC format.
    Maximum file size is 50MB.

    Returns:
        SubmissionResponse with submission details and upload status
    """
    pass
```

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Added tests for new features
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issue
Fixes #123

## How Has This Been Tested?
Describe testing approach

## Checklist
- [ ] Tests pass locally
- [ ] Added/updated tests
- [ ] Updated documentation
- [ ] Code follows style guide
- [ ] No new warnings
```

### Review Process

1. **Automated checks**: CI/CD must pass
2. **Code review**: At least one approval required
3. **Testing**: Verify in staging environment
4. **Merge**: Squash and merge to main

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
<type>[optional scope]: <description>

[optional body]

[optional footer]

# Examples
feat(auth): add OAuth2 authentication
fix(api): resolve CORS issue for Chrome extension
docs(readme): update installation instructions
refactor(database): optimize query performance
test(submissions): add integration tests for upload
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Testing
- `chore`: Maintenance

## Issue Guidelines

### Creating Issues

Use issue templates:

**Bug Report:**
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS:
- Python version:
- Browser (if applicable):

## Screenshots
If applicable
```

**Feature Request:**
```markdown
## Feature Description
What feature you'd like to see

## Use Case
Why this feature is needed

## Proposed Solution
How it could work

## Alternatives Considered
Other approaches you've considered
```

### Issue Labels

- `bug`: Something isn't working
- `feature`: New feature request
- `documentation`: Documentation improvements
- `enhancement`: Improvement to existing feature
- `good first issue`: Good for newcomers
- `help wanted`: Need community help
- `priority:high`: High priority
- `priority:low`: Low priority

## Questions and Support

- **Documentation**: Check [docs](./README.md)
- **Discussions**: Use [GitHub Discussions](https://github.com/suryasai87/voyce/discussions)
- **Issues**: Report bugs via [GitHub Issues](https://github.com/suryasai87/voyce/issues)
- **Email**: For sensitive topics, email support@voyce.ai

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Annual contributor highlights

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Thank you for contributing to Voyce! Your efforts help make this platform better for everyone.
