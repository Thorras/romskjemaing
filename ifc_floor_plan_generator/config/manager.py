"""
Configuration manager for IFC Floor Plan Generator.

Handles loading, validation, and access to configuration data.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Try to import jsonschema, but make it optional
try:
    import jsonschema
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    
    # Create a simple ValidationError class if jsonschema is not available
    class ValidationError(Exception):
        def __init__(self, message: str):
            self.message = message
            super().__init__(message)

from .models import (
    Config, ClassFilters, UnitsConfig, GeometryConfig, 
    TolerancesConfig, RenderingConfig, OutputConfig, 
    PerformanceConfig, StoreyConfig
)
from ..rendering.models import RenderStyle


class ConfigurationManager:
    """Manages configuration loading, validation, and access."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self._config: Optional[Config] = None
        self._schema: Optional[Dict[str, Any]] = None
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema for configuration validation."""
        if self._schema is None:
            # Find schema file relative to this module
            current_dir = Path(__file__).parent
            schema_path = current_dir.parent.parent / "docs" / "floorplandocs" / "config-schema.json"
            
            if not schema_path.exists():
                raise FileNotFoundError(f"Configuration schema not found at {schema_path}")
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                self._schema = json.load(f)
        
        return self._schema
    
    def load_config(self, config_path: str) -> Config:
        """Load configuration from JSON file.
        
        Args:
            config_path: Path to the JSON configuration file
            
        Returns:
            Config: Loaded and validated configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is not valid JSON
            ValidationError: If config doesn't match schema
            ValueError: If config values are invalid
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load JSON configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Validate against schema
        if not self.validate_config(config_data):
            raise ValidationError("Configuration validation failed")
        
        # Convert to Config dataclass
        self._config = self._dict_to_config(config_data)
        return self._config
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against JSON schema.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails with details
        """
        if HAS_JSONSCHEMA:
            try:
                schema = self._load_schema()
                validate(instance=config, schema=schema)
                return True
            except jsonschema.ValidationError as e:
                # Re-raise with more context
                raise ValidationError(f"Configuration validation failed: {e.message}")
            except Exception as e:
                raise ValidationError(f"Schema validation error: {str(e)}")
        else:
            # Basic validation without jsonschema
            return self._basic_validate_config(config)
    
    def _basic_validate_config(self, config: Dict[str, Any]) -> bool:
        """Basic configuration validation without jsonschema.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        required_fields = ["input_path", "output_dir"]
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"Required field '{field}' is missing")
            if not isinstance(config[field], str) or not config[field].strip():
                raise ValidationError(f"Field '{field}' must be a non-empty string")
        
        # Validate cut_offset_m if present
        if "cut_offset_m" in config:
            if not isinstance(config["cut_offset_m"], (int, float)) or config["cut_offset_m"] < 0:
                raise ValidationError("cut_offset_m must be a non-negative number")
        
        # Validate per_storey_overrides if present
        if "per_storey_overrides" in config:
            if not isinstance(config["per_storey_overrides"], dict):
                raise ValidationError("per_storey_overrides must be an object")
            
            for storey_name, storey_config in config["per_storey_overrides"].items():
                if not isinstance(storey_config, dict):
                    raise ValidationError(f"Storey config for '{storey_name}' must be an object")
                if "cut_offset_m" in storey_config:
                    if not isinstance(storey_config["cut_offset_m"], (int, float)) or storey_config["cut_offset_m"] < 0:
                        raise ValidationError(f"cut_offset_m for storey '{storey_name}' must be a non-negative number")
        
        # Validate class_filters if present
        if "class_filters" in config:
            class_filters = config["class_filters"]
            if not isinstance(class_filters, dict):
                raise ValidationError("class_filters must be an object")
            
            for filter_type in ["include_ifc_classes", "exclude_ifc_classes"]:
                if filter_type in class_filters:
                    if not isinstance(class_filters[filter_type], list):
                        raise ValidationError(f"{filter_type} must be an array")
                    if not all(isinstance(cls, str) for cls in class_filters[filter_type]):
                        raise ValidationError(f"All items in {filter_type} must be strings")
        
        return True
    
    def _dict_to_config(self, config_data: Dict[str, Any]) -> Config:
        """Convert configuration dictionary to Config dataclass.
        
        Args:
            config_data: Raw configuration dictionary
            
        Returns:
            Config: Converted configuration object
        """
        # Extract required fields
        input_path = config_data["input_path"]
        output_dir = config_data["output_dir"]
        cut_offset_m = config_data.get("cut_offset_m", 1.05)  # Default value
        
        # Convert per_storey_overrides
        per_storey_overrides = {}
        if "per_storey_overrides" in config_data:
            for storey_name, storey_data in config_data["per_storey_overrides"].items():
                per_storey_overrides[storey_name] = StoreyConfig(
                    cut_offset_m=storey_data["cut_offset_m"]
                )
        
        # Convert class_filters
        class_filters_data = config_data.get("class_filters", {})
        class_filters = ClassFilters(
            include_ifc_classes=class_filters_data.get("include_ifc_classes", []),
            exclude_ifc_classes=class_filters_data.get("exclude_ifc_classes", [])
        )
        
        # Convert units config
        units_data = config_data.get("units", {})
        units = UnitsConfig(
            auto_detect_units=units_data.get("auto_detect_units", True),
            unit_scale_to_m=units_data.get("unit_scale_to_m")
        )
        
        # Convert geometry config
        geometry_data = config_data.get("geometry", {})
        geometry = GeometryConfig(
            use_world_coords=geometry_data.get("use_world_coords", True),
            subtract_openings=geometry_data.get("subtract_openings", True),
            sew_shells=geometry_data.get("sew_shells", True)
        )
        
        # Convert tolerances config
        tolerances_data = config_data.get("tolerances", {})
        tolerances = TolerancesConfig(
            slice_tol=tolerances_data.get("slice_tol", 1e-6),
            chain_tol=tolerances_data.get("chain_tol", 1e-3)
        )
        
        # Convert rendering config
        rendering_data = config_data.get("rendering", {})
        rendering = RenderingConfig(
            default_color=rendering_data.get("default_color", "#000000"),
            default_linewidth_px=rendering_data.get("default_linewidth_px", 1.0),
            background=rendering_data.get("background"),
            invert_y=rendering_data.get("invert_y", True),
            class_styles=rendering_data.get("class_styles", {})
        )
        
        # Convert output config
        output_data = config_data.get("output", {})
        output = OutputConfig(
            svg_filename_pattern=output_data.get("svg_filename_pattern", "{index:02d}_{storey_name}.svg"),
            geojson_filename_pattern=output_data.get("geojson_filename_pattern", "{index:02d}_{storey_name}.geo.json"),
            manifest_filename=output_data.get("manifest_filename", "manifest.json"),
            write_geojson=output_data.get("write_geojson", True)
        )
        
        # Convert performance config
        performance_data = config_data.get("performance", {})
        performance = PerformanceConfig(
            multiprocessing=performance_data.get("multiprocessing", False),
            max_workers=performance_data.get("max_workers")
        )
        
        return Config(
            input_path=input_path,
            output_dir=output_dir,
            cut_offset_m=cut_offset_m,
            per_storey_overrides=per_storey_overrides,
            class_filters=class_filters,
            units=units,
            geometry=geometry,
            tolerances=tolerances,
            rendering=rendering,
            output=output,
            performance=performance
        )
    
    def get_storey_cut_height(self, storey_name: str) -> float:
        """Get cut height for specific storey considering overrides.
        
        This method implements the configuration inheritance and override resolution
        logic. If a storey has a specific override, that value is used. Otherwise,
        the default cut_offset_m is used.
        
        Args:
            storey_name: Name of the building storey
            
        Returns:
            float: Cut height in meters for the specified storey
            
        Raises:
            RuntimeError: If no configuration is loaded
        """
        if self._config is None:
            raise RuntimeError("No configuration loaded. Call load_config() first.")
        
        return self._config.get_storey_cut_height(storey_name)
    
    def has_storey_override(self, storey_name: str) -> bool:
        """Check if a storey has specific configuration overrides.
        
        Args:
            storey_name: Name of the building storey
            
        Returns:
            bool: True if the storey has specific overrides
            
        Raises:
            RuntimeError: If no configuration is loaded
        """
        if self._config is None:
            raise RuntimeError("No configuration loaded. Call load_config() first.")
        
        return storey_name in self._config.per_storey_overrides
    
    def get_storey_override(self, storey_name: str) -> Optional[StoreyConfig]:
        """Get the specific override configuration for a storey.
        
        Args:
            storey_name: Name of the building storey
            
        Returns:
            StoreyConfig or None: The override configuration if it exists
            
        Raises:
            RuntimeError: If no configuration is loaded
        """
        if self._config is None:
            raise RuntimeError("No configuration loaded. Call load_config() first.")
        
        return self._config.per_storey_overrides.get(storey_name)
    
    def add_storey_override(self, storey_name: str, cut_offset_m: float) -> None:
        """Add or update a storey-specific override.
        
        Args:
            storey_name: Name of the building storey
            cut_offset_m: Cut height override in meters
            
        Raises:
            RuntimeError: If no configuration is loaded
            ValueError: If cut_offset_m is negative
        """
        if self._config is None:
            raise RuntimeError("No configuration loaded. Call load_config() first.")
        
        if cut_offset_m < 0:
            raise ValueError("Cut offset must be non-negative")
        
        self._config.per_storey_overrides[storey_name] = StoreyConfig(cut_offset_m=cut_offset_m)
    
    def remove_storey_override(self, storey_name: str) -> bool:
        """Remove a storey-specific override.
        
        Args:
            storey_name: Name of the building storey
            
        Returns:
            bool: True if an override was removed, False if none existed
            
        Raises:
            RuntimeError: If no configuration is loaded
        """
        if self._config is None:
            raise RuntimeError("No configuration loaded. Call load_config() first.")
        
        if storey_name in self._config.per_storey_overrides:
            del self._config.per_storey_overrides[storey_name]
            return True
        return False
    
    def get_class_filters(self) -> ClassFilters:
        """Get IFC class filters configuration.
        
        Returns:
            ClassFilters: The class filters configuration
            
        Raises:
            RuntimeError: If no configuration is loaded
        """
        if self._config is None:
            raise RuntimeError("No configuration loaded. Call load_config() first.")
        return self._config.class_filters
    
    def get_rendering_style(self, ifc_class: str) -> RenderStyle:
        """Get rendering style for specific IFC class.
        
        Args:
            ifc_class: The IFC class name (e.g., "IfcWall")
            
        Returns:
            RenderStyle: Style configuration for the class
            
        Raises:
            RuntimeError: If no configuration is loaded
        """
        if self._config is None:
            raise RuntimeError("No configuration loaded. Call load_config() first.")
        
        # Check if there's a specific style for this class
        if ifc_class in self._config.rendering.class_styles:
            class_style = self._config.rendering.class_styles[ifc_class]
            return RenderStyle(
                color=class_style.get("color", self._config.rendering.default_color),
                linewidth_px=class_style.get("linewidth_px", self._config.rendering.default_linewidth_px)
            )
        
        # Return default style
        return RenderStyle(
            color=self._config.rendering.default_color,
            linewidth_px=self._config.rendering.default_linewidth_px
        )
    
    @property
    def config(self) -> Config:
        """Get the loaded configuration.
        
        Returns:
            Config: The current configuration
            
        Raises:
            RuntimeError: If no configuration is loaded
        """
        if self._config is None:
            raise RuntimeError("No configuration loaded. Call load_config() first.")
        return self._config