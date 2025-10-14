# IFC Floor Plan Generator - CLI Interface

This is the new command-line interface for the IFC Floor Plan Generator. It replaces the old `ifc_floor_plan_generator.py` script with a proper CLI that supports configuration files, progress reporting, and comprehensive error handling.

## Quick Start

1. **Basic usage with example configuration:**
   ```bash
   python ifc_floor_plan_generator_cli.py example_config.json
   ```

2. **With verbose output:**
   ```bash
   python ifc_floor_plan_generator_cli.py example_config.json --verbose
   ```

3. **Get help:**
   ```bash
   python ifc_floor_plan_generator_cli.py --help
   ```

4. **Get configuration help:**
   ```bash
   python ifc_floor_plan_generator_cli.py --help-config
   ```

## Command Line Options

- `config` - Path to JSON configuration file (required)
- `--output-dir, -o` - Override output directory from configuration
- `--verbose, -v` - Enable verbose logging and progress reporting
- `--quiet, -q` - Suppress all output except errors
- `--log-file` - Write logs to specified file
- `--validate-config` - Validate configuration file without processing
- `--dry-run` - Perform a dry run without generating output files
- `--help-config` - Show detailed help about configuration options
- `--version` - Show version information

## Configuration File

The CLI uses JSON configuration files. See `example_config.json` for a complete example with all available options.

### Required Configuration

```json
{
  "input_path": "path/to/input.ifc",
  "output_dir": "path/to/output",
  "cut_offset_m": 1.05
}
```

### Optional Configuration Sections

- `per_storey_overrides` - Override cut heights for specific storeys
- `class_filters` - Control which IFC classes to include/exclude
- `units` - Configure unit detection and scaling
- `geometry` - Control geometry generation settings
- `tolerances` - Set geometric processing tolerances
- `rendering` - Configure SVG styling and appearance
- `output` - Control output file naming and formats
- `performance` - Configure multiprocessing and optimization

## Examples

### Basic Floor Plan Generation
```bash
python ifc_floor_plan_generator_cli.py my_config.json
```

### With Custom Output Directory
```bash
python ifc_floor_plan_generator_cli.py my_config.json --output-dir ./custom_output
```

### Validate Configuration Only
```bash
python ifc_floor_plan_generator_cli.py my_config.json --validate-config
```

### Verbose Processing with Custom Log File
```bash
python ifc_floor_plan_generator_cli.py my_config.json --verbose --log-file processing.log
```

## Migration from Old Script

If you were using the old `ifc_floor_plan_generator.py` script:

1. Create a JSON configuration file based on your old settings
2. Use the new CLI: `python ifc_floor_plan_generator_cli.py your_config.json`
3. The old script will show a deprecation warning and attempt to redirect to the new CLI

## Output Files

The generator creates:
- **SVG files** - Vector graphics floor plans for each storey
- **GeoJSON files** - Geographic data format (optional)
- **Manifest file** - JSON metadata about all generated files

## Error Handling

The CLI provides comprehensive error handling with Norwegian error messages and detailed context. Use `--verbose` for detailed error information and `--log-file` to save logs for debugging.

## Performance

For large IFC files, enable multiprocessing in your configuration:

```json
{
  "performance": {
    "multiprocessing": true,
    "max_workers": 4
  }
}
```

## Support

For detailed configuration options, run:
```bash
python ifc_floor_plan_generator_cli.py --help-config
```

For general help:
```bash
python ifc_floor_plan_generator_cli.py --help
```