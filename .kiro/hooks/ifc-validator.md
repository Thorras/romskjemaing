# IFC File Validator Hook

## Trigger
- **Event**: File added or modified
- **File Pattern**: `**/*.ifc, **/*.ifcxml, **/*.ifczip`

## Description
Validates IFC files when they are added to the project to ensure test data integrity and compatibility.

## Instructions
When an IFC file is added or modified:

1. Validate IFC file format using IfcOpenShell:
   ```python
   import ifcopenshell
   try:
       ifc_file = ifcopenshell.open(file_path)
       # Validation successful
   except Exception as e:
       # Report validation error
   ```

2. Extract and report basic file information:
   - IFC schema version (IFC2X3, IFC4, etc.)
   - File size and entity count
   - Presence of IfcSpace entities
   - Spatial structure hierarchy

3. Generate validation report including:
   - File format compliance
   - Required entities for room schedule functionality
   - Potential parsing issues
   - Recommendations for test coverage

4. For test files, ensure they contain:
   - At least one IfcSpace entity
   - Surface/boundary representations
   - Relationship data
   - Property sets and quantities

5. Create summary report in `tests/ifc_validation_report.md`

6. If validation fails, provide specific guidance on:
   - File format issues
   - Missing required entities
   - Compatibility concerns

## Success Criteria
- All IFC test files are validated automatically
- Clear feedback on file compatibility
- Early detection of problematic test data
- Comprehensive validation reporting