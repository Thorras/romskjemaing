# Test Runner Hook

## Trigger
- **Event**: File saved
- **File Pattern**: `**/*.py`
- **Exclude Pattern**: `**/test_*.py, **/*_test.py`

## Description
Automatically runs relevant unit tests when Python source files are saved to ensure code changes don't break existing functionality.

## Instructions
When a Python file is saved:

1. Identify the saved file and determine related test files
2. Run pytest on the specific test files or test directory
3. If no specific tests found, run all tests in the project
4. Display test results in a clear format showing:
   - Number of tests passed/failed
   - Any failing test details
   - Coverage information if available
5. If tests fail, highlight the specific issues and suggest fixes
6. For IFC-related modules, ensure IfcOpenShell tests run properly

Example commands to run:
```bash
# Run specific test file
pytest tests/test_ifc_parser.py -v

# Run all tests with coverage
pytest --cov=src --cov-report=term-missing

# Run tests for specific module
pytest tests/ -k "test_space_extraction"
```

## Success Criteria
- Tests run automatically without manual intervention
- Clear feedback on test status
- Quick identification of broken functionality
- Minimal performance impact on development workflow