# Documentation Generator Hook

## Trigger
- **Event**: File saved
- **File Pattern**: `**/*.py`
- **Condition**: File contains docstrings or class/function definitions

## Description
Automatically generates and updates API documentation when code with docstrings is modified.

## Instructions
When Python files with documentation are saved:

1. Scan for docstring changes in:
   - Class definitions
   - Function/method definitions
   - Module-level documentation
   - Type hints and annotations

2. Generate API documentation using Sphinx or similar:
   ```bash
   sphinx-apidoc -o docs/api src/
   sphinx-build -b html docs/ docs/_build/html
   ```

3. Update specific documentation sections:
   - IFC Parser API reference
   - PyQt UI component documentation
   - Data model specifications
   - Export engine interface

4. Generate code examples for key functions:
   - IFC file loading examples
   - Space extraction usage
   - Export functionality demos

5. Create or update:
   - `docs/api/` - Auto-generated API docs
   - `README.md` - Usage examples
   - `docs/user_guide.md` - User documentation
   - `docs/developer_guide.md` - Developer reference

6. Validate documentation:
   - Check for broken internal links
   - Ensure code examples are syntactically correct
   - Verify docstring format compliance

7. For PyQt components, generate UI documentation:
   - Widget hierarchy
   - Signal/slot connections
   - User interaction flows

## Success Criteria
- Documentation stays current with code changes
- API reference is always accurate
- Code examples remain functional
- Clear developer and user guides