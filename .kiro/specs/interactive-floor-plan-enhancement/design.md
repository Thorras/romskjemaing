# Interactive Floor Plan Enhancement - Design Document

## Overview

This design addresses critical issues in the IFC Room Schedule application and introduces comprehensive floor plan visualization capabilities. The enhancement will fix the existing SpaceDetailWidget interface bug and implement an interactive floor plan view that displays complete building layouts with all spaces visible simultaneously.

The solution leverages the existing PyQt6-based architecture and extends the current visualization framework to provide intuitive navigation, space selection synchronization, and enhanced visual feedback for better spatial understanding.

## Architecture

### High-Level Architecture

The enhancement follows the existing MVC pattern and integrates with the current UI framework:

```
┌─────────────────────────────────────────────────────────────┐
│                    MainWindow                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   SpaceList     │  │   FloorPlan     │  │ SpaceDetail │ │
│  │    Widget       │  │    Widget       │  │   Widget    │ │
│  │                 │  │                 │  │             │ │
│  │ - Space List    │  │ - Floor Canvas  │  │ - Properties│ │
│  │ - Search/Filter │  │ - Floor Selector│  │ - Surfaces  │ │
│  │ - Selection     │  │ - Navigation    │  │ - Boundaries│ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────────────┐
                    │ FloorPlanCanvas │
                    │                 │
                    │ - 2D Rendering  │
                    │ - Interaction   │
                    │ - Zoom/Pan      │
                    │ - Selection     │
                    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │ GeometryExtractor│
                    │                 │
                    │ - IFC Parsing   │
                    │ - 2D Conversion │
                    │ - Floor Grouping│
                    └─────────────────┘
```

### Component Integration

The design integrates with existing components:

1. **MainWindow**: Enhanced to include the new FloorPlanWidget and coordinate between all UI components
2. **SpaceListWidget**: Extended with floor filtering and bidirectional selection synchronization
3. **SpaceDetailWidget**: Interface bug fixed and enhanced with floor plan integration
4. **FloorPlanCanvas**: Existing component enhanced with multi-floor support and improved interactions
5. **GeometryExtractor**: Enhanced to support floor-level geometry extraction and space grouping

## Components and Interfaces

### 1. FloorPlanWidget (New Component)

**Purpose**: Main container widget that manages floor plan display and navigation controls.

**Key Responsibilities**:
- Floor level selection and switching
- Integration between floor plan canvas and other UI components
- Navigation controls (zoom, pan, fit-to-view)
- Floor-specific space filtering

**Interface**:
```python
class FloorPlanWidget(QWidget):
    # Signals
    space_selected = pyqtSignal(str)  # space_guid
    floor_changed = pyqtSignal(str)   # floor_id
    
    # Methods
    def set_floor_geometry(self, floor_geometries: Dict[str, FloorGeometry])
    def highlight_spaces(self, space_guids: List[str])
    def set_current_floor(self, floor_id: str)
    def zoom_to_spaces(self, space_guids: List[str])
    def zoom_to_fit(self)
```

### 2. Enhanced FloorPlanCanvas

**Purpose**: 2D rendering widget for interactive floor plan visualization.

**Enhancements**:
- Multi-floor support with floor-specific rendering
- Enhanced space labeling with NS 3940 color coding
- Improved selection feedback and hover states
- Better zoom and pan controls with floor-aware boundaries

**New Interface Methods**:
```python
class FloorPlanCanvas(QWidget):
    # New signals
    floor_bounds_changed = pyqtSignal(QRectF)
    
    # Enhanced methods
    def set_floor_data(self, floor_geometry: FloorGeometry, floor_metadata: Dict)
    def set_space_color_scheme(self, color_scheme: Dict[str, QColor])
    def show_space_labels(self, show: bool, min_zoom_level: float = 0.5)
    def get_spaces_in_view(self) -> List[str]
```

### 3. FloorSelector (New Component)

**Purpose**: UI control for switching between building floors.

**Features**:
- Dropdown or tab-based floor selection
- Floor metadata display (name, elevation, space count)
- Visual indicators for floors with/without geometry

**Interface**:
```python
class FloorSelector(QWidget):
    floor_selected = pyqtSignal(str)  # floor_id
    
    def set_floors(self, floors: List[FloorLevel])
    def set_current_floor(self, floor_id: str)
    def get_current_floor(self) -> Optional[str]
```

