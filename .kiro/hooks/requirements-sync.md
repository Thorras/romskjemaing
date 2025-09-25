# Requirements Sync Hook

## Trigger
- **Event**: File saved
- **File Pattern**: `requirements.txt, pyproject.toml, setup.py, Pipfile`

## Description
Automatically synchronizes project dependencies and checks for conflicts when dependency files are modified.

## Instructions
When a dependency file is modified:

1. Detect the dependency management system in use:
   - pip (requirements.txt)
   - poetry (pyproject.toml)
   - pipenv (Pipfile)
   - setuptools (setup.py)

2. Check for dependency conflicts:
   ```bash
   # For pip
   pip check
   
   # For poetry
   poetry check
   
   # For pipenv
   pipenv check
   ```

3. Validate critical dependencies for IFC Room Schedule:
   - IfcOpenShell (ensure compatible version)
   - PyQt6 (check for version compatibility)
   - pytest (for testing framework)
   - Required Python version compatibility

4. Generate dependency report:
   - List of added/removed/updated packages
   - Version compatibility matrix
   - Security vulnerability scan (if available)
   - License compatibility check

5. Update virtual environment if needed:
   ```bash
   pip install -r requirements.txt
   # or
   poetry install
   ```

6. Run quick smoke test to ensure imports work:
   ```python
   import ifcopenshell
   import PyQt6
   # Test critical imports
   ```

7. Update documentation if major dependencies change

## Success Criteria
- Dependencies stay synchronized across environments
- Early detection of version conflicts
- Automatic environment updates when possible
- Clear reporting of dependency changes