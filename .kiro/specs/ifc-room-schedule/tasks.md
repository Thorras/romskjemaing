# Implementation Plan

## Current Status

Project structure is established with all modules created and dependencies installed. All implementation files currently contain placeholder classes that need to be implemented with actual functionality. Tests pass for basic imports and project structure.

**Note:** Additional export formats (CSV, Excel, PDF) have been added to the codebase beyond the original JSON requirement. These are included in the task list as optional enhancements.

- [x] 1. Set up Python project structure and dependencies

  - Create Python package structure with main modules (parser, ui, data, export)
  - Install and configure IfcOpenShell library for IFC file processing
  - Set up PyQt6 dependencies and basic application structure
  - Create requirements.txt and basic project configuration
  - _Requirements: 1.1, 1.2_

- [x] 2. Implement IFC file loading and validation

  - Create IfcFileReader class using IfcOpenShell for file loading
  - Implement IFC file format validation and error handling
  - Add file dialog functionality using QFileDialog
  - Write unit tests for file validation logic using pytest
  - _Requirements: 1.1, 1.2, 1.3, 5.1, 5.3_

- [x] 3. Implement Python data models and storage

  - Create SpaceData, SurfaceData, SpaceBoundaryData, and RelationshipData dataclasses
  - Implement SpaceRepository for in-memory data management
  - Add SpaceBoundaryManager for boundary data operations
  - Add data validation and integrity checks
  - Write unit tests for data models and storage operations
  - _Requirements: 2.1, 2.4, 4.4, 5.4, 7.1_

- [x] 4. Create IFC parser for space extraction

  - Implement IfcSpaceExtractor class to parse IfcSpace entities
  - Extract space properties: GUID, Name, LongName, ObjectType, quantities
  - Handle IFC parsing errors gracefully with detailed error messages
  - Write unit tests for space extraction functionality
  - _Requirements: 1.4, 2.8, 2.9, 5.1, 5.2_

- [x] 4.1 Implement IfcSpaceBoundary parser

  - Create IfcSpaceBoundaryParser class to extract IfcSpaceBoundary entities
  - Parse boundary properties: GUID, Name, PhysicalOrVirtualBoundary, InternalOrExternalBoundary
  - Extract related building element and space references with element type classification
  - Parse connection geometry and calculate boundary areas from IFC geometric representations
  - Implement boundary orientation detection (North, South, East, West, Horizontal) from geometry
  - Generate human-readable display labels (e.g., "North Wall to Office 101")
  - Classify boundary surface types based on building element types
  - Handle missing or invalid boundary data gracefully

  - Write unit tests for space boundary extraction, area calculations, and identification
  - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.7, 7.8_

- [x] 5. Build PyQt main window and space navigation

  - Enhance MainWindow class with menu bar and toolbar for file operations
  - Implement SpaceListWidget using QListWidget for space navigation
  - Connect file dialog to IFC file loading functionality
  - Display space properties (GUID, Name, LongName, ObjectType) in UI
  - Write integration tests for PyQt UI components

  - _Requirements: 4.1, 4.2, 4.3, 2.6_

- [x] 6. Implement surface data extraction and display

  - Extract surface data associated with each IFC space using IfcOpenShell
  - Calculate surface areas by type (walls, floors, ceilings)

  - Create SpaceDetailWidget to display surface properties
  - Handle missing or incomplete surface data gracefully in UI
  - Write unit tests for surface calculations and display
  - _Requirements: 2.1, 2.2, 2.6, 5.2_

- [x] 6.1 Implement space boundary data extraction and display

  - Extract space boundary data for each IFC space using IfcSpaceBoundaryParser
  - Calculate accurate boundary areas from IFC geometric representations
  - Enhance SpaceDetailWidget to display space boundary properties with human-readable labels
  - Show differentiation between Physical, Virtual, and Undefined boundaries
  - Display boundary orientation, surface type, and adjacent spaces/elements
  - Show related building elements and their material properties
  - Implement clear visual identification of what each boundary represents

  - Handle cases where space boundaries are missing or incomplete
  - Write unit tests for boundary area calculations and UI display
  - _Requirements: 2.3, 2.7, 2.10, 7.2, 7.3, 7.5, 7.7, 7.8_

- [x] 7. Create PyQt surface and boundary description editor

  - Build SurfaceEditorWidget using QTextEdit for surface descriptions
  - Extend editor to handle space boundary descriptions

  - Implement real-time saving of both surface and boundary descriptions
  - Add QValidator for user input validation with error messages
  - Ensure descriptions persist when navigating between spaces
  - Create tabbed interface to switch between surfaces and boundaries
  - Write integration tests for description editing workflow
  - _Requirements: 2.4, 2.5, 4.4, 5.3_

- [x] 8. Implement IFC relationship parsing

  - Parse relationships between IFC spaces and other entities using IfcOpenShell
  - Extract GUID, Name, and Description for related entities
  - Categorize relationships by type (contains, adjacent, serves)

  - Handle cases where no relationships exist
  - Write unit tests for relationship parsing and categorization
  - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [x] 8.1 Implement space boundary level differentiation

  - Identify and categorize 1st level boundaries (space-to-building-element)
  - Identify and categorize 2nd level boundaries (space-to-space)
  - Extract thermal and material properties from related building elements
  - Handle boundary hierarchies and parent-child relationships
  - Write unit tests for boundary level classification
  - _Requirements: 7.4, 7.5_

- [x] 9. Build JSON export engine

  - Create JsonBuilder class to construct export data structure
  - Include all space data, surfaces, space boundaries, relationships, and user descriptions
  - Generate metadata including export date and source file information

  - Implement separate sections for surfaces and space boundaries in JSON structure
  - Include boundary geometry, connection types, and calculated areas in export
  - Implement data validation before export
  - Write unit tests for JSON structure and data completeness
  - _Requirements: 3.1, 3.2, 3.8, 3.9, 3.5, 3.6, 3.7, 6.4, 7.7_

- [x] 10. Implement PyQt export functionality

  - Create ExportDialogWidget using QDialog for export options
  - Generate JSON file using Python's json module with QFileDialog
  - Add QMessageBox warning for incomplete data before export
  - Include summary statistics in export data
  - Write integration tests for complete export workflow
  - _Requirements: 3.3, 3.4, 5.4_

- [ ] 11. Add comprehensive error handling with PyQt

  - Implement QMessageBox for IFC parsing error display
  - Add user-friendly error messages with QStatusBar updates
  - Create error recovery mechanisms for partial data processing
  - Use QThread for long-running operations to prevent UI freezing
  - Write tests for error scenarios and recovery
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 12. Implement additional export formats (CSV, Excel, PDF)

  - Implement CsvExporter class for CSV format export
  - Implement ExcelExporter class using openpyxl for Excel export
  - Implement PdfExporter class using reportlab for PDF export
  - Add export format selection to ExportDialogWidget
  - Write unit tests for each export format
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 13. Create end-to-end integration tests
  - Test complete workflow from IFC import to JSON export
  - Validate data integrity throughout the entire process using pytest
  - Test with various IFC file formats and sizes
  - Verify export data matches imported and processed data
  - Test PyQt UI interactions and error handling scenarios
  - _Requirements: All requirements integration testing_