### 4. Enhanced SpaceListWidget

**Purpose**: Extended space list with floor-aware filtering and synchronization.

**Enhancements**:
- Floor-based filtering option
- Visual indicators for spaces with/without geometry
- Enhanced search with floor context
- Bidirectional selection synchronization with floor plan

**New Interface Methods**:
```python
class SpaceListWidget(QWidget):
    # New signals
    floor_filter_changed = pyqtSignal(str)  # floor_id or "all"
    
    # Enhanced methods
    def set_floor_filter(self, floor_id: Optional[str])
    def highlight_spaces_on_floor_plan(self, space_guids: List[str])
    def sync_with_floor_plan_selection(self, space_guids: List[str])
```

### 5. Fixed SpaceDetailWidget

**Purpose**: Corrected interface and enhanced integration with floor plan.

**Bug Fixes**:
- Fixed method name inconsistencies causing AttributeError
- Standardized interface method names across all calling code
- Added proper error handling for missing methods

**Interface Corrections**:
```python
class SpaceDetailWidget(QWidget):
    # Fixed method names (standardized)
    def display_space(self, space: SpaceData)  # was: show_space_details
    def clear_selection(self)                  # was: clear_space
    def get_current_space(self) -> Optional[SpaceData]  # was: current_space
```

## Data Models

### Enhanced FloorLevel Model

```python
@dataclass
class FloorLevel:
    id: str
    name: str
    elevation: float
    spaces: List[str]  # space GUIDs
    has_geometry: bool = False
    space_count: int = 0
    total_area: float = 0.0
```

### Enhanced FloorGeometry Model

```python
@dataclass
class FloorGeometry:
    level: FloorLevel
    room_polygons: List[Polygon2D]
    bounds: Optional[Tuple[float, float, float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_spaces_by_type(self) -> Dict[str, List[str]]
    def get_color_scheme(self) -> Dict[str, QColor]
```

### Space Color Coding Model

```python
@dataclass
class SpaceColorScheme:
    """NS 3940 compliant color coding for space types"""
    
    # Standard NS 3940 categories
    OFFICE_SPACES = QColor(173, 216, 230)      # Light blue
    MEETING_ROOMS = QColor(144, 238, 144)      # Light green  
    CIRCULATION = QColor(255, 218, 185)        # Peach
    TECHNICAL_SPACES = QColor(221, 160, 221)   # Plum
    STORAGE = QColor(255, 255, 224)            # Light yellow
    SANITARY = QColor(255, 182, 193)           # Light pink
    DEFAULT = QColor(240, 240, 240)            # Light gray
    
    @classmethod
    def get_color_for_space_type(cls, space_type: str) -> QColor
```

## Error Handling

### SpaceDetailWidget Interface Fix

**Problem**: MainWindow calls non-existent methods on SpaceDetailWidget, causing AttributeError exceptions.

**Root Cause Analysis**:
- Method name inconsistencies between interface definition and implementation
- Missing error handling for method calls
- Inconsistent naming conventions across UI components

**Solution**:
1. **Standardize Method Names**: Ensure consistent naming across all components
2. **Add Interface Validation**: Implement runtime checks for method existence
3. **Graceful Degradation**: Handle missing methods without crashing
4. **Comprehensive Testing**: Add unit tests for all interface interactions

**Implementation**:
```python
class SpaceDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Ensure all expected methods exist
        self._validate_interface()
    
    def _validate_interface(self):
        """Validate that all expected interface methods exist"""
        required_methods = ['display_space', 'clear_selection', 'get_current_space']
        for method_name in required_methods:
            if not hasattr(self, method_name):
                raise AttributeError(f"Required method {method_name} not implemented")
```

### Geometry Extraction Error Handling

**Enhanced Error Recovery**:
- Graceful handling of spaces without geometry
- Fallback to simplified rectangular representations
- User feedback for geometry extraction issues
- Progressive loading for large files

## Testing Strategy

### Unit Tests

1. **Interface Compatibility Tests**
   - Verify all SpaceDetailWidget methods exist and work correctly
   - Test method signature consistency across components
   - Validate signal/slot connections

2. **Floor Plan Rendering Tests**
   - Test 2D geometry conversion accuracy
   - Verify zoom and pan functionality
   - Test space selection and highlighting

