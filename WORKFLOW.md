# Quick Workflow Guide

## Daily Development Cycle

```bash
# 1. Start working on a new feature
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 2. Make your changes
# ... edit files ...

# 3. Run quality checks
make dev-test

# 4. Commit with conventional message
git add .
git commit -m "feat: add your feature description"

# 5. Push and create PR
git push origin feature/your-feature-name
# Create PR on GitHub
```

## Testing Before Commit

```bash
# Quick test
make test

# Full quality check
make dev-test

# Coverage report
make coverage
```

## Release Process

The project uses automated semantic versioning:

1. **Automatic Release** (recommended):
   - Push to main branch
   - Version is automatically determined from commit messages
   - Changelog is generated automatically
   - Package is published to PyPI

2. **Manual Release**:
   ```bash
   make version  # Check current version
   make build    # Build package
   make tag      # Create and push tag
   ```

## Commit Message Examples

```bash
git commit -m "feat: add new resource validation feature"
git commit -m "fix: resolve RID parsing issue with special characters"
git commit -m "docs: update installation instructions"
git commit -m "refactor: simplify resource initialization logic"
git commit -m "test: add comprehensive tests for edge cases"
```

## Pre-commit Hooks

When you run `git commit`, these hooks automatically run:
- Code formatting with black and ruff
- Linting with ruff
- Type checking with mypy
- Running pytest tests

If any hook fails, the commit is aborted and you'll need to fix the issues.

## Quick Commands

```bash
make help          # Show all available commands
make install-dev   # Set up development environment
make fix           # Auto-fix formatting issues
make clean         # Clean build artifacts
make version       # Show current version
```
