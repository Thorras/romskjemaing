"""
Integration Tests for Surface Display

Tests for surface data extraction and display integration.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys

from ifc_room_schedule.ui.main_window import MainWindow
from ifc_room_schedule.ui.space_detail_widget import SpaceDetailWidget
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.data.surface_model import SurfaceData


class TestSurfaceDisplayIntegration:
    """Integration tests for surface display functionality."""

    @classmethod
    def setup_class(cls):
        """Set up QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setup_method(self):
        """Set up test fixtures."""
        self.main_window = MainWindow()
        self.space_detail_widget = SpaceDetailWidget()

    def create_test_space_with_surfaces(self) -> SpaceData:
        """Create a test space with surface data."""
        space = SpaceData(
            guid="test-space-guid",
            name="101",
            long_name="Office 101",
            description="Test office space",
            object_type="Office",
            zone_category="Office",
            number="101",
            elevation=0.0,
            quantities={"Height": 3.0, "Area": 25.0}
        )
        
        # Add test surfaces
        surfaces = [
            SurfaceData("wall-1", "Wall", 12.0, "Concrete", "IfcWall", space.guid),
            SurfaceData("wall-2", "Wall", 15.0, "Concrete", "IfcWall", space.guid),
            SurfaceData("wall-3", "Wall", 12.0, "Concrete", "IfcWall", space.guid),
            SurfaceData("wall-4", "Wall", 15.0, "Concrete", "IfcWall", space.guid),
            SurfaceData("floor-1", "Floor", 25.0, "Wood", "IfcSlab", space.guid),
            SurfaceData("ceiling-1", "Ceiling", 25.0, "Plaster", "IfcSlab", space.guid),
            SurfaceData("window-1", "Opening", 2.5, "Glass", "IfcWindow", space.guid),
        ]
        
        for surface in surfaces:
            space.add_surface(surface)
            
        return space

    def test_space_detail_widget_displays_surfaces(self):
        """Test that space detail widget displays surface information."""
        space = self.create_test_space_with_surfaces()
        
        # Display the space
        self.space_detail_widget.display_space(space)
        
        # Check that surfaces tab is populated
        surfaces_table = self.space_detail_widget.surfaces_table
        assert surfaces_table.rowCount() == 7  # 7 surfaces
        
        # Check surface data in table
        for row in range(surfaces_table.rowCount()):
            type_item = surfaces_table.item(row, 0)
            area_item = surfaces_table.item(row, 1)
            material_item = surfaces_table.item(row, 2)
            
            assert type_item is not None
            assert area_item is not None
            assert material_item is not None
            
            # Verify surface types are displayed
            surface_type = type_item.text()
            assert surface_type in ["Wall", "Floor", "Ceiling", "Opening"]

    def test_surface_area_summary_calculation(self):
        """Test that surface area summary is calculated correctly."""
        space = self.create_test_space_with_surfaces()
        
        # Display the space
        self.space_detail_widget.display_space(space)
        
        # Check surface summary
        summary_label = self.space_detail_widget.surface_summary_label
        summary_text = summary_label.text()
        
        # Should show total surfaces and area
        assert "Total Surfaces: 7" in summary_text
        assert "Total Area: 106.50" in summary_text  # Sum of all surface areas
        
        # Should show areas by type
        assert "Wall: 54.00" in summary_text  # 4 walls: 12+15+12+15
        assert "Floor: 25.00" in summary_text
        assert "Ceiling: 25.00" in summary_text
        assert "Opening: 2.50" in summary_text

    def test_surface_selection_emits_signal(self):
        """Test that selecting a surface emits the correct signal."""
        space = self.create_test_space_with_surfaces()
        self.space_detail_widget.display_space(space)
        
        # Mock signal handler
        signal_handler = Mock()
        self.space_detail_widget.surface_selected.connect(signal_handler)
        
        # Simulate clicking on first surface
        surfaces_table = self.space_detail_widget.surfaces_table
        first_item = surfaces_table.item(0, 0)
        
        # Trigger the click handler directly
        self.space_detail_widget.on_surface_clicked(first_item)
        
        # Check that signal was emitted with correct surface ID
        signal_handler.assert_called_once()
        args = signal_handler.call_args[0]
        assert len(args) == 1
        assert args[0] in ["wall-1", "wall-2", "wall-3", "wall-4", "floor-1", "ceiling-1", "window-1"]

    def test_empty_space_surfaces_display(self):
        """Test display of space with no surfaces."""
        space = SpaceData(
            guid="empty-space-guid",
            name="102",
            long_name="Empty Office 102",
            description="Empty test space",
            object_type="Office",
            zone_category="Office",
            number="102",
            elevation=0.0
        )
        
        # Display the space
        self.space_detail_widget.display_space(space)
        
        # Check that surfaces table is empty
        surfaces_table = self.space_detail_widget.surfaces_table
        assert surfaces_table.rowCount() == 0
        
        # Check summary shows no surfaces
        summary_label = self.space_detail_widget.surface_summary_label
        summary_text = summary_label.text()
        assert "Total Surfaces: 0" in summary_text
        assert "Total Area: 0.00" in summary_text

    def test_surface_with_user_descriptions(self):
        """Test display of surfaces with user descriptions."""
        space = self.create_test_space_with_surfaces()
        
        # Add user descriptions to some surfaces
        space.surfaces[0].set_user_description("North wall with windows")
        space.surfaces[4].set_user_description("Hardwood flooring")
        
        # Display the space
        self.space_detail_widget.display_space(space)
        
        # Check that descriptions are displayed in table
        surfaces_table = self.space_detail_widget.surfaces_table
        
        # Find the surface with description
        found_description = False
        for row in range(surfaces_table.rowCount()):
            description_item = surfaces_table.item(row, 3)  # Description column
            if description_item and description_item.text():
                found_description = True
                assert description_item.text() in ["North wall with windows", "Hardwood flooring"]
        
        assert found_description, "User descriptions should be displayed in the table"

    @patch('ifc_room_schedule.ui.main_window.MainWindow.extract_surfaces_for_spaces_with_error_handling')
    def test_main_window_surface_extraction_integration(self, mock_extract_surfaces):
        """Test integration of surface extraction in main window."""
        self.main_window._testing_mode = True  # Enable testing mode
        
        # Mock the IFC file loading
        with patch.object(self.main_window.ifc_reader, 'is_loaded', return_value=True):
            with patch.object(self.main_window.ifc_reader, 'validate_file', return_value=(True, "Valid")):
                with patch.object(self.main_window.ifc_reader, 'load_file', return_value=(True, "Loaded")):
                    with patch.object(self.main_window.space_extractor, 'extract_spaces') as mock_extract_spaces:
                        with patch.object(self.main_window.ifc_reader, 'get_ifc_file', return_value=Mock()):
                            with patch.object(self.main_window.surface_extractor, 'set_ifc_file'):
                                with patch.object(self.main_window.boundary_parser, 'set_ifc_file'):
                                    with patch.object(self.main_window.relationship_parser, 'set_ifc_file'):
                                        with patch.object(self.main_window, 'extract_boundaries_for_spaces_with_error_handling'):
                                            with patch.object(self.main_window, 'extract_relationships_for_spaces_with_error_handling'):
                                                
                                                # Create test spaces
                                                test_spaces = [self.create_test_space_with_surfaces()]
                                                mock_extract_spaces.return_value = test_spaces
                                                
                                                # Process a mock file
                                                self.main_window.process_ifc_file("test.ifc")
                                                
                                                # Verify that surface extraction was called
                                                mock_extract_surfaces.assert_called_once()
                        
                        # Verify spaces were loaded
                        assert len(self.main_window.spaces) == 1
                        assert self.main_window.spaces[0].guid == "test-space-guid"

    def test_surface_area_calculation_accuracy(self):
        """Test accuracy of surface area calculations."""
        space = self.create_test_space_with_surfaces()
        
        # Calculate areas manually
        expected_wall_area = 12.0 + 15.0 + 12.0 + 15.0  # 54.0
        expected_floor_area = 25.0
        expected_ceiling_area = 25.0
        expected_opening_area = 2.5
        expected_total = expected_wall_area + expected_floor_area + expected_ceiling_area + expected_opening_area
        
        # Check space calculations
        assert space.get_total_surface_area() == expected_total
        
        areas_by_type = space.get_surface_area_by_type()
        assert areas_by_type["Wall"] == expected_wall_area
        assert areas_by_type["Floor"] == expected_floor_area
        assert areas_by_type["Ceiling"] == expected_ceiling_area
        assert areas_by_type["Opening"] == expected_opening_area

    def test_surface_material_display(self):
        """Test that surface materials are displayed correctly."""
        space = self.create_test_space_with_surfaces()
        
        # Display the space
        self.space_detail_widget.display_space(space)
        
        # Check materials in table
        surfaces_table = self.space_detail_widget.surfaces_table
        materials_found = set()
        
        for row in range(surfaces_table.rowCount()):
            material_item = surfaces_table.item(row, 2)  # Material column
            if material_item:
                materials_found.add(material_item.text())
        
        # Should find all expected materials
        expected_materials = {"Concrete", "Wood", "Plaster", "Glass"}
        assert materials_found == expected_materials

    def test_surface_error_handling_display(self):
        """Test display of surfaces with missing or invalid data."""
        space = SpaceData(
            guid="error-space-guid",
            name="103",
            long_name="Error Test Space",
            description="Space with problematic surface data",
            object_type="Office",
            zone_category="Office",
            number="103",
            elevation=0.0
        )
        
        # Add surfaces with problematic data
        surfaces = [
            SurfaceData("good-surface", "Wall", 10.0, "Concrete", "IfcWall", space.guid),
            SurfaceData("zero-area", "Wall", 0.0, "Concrete", "IfcWall", space.guid),  # Zero area
            SurfaceData("no-material", "Floor", 25.0, "", "IfcSlab", space.guid),  # No material
        ]
        
        for surface in surfaces:
            space.add_surface(surface)
        
        # Display should handle errors gracefully
        self.space_detail_widget.display_space(space)
        
        # Check that all surfaces are displayed despite issues
        surfaces_table = self.space_detail_widget.surfaces_table
        assert surfaces_table.rowCount() == 3
        
        # Check that zero area is displayed
        found_zero_area = False
        found_no_material = False
        
        for row in range(surfaces_table.rowCount()):
            area_item = surfaces_table.item(row, 1)
            material_item = surfaces_table.item(row, 2)
            
            if area_item and area_item.text() == "0.00":
                found_zero_area = True
            if material_item and (material_item.text() == "" or material_item.text() == "Unknown"):
                found_no_material = True
        
        assert found_zero_area, "Zero area surfaces should be displayed"
        assert found_no_material, "Surfaces without materials should be displayed"