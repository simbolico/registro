# Development Guide

This document outlines the development workflow for the Registro project.

## Development Workflow

### 1. Feature Development

```bash
# Create a new feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Run tests and linting locally
python -m pytest
ruff check .
black --check .
mypy registro

# Commit with conventional commits
git add .
git commit -m "feat: add new feature description"

# Push and create PR
git push origin feature/your-feature-name
```

### 2. Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for code formatting changes
- `refactor:` for code refactoring
- `test:` for adding or updating tests
- `chore:` for maintenance tasks

### 3. Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

- **Black**: Code formatting
- **Ruff**: Linting and formatting
- **MyPy**: Type checking
- **Pytest**: Run tests
- **File checks**: YAML/JSON validation, merge conflict detection

Install pre-commit hooks:

```bash
pre-commit install
```

### 4. Testing

Run tests locally:

```bash
# Run all tests with coverage
python -m pytest --cov=registro --cov-report=term-missing

# Run specific test file
python -m pytest tests/unit/test_rid.py

# Run with verbose output
python -m pytest -v
```

### 5. Code Quality Standards

- **Coverage**: 100% test coverage required
- **Type checking**: All code must pass MyPy checks
- **Linting**: All code must pass Ruff checks
- **Formatting**: All code must be properly formatted with Black

## Release Process

### Automated Semantic Release

The project uses semantic-release for automatic versioning and publishing:

1. Commits to `main` trigger the semantic release workflow
2. Version is automatically determined based on commit messages
3. Changelog is automatically generated
4. Package is built and published to PyPI
5. Git tag is created and pushed

### Version Bumping

Versions are bumped automatically based on commit messages:

- `feat:` commits trigger minor version bump (0.1.0 → 0.2.0)
- `fix:` commits trigger patch version bump (0.1.0 → 0.1.1)
- `BREAKING CHANGE:` commits trigger major version bump (0.1.0 → 1.0.0)

### Manual Release

For manual releases:

```bash
# Tag a version
git tag v0.1.0
git push origin v0.1.0
```

This will trigger the publish workflow manually.

## Project Structure

```
registro/
├── .github/workflows/    # CI/CD workflows
├── registro/            # Main package
│   ├── core/           # Core functionality
│   ├── models/         # Data models
│   ├── config/         # Configuration
│   └── __init__.py     # Package initialization
├── tests/              # Test suite
├── examples/           # Usage examples
├── pyproject.toml      # Project configuration
├── README.md           # Project documentation
├── CHANGELOG.md        # Auto-generated changelog
└── LICENSE             # MIT License
```

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/simbolico/registro.git
cd registro
```

2. Install dependencies:

```bash
# Using pip
python -m pip install -e .[dev]

# Using uv (recommended)
uv pip install -e .[dev]
```

3. Install pre-commit hooks:

```bash
pre-commit install
```

4. Run tests to verify setup:

```bash
python -m pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper test coverage
4. Follow commit message conventions
5. Submit a pull request

## Best Practices

- Write tests for all new functionality
- Maintain 100% test coverage
- Use type hints consistently
- Follow existing code style
- Update documentation when needed
- Keep dependencies minimal
- Use conventional commit messages
