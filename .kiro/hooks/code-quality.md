# Code Quality Hook

## Trigger
- **Event**: File saved
- **File Pattern**: `**/*.py`

## Description
Ensures consistent code quality by running linting, formatting, and type checking on Python files when saved.

## Instructions
When a Python file is saved:

1. Run code formatting with black:
   ```bash
   black --line-length 88 {file_path}
   ```

2. Run linting with flake8:
   ```bash
   flake8 {file_path} --max-line-length=88 --extend-ignore=E203,W503
   ```

3. Run type checking with mypy (if type hints present):
   ```bash
   mypy {file_path} --ignore-missing-imports
   ```

4. Check import sorting with isort:
   ```bash
   isort {file_path} --profile black
   ```

5. Report any issues found:
   - Format violations (auto-fix if possible)
   - Linting errors with line numbers
   - Type checking warnings
   - Import organization issues

6. For PyQt files, ensure proper signal/slot type hints
7. For IFC parsing files, validate IfcOpenShell usage patterns

## Configuration
Create or update these config files:
- `.flake8` for linting rules
- `pyproject.toml` for black and isort configuration
- `mypy.ini` for type checking settings

## Success Criteria
- Code automatically formatted on save
- Immediate feedback on code quality issues
- Consistent code style across the project
- Type safety improvements over time