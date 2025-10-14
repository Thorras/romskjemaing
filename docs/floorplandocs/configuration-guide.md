# IFC Floor Plan Generator - Configuration Guide

This guide explains all configuration options available in the IFC Floor Plan Generator. The system uses JSON configuration files to control how IFC files are processed and converted to 2D floor plans.

## Example Configuration Files

Three example configuration files are provided:

- **config-minimal-example.json** - Bare minimum configuration for quick start
- **config-basic-example.json** - Common settings for typical use cases  
- **config-advanced-example.json** - Full-featured configuration with per-storey overrides and detailed styling

## Required Configuration Options

### input_path
**Type:** string  
**Required:** Yes  
**Description:** Path to the IFC file that should be processed.

**Example:**
```json
"input_path": "path/to/your/building.ifc"
```

### output_dir
**Type:** string  
**Required:** Yes  
**Description:** Directory where SVG files and manifest will be saved.

**Example:**
```json
"output_dir": "floor_plans"
```

## Optional Configuration Options

### cut_offset_m
**Type:** number  
**Default:** 1.05  
**Description:** Standard cutting height above the floor level in meters. This determines where the horizontal section is made through the building.

**Example:**
```json
"cut_offset_m": 1.05
```

### per_storey_overrides
**Type:** object  
**Description:** Override settings per floor/storey, such as specific cutting heights. The key should match the storey name from the IFC file.

**Properties:**
- `cut_offset_m` (number): Custom cutting height for this specific storey

**Example:**
```json
"per_storey_overrides": {
  "Ground Floor": {"cut_offset_m": 0.8},
  "First Floor": {"cut_offset_m": 1.2},
  "Basement": {"cut_offset_m": 0.5}
}
```

### class_filters
**Type:** object  
**Description:** Filters for IFC classes that should be included in the section.

**Properties:**
- `include_ifc_classes` (array of strings): IFC classes to include. Empty array means all relevant classes are included.
- `exclude_ifc_classes` (array of strings): IFC classes to exclude from processing.

**Note:** If an IFC class appears in both include and exclude lists, exclude takes priority.

**Example:**
```json
"class_filters": {
  "include_ifc_classes": ["IfcWall", "IfcSlab", "IfcColumn"],
  "exclude_ifc_classes": ["IfcSpace", "IfcOpeningElement"]
}
```

**Common IFC Classes:**
- `IfcWall` - Walls
- `IfcSlab` - Floor slabs and ceilings
- `IfcColumn` - Structural columns
- `IfcBeam` - Structural beams
- `IfcStair` - Stairs
- `IfcRailing` - Railings and handrails
- `IfcDoor` - Doors
- `IfcWindow` - Windows
- `IfcSpace` - Spatial zones (often excluded)
- `IfcOpeningElement` - Openings in walls (often excluded)

### units
**Type:** object  
**Description:** Unit handling configuration.

**Properties:**
- `auto_detect_units` (boolean): Attempt to detect scaling from IFC units to meters
- `unit_scale_to_m` (number): Manual scaling to meters (overrides automatic detection)

**Example:**
```json
"units": {
  "auto_detect_units": true,
  "unit_scale_to_m": null
}
```

### geometry
**Type:** object  
**Description:** Geometry generation settings via IfcOpenShell.

**Properties:**
- `use_world_coords` (boolean): Use global coordinates for shape generation
- `subtract_openings` (boolean): Subtract openings from walls and other elements
- `sew_shells` (boolean): Sew shells for cleaner mesh representation

**Example:**
```json
"geometry": {
  "use_world_coords": true,
  "subtract_openings": true,
  "sew_shells": true
}
```

### tolerances
**Type:** object  
**Description:** Numerical tolerances for cutting and chaining operations.

**Properties:**
- `slice_tol` (number): Tolerance for plane-section operations
- `chain_tol` (number): Tolerance for polyline chaining

**Example:**
```json
"tolerances": {
  "slice_tol": 1e-6,
  "chain_tol": 1e-3
}
```

### rendering
**Type:** object  
**Description:** Styling configuration for SVG output.

**Properties:**
- `invert_y` (boolean): Invert Y-axis for classic 2D drawing orientation
- `background` (string): Background color in HEX format, null for transparent
- `default_color` (string): Default line color in HEX format
- `default_linewidth_px` (number): Default line width in pixels
- `class_styles` (object): Override styling per IFC class

