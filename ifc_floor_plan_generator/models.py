"""
Core data models for IFC Floor Plan Generator.

Defines the main data structures used throughout the system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime


@dataclass
class Polyline2D:
    """Represents a 2D polyline with associated IFC metadata."""
    points: List[Tuple[float, float]]
    ifc_class: str
    element_guid: str
    is_closed: bool = False
    
    def __post_init__(self):
        """Validate polyline data after initialization."""
        if len(self.points) < 2:
            raise ValueError("Polyline must have at least 2 points")
        if not self.element_guid:
            raise ValueError("Element GUID is required")
        if not self.ifc_class:
            raise ValueError("IFC class is required")


@dataclass
class BoundingBox:
    """Represents a 2D bounding box."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    def __post_init__(self):
        """Validate bounding box after initialization."""
        if self.min_x > self.max_x:
            raise ValueError("min_x cannot be greater than max_x")
        if self.min_y > self.max_y:
            raise ValueError("min_y cannot be greater than max_y")
    
    @property
    def width(self) -> float:
        """Get the width of the bounding box."""
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        """Get the height of the bounding box."""
        return self.max_y - self.min_y
    
    @property
    def center(self) -> Tuple[float, float]:
        """Get the center point of the bounding box."""
        return ((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)


@dataclass
class StoreyResult:
    """Results from processing a single building storey."""
    storey_name: str
    polylines: List[Polyline2D]
    bounds: BoundingBox
    cut_height: float
    element_count: int
    svg_file: Optional[str] = None
    geojson_file: Optional[str] = None
    
    def __post_init__(self):
        """Validate storey result after initialization."""
        if not self.storey_name:
            raise ValueError("Storey name is required")
        if self.element_count < 0:
            raise ValueError("Element count cannot be negative")


@dataclass
class ProcessingError:
    """Represents an error that occurred during processing."""
    error_code: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate error after initialization."""
        if not self.error_code:
            raise ValueError("Error code is required")
        if not self.message:
            raise ValueError("Error message is required")


@dataclass
class ManifestData:
    """Manifest data for the processing results."""
    input_file: str
    generated_at: datetime
    storeys: List[Dict[str, Any]]
    config_used: Dict[str, Any]
    total_elements: int = 0
    processing_time_seconds: float = 0.0
    
    def __post_init__(self):
        """Validate manifest data after initialization."""
        if not self.input_file:
            raise ValueError("Input file path is required")
        if self.total_elements < 0:
            raise ValueError("Total elements cannot be negative")


@dataclass
class ProcessingResult:
    """Complete results from IFC floor plan generation."""
    storeys: List[StoreyResult]
    manifest: ManifestData
    errors: List[ProcessingError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    success: bool = True
    
    def __post_init__(self):
        """Validate processing result after initialization."""
        # Mark as failed if there are critical errors
        critical_error_codes = ["IFC_OPEN_FAILED", "NO_STOREYS_FOUND", "WRITE_FAILED"]
        has_critical_errors = any(
            error.error_code in critical_error_codes for error in self.errors
        )
        if has_critical_errors:
            self.success = False
    
    def add_error(self, error_code: str, message: str, context: Dict[str, Any] = None) -> None:
        """Add an error to the processing result."""
        error = ProcessingError(
            error_code=error_code,
            message=message,
            context=context or {}
        )
        self.errors.append(error)
        
        # Update success status if critical error
        critical_error_codes = ["IFC_OPEN_FAILED", "NO_STOREYS_FOUND", "WRITE_FAILED"]
        if error_code in critical_error_codes:
            self.success = False
    
    def add_warning(self, message: str) -> None:
        """Add a warning to the processing result."""
        self.warnings.append(message)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


# Configuration data classes
@dataclass
class StoreyConfig:
    """Configuration for a specific building storey."""
    cut_offset_m: float
    
    def __post_init__(self):
        """Validate storey config after initialization."""
        if self.cut_offset_m < 0:
            raise ValueError("Cut offset must be non-negative")


@dataclass
class ClassFilters:
    """Configuration for IFC class filtering."""
    include_ifc_classes: List[str] = field(default_factory=list)
    exclude_ifc_classes: List[str] = field(default_factory=list)
    
    def should_include_class(self, ifc_class: str) -> bool:
        """Determine if an IFC class should be included based on filters."""
        # Exclude takes priority over include
        if ifc_class in self.exclude_ifc_classes:
            return False
        
        # If include list is empty, include all (except excluded)
        if not self.include_ifc_classes:
            return True
        
        # Otherwise, only include if in include list
        return ifc_class in self.include_ifc_classes


@dataclass
class UnitsConfig:
    """Configuration for units handling."""
    auto_detect_units: bool = True
    unit_scale_to_m: Optional[float] = None
    
    def __post_init__(self):
        """Validate units config after initialization."""
        if self.unit_scale_to_m is not None and self.unit_scale_to_m <= 0:
            raise ValueError("Unit scale must be positive")


@dataclass
class GeometryConfig:
    """Configuration for geometry generation."""
    use_world_coords: bool = True
    subtract_openings: bool = True
    sew_shells: bool = True
    cache_geometry: bool = True


@dataclass
class TolerancesConfig:
    """Configuration for geometric tolerances."""
    slice_tol: float = 1e-6
    chain_tol: float = 1e-3
    
    def __post_init__(self):
        """Validate tolerances config after initialization."""
        if self.slice_tol <= 0:
            raise ValueError("Slice tolerance must be positive")
        if self.chain_tol <= 0:
            raise ValueError("Chain tolerance must be positive")


@dataclass
class RenderingConfig:
    """Configuration for rendering output."""
    default_color: str = "#000000"
    default_linewidth_px: float = 1.0
    background: Optional[str] = None
    invert_y: bool = True
    class_styles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate rendering config after initialization."""
        if self.default_linewidth_px <= 0:
            raise ValueError("Default linewidth must be positive")


@dataclass
class OutputConfig:
    """Configuration for output files."""
    svg_filename_pattern: str = "{index:02d}_{storey_name}.svg"
    geojson_filename_pattern: str = "{index:02d}_{storey_name}.geo.json"
    manifest_filename: str = "manifest.json"
    write_geojson: bool = True


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""
    multiprocessing: bool = False
    max_workers: Optional[int] = None
    
    def __post_init__(self):
        """Validate performance config after initialization."""
        if self.max_workers is not None and self.max_workers <= 0:
            raise ValueError("Max workers must be positive")


@dataclass
class Config:
    """Main configuration for IFC Floor Plan Generator."""
    input_path: str
    output_dir: str
    cut_offset_m: float
    per_storey_overrides: Dict[str, StoreyConfig] = field(default_factory=dict)
    class_filters: ClassFilters = field(default_factory=ClassFilters)
    units: UnitsConfig = field(default_factory=UnitsConfig)
    geometry: GeometryConfig = field(default_factory=GeometryConfig)
    tolerances: TolerancesConfig = field(default_factory=TolerancesConfig)
    rendering: RenderingConfig = field(default_factory=RenderingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    def __post_init__(self):
        """Validate main config after initialization."""
        if not self.input_path:
            raise ValueError("Input path is required")
        if not self.output_dir:
            raise ValueError("Output directory is required")
        if self.cut_offset_m < 0:
            raise ValueError("Cut offset must be non-negative")
    
    def get_storey_cut_height(self, storey_name: str) -> float:
        """Get the cut height for a specific storey, considering overrides."""
        if storey_name in self.per_storey_overrides:
            return self.per_storey_overrides[storey_name].cut_offset_m
        return self.cut_offset_m