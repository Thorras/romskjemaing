"""
Unit tests for configuration management system.

Tests JSON schema validation, per-storey override resolution logic,
and units conversion and scaling functionality.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ifc_floor_plan_generator.config.manager import ConfigurationManager
from ifc_floor_plan_generator.config.models import (
    Config, StoreyConfig, ClassFilters, UnitsConfig, GeometryConfig,
    TolerancesConfig, RenderingConfig, OutputConfig, PerformanceConfig
)
from ifc_floor_plan_generator.rendering.models import RenderStyle


class TestConfigurationManager(unittest.TestCase):
    """Test cases for ConfigurationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigurationManager()
        self.temp_dir = tempfile.mkdtemp()
        
        # Valid minimal configuration
        self.valid_minimal_config = {
            "input_path": "/path/to/test.ifc",
            "output_dir": "/path/to/output"
        }
        
        # Valid complete configuration
        self.valid_complete_config = {
            "input_path": "/path/to/test.ifc",
            "output_dir": "/path/to/output",
            "cut_offset_m": 1.2,
            "per_storey_overrides": {
                "Ground Floor": {
                    "cut_offset_m": 0.8
                },
                "First Floor": {
                    "cut_offset_m": 1.5
                }
            },
            "class_filters": {
                "include_ifc_classes": ["IfcWall", "IfcSlab", "IfcColumn"],
                "exclude_ifc_classes": ["IfcSpace"]
            },
            "units": {
                "auto_detect_units": True,
                "unit_scale_to_m": 0.001
            },
            "geometry": {
                "use_world_coords": True,
                "subtract_openings": True,
                "sew_shells": False
            },
            "tolerances": {
                "slice_tol": 1e-5,
                "chain_tol": 1e-2
            },
            "rendering": {
                "default_color": "#FF0000",
                "default_linewidth_px": 2.0,
                "background": "#FFFFFF",
                "invert_y": False,
                "class_styles": {
                    "IfcWall": {
                        "color": "#000000",
                        "linewidth_px": 3.0
                    }
                }
            },
            "output": {
                "svg_filename_pattern": "{index:03d}_{storey_name}.svg",
                "geojson_filename_pattern": "{index:03d}_{storey_name}.geojson",
                "manifest_filename": "results.json",
                "write_geojson": False
            },
            "performance": {
                "multiprocessing": True,
                "max_workers": 4
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_temp_config_file(self, config_data: dict) -> str:
        """Create a temporary configuration file."""
        config_path = os.path.join(self.temp_dir, "test_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        return config_path


class TestJSONSchemaValidation(TestConfigurationManager):
    """Test JSON schema validation functionality."""
    
    def test_validate_minimal_valid_config(self):
        """Test validation of minimal valid configuration."""
        result = self.config_manager.validate_config(self.valid_minimal_config)
        self.assertTrue(result)
    
    def test_validate_complete_valid_config(self):
        """Test validation of complete valid configuration."""
        result = self.config_manager.validate_config(self.valid_complete_config)
        self.assertTrue(result)
    
    def test_validate_missing_required_field_input_path(self):
        """Test validation fails when input_path is missing."""
        invalid_config = {"output_dir": "/path/to/output"}
        
        with self.assertRaises(Exception) as context:
            self.config_manager.validate_config(invalid_config)
        
        self.assertIn("input_path", str(context.exception))
    
    def test_validate_missing_required_field_output_dir(self):
        """Test validation fails when output_dir is missing."""
        invalid_config = {"input_path": "/path/to/test.ifc"}
        
        with self.assertRaises(Exception) as context:
            self.config_manager.validate_config(invalid_config)
        
        self.assertIn("output_dir", str(context.exception))
    
    def test_validate_empty_required_fields(self):
        """Test validation fails when required fields are empty."""
        invalid_configs = [
            {"input_path": "", "output_dir": "/path/to/output"},
            {"input_path": "/path/to/test.ifc", "output_dir": ""},
            {"input_path": "   ", "output_dir": "/path/to/output"},
        ]
        
        for invalid_config in invalid_configs:
            with self.assertRaises(Exception):
                self.config_manager.validate_config(invalid_config)
    
    def test_validate_invalid_cut_offset_negative(self):
        """Test validation fails for negative cut_offset_m."""
        invalid_config = self.valid_minimal_config.copy()
        invalid_config["cut_offset_m"] = -1.0
        
        with self.assertRaises(Exception) as context:
            self.config_manager.validate_config(invalid_config)
        
        self.assertIn("cut_offset_m", str(context.exception))
    
    def test_validate_invalid_cut_offset_non_numeric(self):
        """Test validation fails for non-numeric cut_offset_m."""
        invalid_config = self.valid_minimal_config.copy()
        invalid_config["cut_offset_m"] = "invalid"
        
        with self.assertRaises(Exception):
            self.config_manager.validate_config(invalid_config)
    
    def test_validate_invalid_per_storey_overrides_structure(self):
        """Test validation fails for invalid per_storey_overrides structure."""
        invalid_configs = [
            # Non-object per_storey_overrides
            {**self.valid_minimal_config, "per_storey_overrides": "invalid"},
            # Non-object storey config
            {**self.valid_minimal_config, "per_storey_overrides": {"Floor1": "invalid"}},
            # Negative cut_offset_m in override
            {**self.valid_minimal_config, "per_storey_overrides": {"Floor1": {"cut_offset_m": -1.0}}},
        ]
        
        for invalid_config in invalid_configs:
            with self.assertRaises(Exception):
                self.config_manager.validate_config(invalid_config)
    
    def test_validate_invalid_class_filters_structure(self):
        """Test validation fails for invalid class_filters structure."""
        invalid_configs = [
            # Non-object class_filters
            {**self.valid_minimal_config, "class_filters": "invalid"},
            # Non-array include_ifc_classes
            {**self.valid_minimal_config, "class_filters": {"include_ifc_classes": "invalid"}},
            # Non-string items in include_ifc_classes
            {**self.valid_minimal_config, "class_filters": {"include_ifc_classes": [123, "IfcWall"]}},
            # Non-array exclude_ifc_classes
            {**self.valid_minimal_config, "class_filters": {"exclude_ifc_classes": "invalid"}},
            # Non-string items in exclude_ifc_classes
            {**self.valid_minimal_config, "class_filters": {"exclude_ifc_classes": ["IfcWall", 456]}},
        ]
        
        for invalid_config in invalid_configs:
            with self.assertRaises(Exception):
                self.config_manager.validate_config(invalid_config)
    
    def test_validate_valid_class_filters(self):
        """Test validation passes for valid class_filters."""
        valid_configs = [
            # Empty filters
            {**self.valid_minimal_config, "class_filters": {}},
            # Empty arrays
            {**self.valid_minimal_config, "class_filters": {"include_ifc_classes": [], "exclude_ifc_classes": []}},
            # Valid string arrays
            {**self.valid_minimal_config, "class_filters": {"include_ifc_classes": ["IfcWall", "IfcSlab"]}},
            {**self.valid_minimal_config, "class_filters": {"exclude_ifc_classes": ["IfcSpace"]}},
        ]
        
        for valid_config in valid_configs:
            result = self.config_manager.validate_config(valid_config)
            self.assertTrue(result)
    
    @patch('ifc_floor_plan_generator.config.manager.HAS_JSONSCHEMA', False)
    def test_basic_validation_without_jsonschema(self):
        """Test basic validation works when jsonschema is not available."""
        # Should still validate basic structure
        result = self.config_manager.validate_config(self.valid_minimal_config)
        self.assertTrue(result)
        
        # Should still catch basic errors
        with self.assertRaises(Exception):
            self.config_manager.validate_config({"input_path": ""})
    
    def test_jsonschema_validation_error_handling(self):
        """Test proper error handling when jsonschema validation fails."""
        # Skip this test if jsonschema is not available
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not available")
        
        from ifc_floor_plan_generator.config.manager import ValidationError
        
        # Test with a config that would fail jsonschema validation
        # but pass basic validation (if jsonschema was available)
        with patch('ifc_floor_plan_generator.config.manager.HAS_JSONSCHEMA', True):
            with patch('jsonschema.validate') as mock_validate:
                mock_validate.side_effect = jsonschema.ValidationError("Test validation error")
                
                with self.assertRaises(ValidationError) as context:
                    self.config_manager.validate_config(self.valid_minimal_config)
                
                self.assertIn("Configuration validation failed", str(context.exception))


class TestConfigurationLoading(TestConfigurationManager):
    """Test configuration loading from files."""
    
    def test_load_valid_minimal_config(self):
        """Test loading valid minimal configuration from file."""
        config_path = self._create_temp_config_file(self.valid_minimal_config)
        
        config = self.config_manager.load_config(config_path)
        
        self.assertIsInstance(config, Config)
        self.assertEqual(config.input_path, "/path/to/test.ifc")
        self.assertEqual(config.output_dir, "/path/to/output")
        self.assertEqual(config.cut_offset_m, 1.05)  # Default value
    
    def test_load_valid_complete_config(self):
        """Test loading complete configuration from file."""
        config_path = self._create_temp_config_file(self.valid_complete_config)
        
        config = self.config_manager.load_config(config_path)
        
        self.assertIsInstance(config, Config)
        self.assertEqual(config.input_path, "/path/to/test.ifc")
        self.assertEqual(config.output_dir, "/path/to/output")
        self.assertEqual(config.cut_offset_m, 1.2)
        
        # Check per_storey_overrides
        self.assertIn("Ground Floor", config.per_storey_overrides)
        self.assertEqual(config.per_storey_overrides["Ground Floor"].cut_offset_m, 0.8)
        
        # Check class_filters
        self.assertEqual(config.class_filters.include_ifc_classes, ["IfcWall", "IfcSlab", "IfcColumn"])
        self.assertEqual(config.class_filters.exclude_ifc_classes, ["IfcSpace"])
        
        # Check units config
        self.assertTrue(config.units.auto_detect_units)
        self.assertEqual(config.units.unit_scale_to_m, 0.001)
        
        # Check geometry config
        self.assertTrue(config.geometry.use_world_coords)
        self.assertTrue(config.geometry.subtract_openings)
        self.assertFalse(config.geometry.sew_shells)
        
        # Check rendering config
        self.assertEqual(config.rendering.default_color, "#FF0000")
        self.assertEqual(config.rendering.default_linewidth_px, 2.0)
        self.assertFalse(config.rendering.invert_y)
        
        # Check performance config
        self.assertTrue(config.performance.multiprocessing)
        self.assertEqual(config.performance.max_workers, 4)
    
    def test_load_nonexistent_file(self):
        """Test loading configuration from nonexistent file raises FileNotFoundError."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.json")
        
        with self.assertRaises(FileNotFoundError) as context:
            self.config_manager.load_config(nonexistent_path)
        
        self.assertIn("Configuration file not found", str(context.exception))
    
    def test_load_invalid_json_file(self):
        """Test loading invalid JSON file raises JSONDecodeError."""
        invalid_json_path = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json_path, 'w') as f:
            f.write("{ invalid json content")
        
        with self.assertRaises(json.JSONDecodeError):
            self.config_manager.load_config(invalid_json_path)
    
    def test_load_invalid_config_structure(self):
        """Test loading config with invalid structure raises ValidationError."""
        invalid_config = {"invalid": "structure"}
        config_path = self._create_temp_config_file(invalid_config)
        
        with self.assertRaises(Exception):
            self.config_manager.load_config(config_path)


class TestPerStoreyOverrideLogic(TestConfigurationManager):
    """Test per-storey override resolution logic."""
    
    def setUp(self):
        """Set up test fixtures with loaded configuration."""
        super().setUp()
        
        # Load a configuration with overrides
        config_with_overrides = {
            "input_path": "/path/to/test.ifc",
            "output_dir": "/path/to/output",
            "cut_offset_m": 1.0,
            "per_storey_overrides": {
                "Ground Floor": {"cut_offset_m": 0.5},
                "First Floor": {"cut_offset_m": 1.5},
                "Second Floor": {"cut_offset_m": 2.0}
            }
        }
        
        config_path = self._create_temp_config_file(config_with_overrides)
        self.config_manager.load_config(config_path)
    
    def test_get_storey_cut_height_with_override(self):
        """Test getting cut height for storey with specific override."""
        height = self.config_manager.get_storey_cut_height("Ground Floor")
        self.assertEqual(height, 0.5)
        
        height = self.config_manager.get_storey_cut_height("First Floor")
        self.assertEqual(height, 1.5)
        
        height = self.config_manager.get_storey_cut_height("Second Floor")
        self.assertEqual(height, 2.0)
    
    def test_get_storey_cut_height_without_override(self):
        """Test getting cut height for storey without override uses default."""
        height = self.config_manager.get_storey_cut_height("Third Floor")
        self.assertEqual(height, 1.0)  # Default cut_offset_m
        
        height = self.config_manager.get_storey_cut_height("Basement")
        self.assertEqual(height, 1.0)  # Default cut_offset_m
    
    def test_has_storey_override(self):
        """Test checking if storey has specific overrides."""
        self.assertTrue(self.config_manager.has_storey_override("Ground Floor"))
        self.assertTrue(self.config_manager.has_storey_override("First Floor"))
        self.assertFalse(self.config_manager.has_storey_override("Third Floor"))
        self.assertFalse(self.config_manager.has_storey_override("Nonexistent Floor"))
    
    def test_get_storey_override(self):
        """Test getting specific storey override configuration."""
        override = self.config_manager.get_storey_override("Ground Floor")
        self.assertIsNotNone(override)
        self.assertIsInstance(override, StoreyConfig)
        self.assertEqual(override.cut_offset_m, 0.5)
        
        override = self.config_manager.get_storey_override("Nonexistent Floor")
        self.assertIsNone(override)
    
    def test_add_storey_override(self):
        """Test adding new storey override."""
        # Add new override
        self.config_manager.add_storey_override("New Floor", 2.5)
        
        # Verify it was added
        self.assertTrue(self.config_manager.has_storey_override("New Floor"))
        height = self.config_manager.get_storey_cut_height("New Floor")
        self.assertEqual(height, 2.5)
    
    def test_add_storey_override_update_existing(self):
        """Test updating existing storey override."""
        # Update existing override
        self.config_manager.add_storey_override("Ground Floor", 0.8)
        
        # Verify it was updated
        height = self.config_manager.get_storey_cut_height("Ground Floor")
        self.assertEqual(height, 0.8)
    
    def test_add_storey_override_invalid_value(self):
        """Test adding storey override with invalid value raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.config_manager.add_storey_override("Test Floor", -1.0)
        
        self.assertIn("Cut offset must be non-negative", str(context.exception))
    
    def test_remove_storey_override(self):
        """Test removing storey override."""
        # Remove existing override
        result = self.config_manager.remove_storey_override("Ground Floor")
        self.assertTrue(result)
        
        # Verify it was removed
        self.assertFalse(self.config_manager.has_storey_override("Ground Floor"))
        height = self.config_manager.get_storey_cut_height("Ground Floor")
        self.assertEqual(height, 1.0)  # Should use default now
    
    def test_remove_nonexistent_storey_override(self):
        """Test removing nonexistent storey override returns False."""
        result = self.config_manager.remove_storey_override("Nonexistent Floor")
        self.assertFalse(result)
    
    def test_storey_override_methods_without_loaded_config(self):
        """Test storey override methods raise RuntimeError when no config is loaded."""
        empty_manager = ConfigurationManager()
        
        with self.assertRaises(RuntimeError):
            empty_manager.get_storey_cut_height("Test Floor")
        
        with self.assertRaises(RuntimeError):
            empty_manager.has_storey_override("Test Floor")
        
        with self.assertRaises(RuntimeError):
            empty_manager.get_storey_override("Test Floor")
        
        with self.assertRaises(RuntimeError):
            empty_manager.add_storey_override("Test Floor", 1.0)
        
        with self.assertRaises(RuntimeError):
            empty_manager.remove_storey_override("Test Floor")


class TestUnitsConversionAndScaling(TestConfigurationManager):
    """Test units conversion and scaling functionality."""
    
    def test_units_config_auto_detect_default(self):
        """Test units config defaults to auto-detect enabled."""
        config_path = self._create_temp_config_file(self.valid_minimal_config)
        config = self.config_manager.load_config(config_path)
        
        self.assertTrue(config.units.auto_detect_units)
        self.assertIsNone(config.units.unit_scale_to_m)
    
    def test_units_config_manual_scale_override(self):
        """Test units config with manual scale override."""
        config_with_units = {
            **self.valid_minimal_config,
            "units": {
                "auto_detect_units": False,
                "unit_scale_to_m": 0.001  # millimeters to meters
            }
        }
        
        config_path = self._create_temp_config_file(config_with_units)
        config = self.config_manager.load_config(config_path)
        
        self.assertFalse(config.units.auto_detect_units)
        self.assertEqual(config.units.unit_scale_to_m, 0.001)
    
    def test_units_config_validation_positive_scale(self):
        """Test units config validation requires positive scale."""
        invalid_configs = [
            {
                **self.valid_minimal_config,
                "units": {"unit_scale_to_m": 0.0}
            },
            {
                **self.valid_minimal_config,
                "units": {"unit_scale_to_m": -1.0}
            }
        ]
        
        for invalid_config in invalid_configs:
            config_path = self._create_temp_config_file(invalid_config)
            with self.assertRaises(ValueError):
                self.config_manager.load_config(config_path)
    
    def test_units_config_common_scale_factors(self):
        """Test units config with common scale factors."""
        common_scales = [
            ("millimeters", 0.001),
            ("centimeters", 0.01),
            ("inches", 0.0254),
            ("feet", 0.3048),
            ("meters", 1.0)
        ]
        
        for unit_name, scale_factor in common_scales:
            config_with_units = {
                **self.valid_minimal_config,
                "units": {
                    "auto_detect_units": False,
                    "unit_scale_to_m": scale_factor
                }
            }
            
            config_path = self._create_temp_config_file(config_with_units)
            config = self.config_manager.load_config(config_path)
            
            self.assertEqual(config.units.unit_scale_to_m, scale_factor, 
                           f"Failed for {unit_name}")
    
    def test_units_config_auto_detect_with_manual_override(self):
        """Test that manual scale overrides auto-detect when both are specified."""
        config_with_both = {
            **self.valid_minimal_config,
            "units": {
                "auto_detect_units": True,
                "unit_scale_to_m": 0.001
            }
        }
        
        config_path = self._create_temp_config_file(config_with_both)
        config = self.config_manager.load_config(config_path)
        
        # Both should be preserved in config
        self.assertTrue(config.units.auto_detect_units)
        self.assertEqual(config.units.unit_scale_to_m, 0.001)
        
        # According to requirements, manual scale should override auto-detect
        # This would be tested in the actual IFC parser implementation


class TestConfigurationAccess(TestConfigurationManager):
    """Test configuration access methods."""
    
    def setUp(self):
        """Set up test fixtures with loaded configuration."""
        super().setUp()
        config_path = self._create_temp_config_file(self.valid_complete_config)
        self.config_manager.load_config(config_path)
    
    def test_get_class_filters(self):
        """Test getting class filters configuration."""
        class_filters = self.config_manager.get_class_filters()
        
        self.assertIsInstance(class_filters, ClassFilters)
        self.assertEqual(class_filters.include_ifc_classes, ["IfcWall", "IfcSlab", "IfcColumn"])
        self.assertEqual(class_filters.exclude_ifc_classes, ["IfcSpace"])
    
    def test_get_rendering_style_with_class_override(self):
        """Test getting rendering style for class with specific override."""
        style = self.config_manager.get_rendering_style("IfcWall")
        
        self.assertIsInstance(style, RenderStyle)
        self.assertEqual(style.color, "#000000")
        self.assertEqual(style.linewidth_px, 3.0)
    
    def test_get_rendering_style_without_class_override(self):
        """Test getting rendering style for class without override uses defaults."""
        style = self.config_manager.get_rendering_style("IfcSlab")
        
        self.assertIsInstance(style, RenderStyle)
        self.assertEqual(style.color, "#FF0000")  # Default color
        self.assertEqual(style.linewidth_px, 2.0)  # Default linewidth
    
    def test_config_property_access(self):
        """Test accessing config through property."""
        config = self.config_manager.config
        
        self.assertIsInstance(config, Config)
        self.assertEqual(config.input_path, "/path/to/test.ifc")
    
    def test_config_property_without_loaded_config(self):
        """Test config property raises RuntimeError when no config is loaded."""
        empty_manager = ConfigurationManager()
        
        with self.assertRaises(RuntimeError):
            _ = empty_manager.config
    
    def test_access_methods_without_loaded_config(self):
        """Test access methods raise RuntimeError when no config is loaded."""
        empty_manager = ConfigurationManager()
        
        with self.assertRaises(RuntimeError):
            empty_manager.get_class_filters()
        
        with self.assertRaises(RuntimeError):
            empty_manager.get_rendering_style("IfcWall")


class TestTolerancesConfiguration(TestConfigurationManager):
    """Test tolerances configuration validation and access."""
    
    def test_tolerances_config_defaults(self):
        """Test tolerances config uses proper defaults."""
        config_path = self._create_temp_config_file(self.valid_minimal_config)
        config = self.config_manager.load_config(config_path)
        
        self.assertEqual(config.tolerances.slice_tol, 1e-6)
        self.assertEqual(config.tolerances.chain_tol, 1e-3)
    
    def test_tolerances_config_custom_values(self):
        """Test tolerances config with custom values."""
        config_with_tolerances = {
            **self.valid_minimal_config,
            "tolerances": {
                "slice_tol": 1e-5,
                "chain_tol": 1e-2
            }
        }
        
        config_path = self._create_temp_config_file(config_with_tolerances)
        config = self.config_manager.load_config(config_path)
        
        self.assertEqual(config.tolerances.slice_tol, 1e-5)
        self.assertEqual(config.tolerances.chain_tol, 1e-2)
    
    def test_tolerances_config_validation_positive_values(self):
        """Test tolerances config validation requires positive values."""
        invalid_configs = [
            {
                **self.valid_minimal_config,
                "tolerances": {"slice_tol": 0.0}
            },
            {
                **self.valid_minimal_config,
                "tolerances": {"slice_tol": -1e-6}
            },
            {
                **self.valid_minimal_config,
                "tolerances": {"chain_tol": 0.0}
            },
            {
                **self.valid_minimal_config,
                "tolerances": {"chain_tol": -1e-3}
            }
        ]
        
        for invalid_config in invalid_configs:
            config_path = self._create_temp_config_file(invalid_config)
            with self.assertRaises(ValueError):
                self.config_manager.load_config(config_path)


if __name__ == '__main__':
    unittest.main()