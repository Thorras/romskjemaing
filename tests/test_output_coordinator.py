"""
Unit tests for OutputCoordinator.

Tests the output coordination functionality including SVG, GeoJSON, and manifest generation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from ifc_floor_plan_generator.rendering.output_coordinator import OutputCoordinator
from ifc_floor_plan_generator.models import (
    Config, StoreyResult, Polyline2D, BoundingBox,
    ClassFilters, UnitsConfig, GeometryConfig, TolerancesConfig,
    RenderingConfig, OutputConfig, PerformanceConfig
)


class TestOutputCoordinator(unittest.TestCase):
    """Test cases for OutputCoordinator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test configuration
        self.config = Config(
            input_path="test.ifc",
            output_dir=self.temp_dir,
            cut_offset_m=1.0,
            per_storey_overrides={},
            class_filters=ClassFilters(
                include_ifc_classes=[],
                exclude_ifc_classes=[]
            ),
            units=UnitsConfig(
                auto_detect_units=True,
                unit_scale_to_m=1.0
            ),
            geometry=GeometryConfig(
                use_world_coords=True,
                subtract_openings=True,
                sew_shells=True,
                cache_geometry=True
            ),
            tolerances=TolerancesConfig(
                slice_tol=1e-6,
                chain_tol=1e-3
            ),
            rendering=RenderingConfig(
                default_color="#000000",
                default_linewidth_px=1.0,
                background="#ffffff",
                invert_y=True,
                class_styles={}
            ),
            output=OutputConfig(
                svg_filename_pattern="{index:02d}_{storey_name}.svg",
                geojson_filename_pattern="{index:02d}_{storey_name}.geo.json",
                manifest_filename="manifest.json",
                write_geojson=True
            ),
            performance=PerformanceConfig(
                multiprocessing=False,
                max_workers=1
            )
        )
        
        # Create test storey results
        self.test_polylines = [
            Polyline2D(
                points=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
                is_closed=True,
                ifc_class="IfcWall",
                element_guid="test-guid-1"
            ),
            Polyline2D(
                points=[(2.0, 0.0), (3.0, 0.0), (3.0, 1.0)],
                is_closed=False,
                ifc_class="IfcBeam",
                element_guid="test-guid-2"
            )
        ]
        
        self.test_bounds = BoundingBox(
            min_x=0.0,
            min_y=0.0,
            max_x=3.0,
            max_y=1.0
        )
        
        self.test_storeys = [
            StoreyResult(
                storey_name="Ground Floor",
                cut_height=1.0,
                polylines=self.test_polylines,
                bounds=self.test_bounds,
                element_count=2,
                svg_file=None,
                geojson_file=None
            )
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test OutputCoordinator initialization."""
        coordinator = OutputCoordinator(self.config)
        
        self.assertIsNotNone(coordinator.svg_renderer)
        self.assertIsNotNone(coordinator.geojson_renderer)
        self.assertIsNotNone(coordinator.manifest_generator)
        self.assertIsNotNone(coordinator.output_manager)
        self.assertEqual(coordinator.config, self.config)
    
    @patch('ifc_floor_plan_generator.rendering.output_coordinator.SVGRenderer')
    @patch('ifc_floor_plan_generator.rendering.output_coordinator.GeoJSONRenderer')
    @patch('ifc_floor_plan_generator.rendering.output_coordinator.ManifestGenerator')
    def test_generate_all_outputs_success(self, mock_manifest_gen, mock_geojson_renderer, mock_svg_renderer):
        """Test successful generation of all output files."""
        # Setup mocks
        mock_svg_instance = Mock()
        mock_svg_instance.render_and_save.return_value = os.path.join(self.temp_dir, "00_Ground_Floor.svg")
        mock_svg_renderer.return_value = mock_svg_instance
        
        mock_geojson_instance = Mock()
        mock_geojson_instance.should_generate_geojson.return_value = True
        mock_geojson_instance.render_and_save_conditional.return_value = os.path.join(self.temp_dir, "00_Ground_Floor.geo.json")
        mock_geojson_renderer.return_value = mock_geojson_instance
        
        mock_manifest_instance = Mock()
        mock_manifest_instance.generate_and_save_manifest.return_value = os.path.join(self.temp_dir, "manifest.json")
        mock_manifest_gen.return_value = mock_manifest_instance
        
        # Create coordinator and generate outputs
        coordinator = OutputCoordinator(self.config)
        result = coordinator.generate_all_outputs(
            self.test_storeys,
            "test.ifc",
            10.5
        )
        
        # Verify results
        self.assertEqual(len(result["svg_files"]), 1)
        self.assertEqual(len(result["geojson_files"]), 1)
        self.assertIsNotNone(result["manifest_file"])
        self.assertEqual(result["total_files"], 3)
        self.assertEqual(len(result["errors"]), 0)
    
    @patch('ifc_floor_plan_generator.rendering.output_coordinator.SVGRenderer')
    def test_generate_svg_for_storey_no_polylines(self, mock_svg_renderer):
        """Test SVG generation when storey has no polylines."""
        # Create storey with no polylines
        empty_storey = StoreyResult(
            storey_name="Empty Floor",
            cut_height=1.0,
            polylines=[],
            bounds=None,
            element_count=0,
            svg_file=None,
            geojson_file=None
        )
        
        coordinator = OutputCoordinator(self.config)
        result = coordinator._generate_svg_for_storey(empty_storey, 0)
        
        self.assertIsNone(result)
    
    def test_ensure_consistent_filenames(self):
        """Test filename consistency checking."""
        coordinator = OutputCoordinator(self.config)
        
        # Set some file paths on storeys
        self.test_storeys[0].svg_file = os.path.join(self.temp_dir, "00_Ground_Floor.svg")
        self.test_storeys[0].geojson_file = os.path.join(self.temp_dir, "00_Ground_Floor.geo.json")
        
        # This should not raise any exceptions
        coordinator.ensure_consistent_filenames(self.test_storeys)
    
    def test_get_output_organization_info(self):
        """Test output organization information retrieval."""
        coordinator = OutputCoordinator(self.config)
        info = coordinator.get_output_organization_info()
        
        self.assertIn("output_manager_info", info)
        self.assertIn("svg_renderer_viewport", info)
        self.assertIn("geojson_config", info)
        self.assertIn("existing_files", info)
    
    def test_validate_output_configuration(self):
        """Test output configuration validation."""
        coordinator = OutputCoordinator(self.config)
        validation = coordinator.validate_output_configuration()
        
        self.assertIn("valid", validation)
        self.assertIn("warnings", validation)
        self.assertIn("errors", validation)
        self.assertIsInstance(validation["warnings"], list)
        self.assertIsInstance(validation["errors"], list)
    
    def test_cleanup_output_directory(self):
        """Test output directory cleanup."""
        # Create some test files
        test_svg = os.path.join(self.temp_dir, "test.svg")
        test_geojson = os.path.join(self.temp_dir, "test.geo.json")
        test_manifest = os.path.join(self.temp_dir, "manifest.json")
        
        with open(test_svg, 'w') as f:
            f.write("<svg></svg>")
        with open(test_geojson, 'w') as f:
            f.write('{"type": "FeatureCollection"}')
        with open(test_manifest, 'w') as f:
            f.write('{"manifest": true}')
        
        coordinator = OutputCoordinator(self.config)
        result = coordinator.cleanup_output_directory(keep_manifest=True)
        
        self.assertIn("svg_removed", result)
        self.assertIn("geojson_removed", result)
        self.assertIn("manifest_removed", result)
        
        # Manifest should still exist
        self.assertTrue(os.path.exists(test_manifest))


if __name__ == '__main__':
    unittest.main()