3. **Data Model Tests**
   - Validate FloorLevel and FloorGeometry data integrity
   - Test color scheme application
   - Verify space grouping by floor

### Integration Tests

1. **UI Component Synchronization**
   - Test bidirectional selection between space list and floor plan
   - Verify floor switching updates all components correctly
   - Test search filtering with floor context

2. **Geometry Processing**
   - Test IFC file loading with various floor configurations
   - Verify geometry extraction for different space types
   - Test error handling for malformed geometry data

3. **Performance Tests**
   - Test rendering performance with large floor plans (>100 spaces)
   - Verify memory usage during geometry extraction
   - Test responsiveness during zoom/pan operations

### User Acceptance Tests

1. **Navigation Workflow**
   - User can easily switch between floors
   - Zoom and pan controls work intuitively
   - Space selection is clear and responsive

2. **Visual Clarity**
   - Space boundaries are clearly visible
   - Color coding helps identify space types
   - Labels are readable at appropriate zoom levels

3. **Error Recovery**
   - Application handles missing geometry gracefully
   - User receives helpful feedback for issues
   - No crashes during normal operation

## Implementation Phases

### Phase 1: Interface Bug Fix (Priority: Critical)
- Fix SpaceDetailWidget method name inconsistencies
- Add interface validation and error handling
- Update all calling code to use correct method names
- Add unit tests for interface compatibility

### Phase 2: Enhanced Floor Plan Canvas (Priority: High)
- Extend FloorPlanCanvas with multi-floor support
- Implement space color coding based on NS 3940 standards
- Add enhanced labeling and visual feedback
- Improve zoom/pan controls with floor-aware boundaries

### Phase 3: Floor Plan Widget Integration (Priority: High)
- Create FloorPlanWidget container component
- Implement FloorSelector for floor switching
- Add navigation controls (zoom, pan, fit-to-view)
- Integrate with existing MainWindow layout

### Phase 4: Bidirectional Synchronization (Priority: Medium)
- Enhance SpaceListWidget with floor filtering
- Implement selection synchronization between components
- Add floor-aware search and filtering
- Test and refine user interaction workflows

### Phase 5: Visual Enhancements (Priority: Medium)
- Implement NS 3940 compliant color schemes
- Add space type icons and enhanced labeling
- Improve hover and selection visual feedback
- Add floor metadata display and statistics

### Phase 6: Performance Optimization (Priority: Low)
- Optimize rendering for large floor plans
- Implement spatial indexing for faster hit testing
- Add progressive loading for complex geometry
- Memory usage optimization for multiple floors

## Design Decisions and Rationales

### 1. PyQt6 Canvas-Based Rendering
**Decision**: Use PyQt6's QPainter for 2D floor plan rendering instead of web-based or OpenGL solutions.

**Rationale**: 
- Consistent with existing application architecture
- Better integration with Qt-based UI components
- Simpler deployment without additional dependencies
- Adequate performance for typical building floor plans

### 2. Floor-Centric Data Organization
**Decision**: Organize geometry data by building floors rather than as a flat space list.

**Rationale**:
- Matches user mental model of building navigation
- Enables efficient rendering of large buildings
- Supports floor-specific filtering and navigation
- Aligns with IFC building hierarchy standards

### 3. Bidirectional Selection Synchronization
**Decision**: Implement real-time synchronization between space list and floor plan selections.

**Rationale**:
- Provides intuitive user experience
- Reduces cognitive load when navigating between views
- Enables efficient space location and identification
- Supports both list-based and visual navigation workflows

### 4. NS 3940 Color Coding Standard
**Decision**: Implement color coding based on Norwegian NS 3940 standard for space classification.

**Rationale**:
- Provides standardized visual language for space types
- Improves spatial understanding and navigation
- Aligns with Norwegian building industry practices
- Enables quick visual identification of functional areas

### 5. Progressive Enhancement Approach
**Decision**: Implement features in phases with graceful degradation for missing data.

**Rationale**:
- Ensures application stability during development
- Provides value to users even with incomplete geometry data
- Enables iterative testing and user feedback
- Reduces risk of introducing breaking changes

This design provides a comprehensive solution that addresses all requirements while maintaining compatibility with the existing codebase and following established architectural patterns.