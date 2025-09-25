# Design Document - IFC Room Schedule Application

## Overview

The IFC Room Schedule application is a desktop tool built with Python and PyQt that enables building professionals to import IFC files, analyze spatial data, and generate structured room schedules. The application focuses on extracting IfcSpace entities and their associated surfaces, allowing users to add descriptions and export comprehensive JSON data.

The system follows a modular architecture with clear separation between IFC parsing, data processing, user interface, and export functionality. It leverages Python's robust ecosystem for IFC processing and PyQt for a native desktop user experience.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PyQt UI       │    │  IFC Parser     │    │  Data Manager   │
│                 │    │                 │    │                 │
│ - File Dialog   │◄──►│ - IfcOpenShell  │◄──►│ - Space Storage │
│ - Space List    │    │ - IFC Entities  │    │ - Relationships │
│ - Surface View  │    │ - Validation    │    │ - Descriptions  │
│ - Export Dialog │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Export Engine  │
                    │                 │
                    │ - JSON Builder  │
                    │ - File Writer   │
                    └─────────────────┘
```

### Technology Stack

- **Backend**: Python 3.8+
- **GUI Framework**: PyQt6 for native desktop interface
- **IFC Parsing**: IfcOpenShell library for robust IFC file processing
- **File Handling**: Python's built-in file I/O operations
- **Data Storage**: Python dictionaries and classes with optional SQLite for persistence
- **Export**: JSON serialization with Python's json module

## Components and Interfaces

### 1. IFC Parser Module

**Purpose**: Handle IFC file import, validation, and entity extraction

**Key Classes**:
- `IfcFileReader`: Manages file loading and initial validation
- `IfcSpaceExtractor`: Extracts IfcSpace entities and properties
- `IfcRelationshipParser`: Processes relationships between IFC entities

**Interface**:
```python
class IfcParser:
    def load_file(self, file_path: str) -> bool
    def extract_spaces(self) -> List[Dict]
    def get_space_properties(self, space_id: str) -> Dict
    def get_related_entities(self, space_id: str) -> List[Dict]
    def validate_file(self, file_path: str) -> Tuple[bool, str]
```

**Key Properties Extracted**:
- GlobalId (GUID)
- Name (space number/identifier)
- LongName (descriptive name)
- Description
- ObjectType (zone category)
- ElevationWithFlooring
- CompositionType
- BaseQuantities (Height, FinishFloorHeight, FinishCeilingHeight)

### 2. Space Data Manager

**Purpose**: Manage space data, user descriptions, and relationships

**Key Classes**:
- `SpaceRepository`: CRUD operations for space data
- `SurfaceManager`: Handle surface data and calculations
- `RelationshipManager`: Manage IFC entity relationships

**Interface**:
```python
class SpaceDataManager:
    def add_space(self, space_data: Dict) -> None
    def update_space_description(self, space_id: str, description: str) -> None
    def get_surfaces_by_space(self, space_id: str) -> List[Dict]
    def add_surface_description(self, surface_id: str, description: str) -> None
    def get_related_entities(self, space_id: str) -> List[Dict]
    def calculate_surface_areas(self, space_id: str) -> Dict
```

### 3. PyQt User Interface Components

**Purpose**: Provide native desktop interface for space navigation and data entry

**Key Components**:
- `MainWindow`: Primary application window with menu and toolbar
- `FileDialogWidget`: File selection and import functionality
- `SpaceListWidget`: QListWidget showing all imported spaces
- `SpaceDetailWidget`: QWidget displaying space properties and surfaces
- `SurfaceEditorWidget`: QTextEdit and forms for adding descriptions
- `ExportDialogWidget`: QDialog for configuring JSON export

**Interface Structure**:
```python
class MainWindow(QMainWindow):
    def setup_ui(self) -> None
    def load_ifc_file(self) -> None
    def display_spaces(self, spaces: List[Dict]) -> None
    def show_space_details(self, space_id: str) -> None
    def enable_surface_editing(self, surface_id: str) -> None
    def export_json(self) -> None

