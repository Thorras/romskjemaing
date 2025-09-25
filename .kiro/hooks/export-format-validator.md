# Export Format Validator Hook

## Trigger
- **Event**: File saved
- **File Pattern**: `**/export*.py, **/json*.py, **/*export*.py`

## Description
Validates JSON export format and schema compliance when export-related code is modified.

## Instructions
When export functionality code is saved:

1. Validate JSON schema compliance:
   ```python
   import jsonschema
   # Validate against defined room schedule schema
   ```

2. Generate sample export data:
   - Create test JSON output with sample IFC data
   - Validate structure matches specification
   - Check for required fields and data types

3. Test export functionality:
   - Run export with various space configurations
   - Test edge cases (empty spaces, missing data)
   - Validate metadata generation
   - Check file size and performance

4. Schema validation checks:
   - Required fields presence
   - Data type compliance
   - Nested object structure
   - Array format consistency

5. Generate export documentation:
   - JSON schema definition
   - Field descriptions and examples
   - Usage guidelines
   - Integration examples

6. Create validation report:
   ```json
   {
     "schema_version": "1.0",
     "validation_status": "passed",
     "sample_exports": ["example1.json", "example2.json"],
     "issues_found": [],
     "recommendations": []
   }
   ```

7. Test backward compatibility:
   - Ensure new exports work with existing consumers
   - Validate version migration paths
   - Check for breaking changes

8. Performance validation:
   - Export time for large datasets
   - Memory usage during export
   - File size optimization

## Success Criteria
- JSON exports always match defined schema
- Consistent export format across versions
- Early detection of format breaking changes
- Comprehensive export testing coverage