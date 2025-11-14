# Contributing to MSH Med Tour

Thank you for considering contributing to MSH Med Tour! This document provides guidelines and instructions for contributing.

## 🤝 Ways to Contribute

- **Report Bugs** - Submit issues with detailed descriptions
- **Suggest Features** - Propose new functionality
- **Fix Bugs** - Submit pull requests with bug fixes
- **Add Features** - Implement new features (discuss first!)
- **Improve Documentation** - Fix typos, add clarity, add examples
- **Write Tests** - Improve test coverage
- **Share Feedback** - Help us improve the project

---

## 🐛 Reporting Bugs

### Before Reporting
- Check if bug already exists in [Issues](https://github.com/mshjiyan-a11y/msh_med_tour/issues)
- Try to reproduce on latest `main` branch
- Collect relevant information

### How to Report
1. Go to [Issues](https://github.com/mshjiyan-a11y/msh_med_tour/issues)
2. Click "New Issue"
3. Choose "Bug Report" template
4. Fill in required information:
   - **Title:** Clear, descriptive title
   - **Description:** What happened vs. expected behavior
   - **Steps to Reproduce:** Exact steps to reproduce
   - **Environment:** Python version, OS, browser
   - **Screenshots:** If applicable
   - **Error Messages:** Full error output

### Bug Report Template
```markdown
## Bug Description
[Brief description of the bug]

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: [e.g., Windows 10, macOS, Ubuntu]
- Python Version: [e.g., 3.9.0]
- Browser: [e.g., Chrome 90]
- Flask Version: [from requirements.txt]

## Error Messages
[Paste full error traceback if applicable]

## Additional Context
[Any other relevant information]
```

---

## ✨ Suggesting Features

### Before Suggesting
- Check if feature already requested in [Issues](https://github.com/mshjiyan-a11y/msh_med_tour/issues)
- Ensure feature aligns with project goals
- Think about implementation approach

### How to Suggest
1. Go to [Issues](https://github.com/mshjiyan-a11y/msh_med_tour/issues)
2. Click "New Issue"
3. Choose "Feature Request" template
4. Fill in details:
   - **Title:** Clear feature name
   - **Problem:** What problem does it solve?
   - **Solution:** How should it work?
   - **Benefits:** Why is it important?
   - **Examples:** Show use cases

### Feature Request Template
```markdown
## Feature Description
[Clear description of the feature]

## Problem It Solves
[What problem/pain point does this address?]

## Proposed Solution
[How should this feature work?]

## Benefits
- Benefit 1
- Benefit 2
- Benefit 3

## Implementation Approach
[How you think it could be implemented]

## Examples
[Show how it would be used]

## Additional Context
[Any other relevant information]
```

---

## 🔧 Development Setup

### 1. Fork Repository
- Click "Fork" on GitHub
- Creates your own copy

### 2. Clone Your Fork
```bash
git clone https://github.com/YOUR_USERNAME/msh_med_tour.git
cd msh_med_tour
```

### 3. Add Upstream Remote
```bash
git remote add upstream https://github.com/mshjiyan-a11y/msh_med_tour.git
```

### 4. Create Branch
```bash
# Update main
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 5. Make Changes
- Follow code style guidelines
- Write/update tests
- Update documentation

### 6. Commit Changes
```bash
git add .
git commit -m "feat: add your feature description"
```

### 7. Push to Your Fork
```bash
git push origin feature/your-feature-name
```

### 8. Create Pull Request
- Go to your fork on GitHub
- Click "Compare & pull request"
- Fill in PR template
- Wait for review

---

## 📝 Code Style Guide

### Python Style (PEP 8)
```python
# Good: Clear, well-formatted code
def calculate_lead_score(lead_data):
    """Calculate quality score for a lead.
    
    Args:
        lead_data (dict): Lead information
        
    Returns:
        int: Quality score 0-100
    """
    score = 0
    
    # Check data completeness
    if all([lead_data.get('email'), lead_data.get('phone')]):
        score += 20
    
    return score

# Bad: Poor naming and formatting
def cs(d):
    s = 0
    if d.get('e') and d.get('p'):
        s += 20
    return s
```

### Naming Conventions
```python
# Variables and functions: snake_case
user_email = "user@example.com"
def get_user_by_id(user_id):
    pass

# Classes: PascalCase
class FacebookLead:
    pass

class MetaAPIConfig:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Private methods/attributes: _leading_underscore
def _internal_method(self):
    pass

self._private_attribute = None
```

### Docstring Format
```python
def sync_leads(config, limit=100):
    """Synchronize leads from Meta API.
    
    Fetches latest leads from configured Meta Lead Form
    and stores them in database with quality scoring.
    
    Args:
        config (MetaAPIConfig): Meta API configuration
        limit (int, optional): Max leads to fetch. Defaults to 100.
        
    Returns:
        dict: Sync result with keys:
            - success (bool): Whether sync succeeded
            - count (int): Number of leads synced
            - errors (list): Any errors encountered
            
    Raises:
        ValueError: If config is invalid
        requests.exceptions.RequestException: If API call fails
        
    Example:
        >>> config = MetaAPIConfig.query.first()
        >>> result = sync_leads(config, limit=50)
        >>> print(result['count'])  # Number of new leads
    """
    pass
```

### Import Order
```python
# 1. Standard library
import os
import sys
from datetime import datetime

# 2. Third-party packages
from flask import Flask, render_template
from sqlalchemy import Column, String

# 3. Local imports
from app.models import User, Distributor
from app.services import MetaLeadService
```

---

## 🧪 Testing Requirements

### Write Tests For:
- New functions/methods
- Bug fixes (test should fail without fix)
- Important features
- API endpoints

### Test File Structure
```python
# tests/test_meta_lead_service.py
import pytest
from app.services.meta_lead_service import MetaLeadService
from app.models.meta_lead import MetaAPIConfig

class TestMetaLeadService:
    """Tests for MetaLeadService"""
    
    @pytest.fixture
    def config(self):
        """Create test config"""
        return MetaAPIConfig(
            page_id="123456",
            form_id="654321",
            access_token="token123"
        )
    
    def test_connection_valid_config(self, config):
        """Test connection with valid config"""
        service = MetaLeadService(config)
        success, message = service.test_connection()
        assert isinstance(success, bool)
        assert isinstance(message, str)
    
    def test_connection_invalid_token(self):
        """Test connection with invalid token"""
        config = MetaAPIConfig(
            page_id="123456",
            form_id="654321",
            access_token="invalid"
        )
        service = MetaLeadService(config)
        success, message = service.test_connection()
        assert success is False
```

### Run Tests
```bash
# Run all tests
python -m pytest

# Run specific test
python -m pytest tests/test_meta_lead_service.py::TestMetaLeadService::test_connection_valid_config

# Run with coverage
python -m pytest --cov=app tests/

# Verbose output
python -m pytest -v
```

---

## 📚 Documentation Requirements

### Update Documentation For:
- New features
- API endpoints
- Configuration changes
- Database schema changes

### Documentation Files
- **README.md** - Project overview
- **SETUP.md** - Installation guide
- **API_REFERENCE.md** - API endpoints
- **CHANGELOG.md** - Change history
- Code comments/docstrings

---

## 🚀 Pull Request Process

### 1. Before Submitting
- [ ] Code follows PEP 8 style guide
- [ ] All tests pass: `python -m pytest`
- [ ] Code coverage doesn't decrease
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts with `main`
- [ ] Commits are squashed if appropriate

### 2. PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #123

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass locally

## Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] CHANGELOG.md updated

## Screenshots (if applicable)
[Add screenshots here]
```

### 3. Code Review Process
- Maintainers review your PR
- May request changes
- Address feedback
- PR gets merged when approved

### 4. After Merge
- Your branch is deleted
- Credit given in release notes
- Thank you! 🎉

---

## 📋 Commit Message Guidelines

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation change
- `style:` Code style (no logic change)
- `refactor:` Code restructuring
- `test:` Test updates
- `chore:` Maintenance tasks

### Examples
```bash
git commit -m "feat(leads): add lead quality scoring"
git commit -m "fix(meta-api): handle connection timeout"
git commit -m "docs: update README with setup steps"
git commit -m "refactor(services): simplify lead import logic"
```

---

## 🔐 Code Review Checklist

When reviewing code, check:

- **Functionality:** Does it work as intended?
- **Code Quality:** Is it readable and maintainable?
- **Testing:** Are tests present and comprehensive?
- **Documentation:** Is it well documented?
- **Performance:** Are there performance concerns?
- **Security:** Any security vulnerabilities?
- **Style:** Does it follow guidelines?
- **Compatibility:** Does it break anything?

---

## 📞 Communication

- **Issues:** For bugs and features
- **Discussions:** For questions and ideas
- **Email:** mshjiyan@gmail.com
- **GitHub:** @mshjiyan-a11y

---

## 🎓 Learning Resources

- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [How to Write Good Commit Messages](https://cbea.ms/git-commit/)
- [Python Code Style (PEP 8)](https://pep8.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

## ✨ Recognition

Contributors are recognized in:
- GitHub Contributors page
- Release notes
- README.md credits

Thank you for contributing to MSH Med Tour! 🙏

---

**Last Updated:** November 14, 2025  
**Maintained by:** Jiyan