class SpaceListWidget(QListWidget):
    space_selected = pyqtSignal(str)
    
class SpaceDetailWidget(QWidget):
    surface_selected = pyqtSignal(str)
```

### 4. Export Engine

**Purpose**: Generate structured JSON output with all collected data

**Key Classes**:
- `JsonBuilder`: Construct JSON structure
- `DataValidator`: Ensure data completeness
- `FileWriter`: Handle file system operations

**Interface**:
```python
class ExportEngine:
    def build_json_structure(self, spaces: List[Dict], metadata: Dict) -> Dict
    def validate_export_data(self, data: Dict) -> Tuple[bool, List[str]]
    def write_json_file(self, filename: str, data: Dict) -> bool
    def generate_metadata(self) -> Dict
```

## Data Models

### Space Data Model

```python
@dataclass
class SpaceData:
    guid: str
    name: str
    long_name: str
    description: str
    object_type: str
    zone_category: str
    number: str
    elevation: float
    quantities: Dict[str, float]  # height, finishFloorHeight, etc.
    surfaces: List['SurfaceData']
    relationships: List['RelationshipData']
    user_descriptions: Dict[str, str]
    processed: bool = False
```

### Surface Data Model

```python
@dataclass
class SurfaceData:
    id: str
    type: str  # "Wall", "Floor", "Ceiling", "Opening"
    area: float
    material: str
    ifc_type: str
    related_space_guid: str
    user_description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
```

### Relationship Data Model

```python
@dataclass
class RelationshipData:
    related_entity_guid: str
    related_entity_name: str
    related_entity_description: str
    relationship_type: str  # "Contains", "Adjacent", "Serves", etc.
    ifc_relationship_type: str
```

### Export JSON Structure

```python
{
    "metadata": {
        "export_date": "ISO date string",
        "source_file": "string",
        "ifc_version": "string",
        "application_version": "string"
    },
    "spaces": [
        {
            "guid": "string",
            "properties": "SpaceData as dict",
            "surfaces": ["SurfaceData as dict"],
            "relationships": ["RelationshipData as dict"]
        }
    ],
    "summary": {
        "total_spaces": "int",
        "processed_spaces": "int",
        "total_surface_area": "float",
        "surface_area_by_type": "dict"
    }
}
```

## Error Handling

### File Processing Errors

- **Invalid IFC Format**: Display QMessageBox with specific validation errors
- **Corrupted Files**: Graceful degradation with partial data recovery
- **Large Files**: QProgressBar indicators and threaded processing
- **Memory Limitations**: Efficient data structures and garbage collection

### Data Processing Errors

- **Missing Properties**: Default values and clear indicators in UI
- **Invalid Relationships**: Skip invalid relationships, log to status bar
- **Calculation Errors**: Fallback to available data, mark uncertain values

### User Interface Errors

- **File Access Issues**: Handle permissions and file locks gracefully
- **UI Threading**: Use QThread for long-running operations
- **User Input Validation**: Real-time validation with QValidator classes

## Testing Strategy

### Unit Testing

- **IFC Parser**: Test with various IFC file formats using pytest
- **Data Models**: Validate data integrity and transformations
- **Calculations**: Verify surface area and quantity calculations
- **Export Engine**: Test JSON structure and data completeness

### Integration Testing

- **File Loading Flow**: End-to-end file processing workflow
- **UI Interactions**: Test PyQt signal/slot connections
- **Data Persistence**: Ensure data consistency across operations

### User Acceptance Testing

- **Workflow Testing**: Complete user journeys from import to export
- **Performance Testing**: Large IFC files and multiple spaces
- **Usability Testing**: Interface responsiveness and user experience
- **Cross-platform Testing**: Windows, macOS, and Linux compatibility

### Test Data Requirements

- Sample IFC files with various space configurations
- Files with missing or incomplete data
- Large files for performance testing
- Files with complex relationship structures