**Example:**
```json
"rendering": {
  "default_color": "#000000",
  "default_linewidth_px": 1.0,
  "background": "#FFFFFF",
  "invert_y": true,
  "class_styles": {
    "IfcWall": {"color": "#FF0000", "linewidth_px": 2.0},
    "IfcSlab": {"color": "#808080", "linewidth_px": 1.5},
    "IfcColumn": {"color": "#0000FF", "linewidth_px": 2.5}
  }
}
```

**Color Examples:**
- `#FF0000` - Red
- `#00FF00` - Green  
- `#0000FF` - Blue
- `#000000` - Black
- `#FFFFFF` - White
- `#808080` - Gray

### output
**Type:** object  
**Description:** Output file settings and naming conventions.

**Properties:**
- `svg_filename_pattern` (string): Pattern for SVG filenames
- `geojson_filename_pattern` (string): Pattern for GeoJSON filenames
- `manifest_filename` (string): Name of the manifest file
- `write_geojson` (boolean): Also write GeoJSON files for web use

**Filename Pattern Variables:**
- `{index:02d}` - Zero-padded index number
- `{storey_name_sanitized}` - Sanitized storey name (special characters replaced)

**Example:**
```json
"output": {
  "svg_filename_pattern": "{index:02d}_{storey_name_sanitized}.svg",
  "geojson_filename_pattern": "{index:02d}_{storey_name_sanitized}.geo.json",
  "manifest_filename": "manifest.json",
  "write_geojson": true
}
```

### performance
**Type:** object  
**Description:** Performance optimization settings.

**Properties:**
- `multiprocessing` (boolean): Enable parallel processing per storey/element
- `max_workers` (integer): Number of worker threads/processes
- `cache_geometry` (boolean): Cache geometry per GUID for reuse

**Example:**
```json
"performance": {
  "multiprocessing": true,
  "max_workers": 4,
  "cache_geometry": true
}
```

## Configuration Examples by Use Case

### Quick Start (Minimal)
For testing or simple buildings:
```json
{
  "input_path": "your-building.ifc",
  "output_dir": "output"
}
```

### Typical Office Building
For standard commercial buildings:
```json
{
  "input_path": "office-building.ifc",
  "output_dir": "floor_plans",
  "cut_offset_m": 1.05,
  "class_filters": {
    "exclude_ifc_classes": ["IfcSpace", "IfcOpeningElement"]
  },
  "rendering": {
    "class_styles": {
      "IfcWall": {"color": "#FF0000", "linewidth_px": 2.0},
      "IfcColumn": {"color": "#0000FF", "linewidth_px": 2.5}
    }
  }
}
```

### Complex Multi-Story Building
For buildings with varying floor types:
```json
{
  "input_path": "complex-building.ifc",
  "output_dir": "detailed_plans",
  "cut_offset_m": 1.05,
  "per_storey_overrides": {
    "Basement": {"cut_offset_m": 0.8},
    "Ground Floor": {"cut_offset_m": 1.0},
    "Penthouse": {"cut_offset_m": 0.7}
  },
  "class_filters": {
    "include_ifc_classes": ["IfcWall", "IfcSlab", "IfcColumn", "IfcStair"],
    "exclude_ifc_classes": ["IfcSpace", "IfcFurnishingElement"]
  },
  "performance": {
    "multiprocessing": true,
    "max_workers": 4
  }
}
```

## Troubleshooting Configuration Issues

### Common Problems

1. **No output generated**: Check that `input_path` points to a valid IFC file
2. **Empty floor plans**: Adjust `cut_offset_m` or check `class_filters`
3. **Performance issues**: Enable `multiprocessing` and `cache_geometry`
4. **Wrong colors**: Verify HEX color codes in `class_styles`
5. **File naming issues**: Check `svg_filename_pattern` for valid variables

### Validation

The configuration is validated against a JSON schema. Common validation errors:
- Missing required fields (`input_path`, `output_dir`)
- Invalid data types (string instead of number)
- Invalid HEX color codes
- Negative values for tolerances or line widths

## Best Practices

1. **Start minimal**: Begin with basic configuration and add complexity as needed
2. **Test cutting heights**: Different building types may need different `cut_offset_m` values
3. **Filter wisely**: Use `class_filters` to focus on relevant building elements
4. **Performance tuning**: Enable multiprocessing for large files, but test with small files first
5. **Consistent naming**: Use clear, descriptive patterns for output filenames
6. **Color coding**: Use consistent color schemes across projects for better readability