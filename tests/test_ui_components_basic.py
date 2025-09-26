"""
Basic Tests for UI Components (without PyQt6 dependency)

Tests the basic functionality of UI components without requiring PyQt6 installation.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ifc_room_schedule.data.space_model import SpaceData


def test_space_data_creation():
    """Test creating SpaceData objects for UI testing."""
    space = SpaceData(
        guid="TEST_SPACE_001",
        name="101",
        long_name="Test Office 101",
        description="Test office space",
        object_type="Office",
        zone_category="Office",
        number="101",
        elevation=0.0,
        quantities={"Height": 3.0, "Area": 25.5}
    )
    
    assert space.guid == "TEST_SPACE_001"
    assert space.name == "101"
    assert space.long_name == "Test Office 101"
    assert space.object_type == "Office"
    assert space.zone_category == "Office"
    assert space.number == "101"
    assert space.elevation == 0.0
    assert space.quantities["Height"] == 3.0
    assert space.quantities["Area"] == 25.5


def test_space_data_methods():
    """Test SpaceData methods used by UI components."""
    space = SpaceData(
        guid="TEST_SPACE_002",
        name="Meeting Room",
        long_name="Conference Room A",
        description="Main conference room",
        object_type="Meeting Room",
        zone_category="Meeting Room",
        number="CR-A",
        elevation=0.0,
        quantities={"Height": 3.2, "Area": 18.0, "Volume": 57.6}
    )
    
    # Test total surface area calculation (when no surfaces)
    total_area = space.get_total_surface_area()
    assert total_area == 0.0
    
    # Test surface area by type (when no surfaces)
    areas_by_type = space.get_surface_area_by_type()
    assert areas_by_type == {}
    
    # Test user descriptions
    space.set_user_description("notes", "This is a test note")
    assert space.get_user_description("notes") == "This is a test note"
    assert space.get_user_description("nonexistent") is None


def test_ui_data_formatting():
    """Test data formatting functions that would be used by UI components."""
    space = SpaceData(
        guid="SPACE_LONG_GUID_123456789",
        name="Office 205",
        long_name="Senior Manager Office",
        description="Corner office with windows",
        object_type="Office",
        zone_category="Office",
        number="205",
        elevation=2.5,
        quantities={"Height": 3.0, "Area": 32.5, "Volume": 97.5}
    )
    
    # Test display text formatting (simulating UI widget logic)
    def format_space_display_text(space_data):
        primary = space_data.number if space_data.number != "Unknown" else space_data.guid[-8:]
        if space_data.name and space_data.name != space_data.number:
            primary += f" - {space_data.name}"
        
        secondary = ""
        if space_data.long_name and space_data.long_name != space_data.name:
            secondary = space_data.long_name
        elif space_data.object_type:
            secondary = f"({space_data.object_type})"
        
        if secondary:
            return f"{primary}\n{secondary}"
        else:
            return primary
    
    display_text = format_space_display_text(space)
    expected = "205 - Office 205\nSenior Manager Office"
    assert display_text == expected
    
    # Test tooltip formatting (simulating UI widget logic)
    def format_space_tooltip(space_data):
        tooltip_parts = [
            f"GUID: {space_data.guid}",
            f"Number: {space_data.number}",
            f"Name: {space_data.name}",
            f"Long Name: {space_data.long_name}",
            f"Type: {space_data.object_type}",
            f"Category: {space_data.zone_category}",
            f"Elevation: {space_data.elevation}m"
        ]
        
        if space_data.quantities:
            tooltip_parts.append("Quantities:")
            for name, value in space_data.quantities.items():
                tooltip_parts.append(f"  {name}: {value}")
        
        return "\n".join(tooltip_parts)
    
    tooltip = format_space_tooltip(space)
    assert "GUID: SPACE_LONG_GUID_123456789" in tooltip
    assert "Number: 205" in tooltip
    assert "Height: 3.0" in tooltip
    assert "Area: 32.5" in tooltip


def test_space_filtering_logic():
    """Test space filtering logic that would be used by UI components."""
    spaces = [
        SpaceData(
            guid="SPACE001", name="101", long_name="Office 101",
            description="", object_type="Office", zone_category="Office",
            number="101", elevation=0.0
        ),
        SpaceData(
            guid="SPACE002", name="102", long_name="Meeting Room 102",
            description="", object_type="Meeting Room", zone_category="Meeting Room",
            number="102", elevation=0.0
        ),
        SpaceData(
            guid="SPACE003", name="Corridor", long_name="Main Corridor",
            description="", object_type="Corridor", zone_category="Corridor",
            number="C01", elevation=0.0
        )
    ]
    
    # Test filtering by "office"
    def filter_spaces(spaces_list, filter_text):
        if not filter_text:
            return spaces_list
            
        filter_lower = filter_text.lower()
        return [
            space for space in spaces_list
            if (filter_lower in space.name.lower() or
                filter_lower in space.long_name.lower() or
                filter_lower in space.object_type.lower() or
                filter_lower in space.zone_category.lower() or
                filter_lower in space.number.lower())
        ]
    
    # Filter by "office"
    office_spaces = filter_spaces(spaces, "office")
    assert len(office_spaces) == 1  # Only Office 101 contains "office"
    
    # Filter by "corridor"
    corridor_spaces = filter_spaces(spaces, "corridor")
    assert len(corridor_spaces) == 1
    assert corridor_spaces[0].name == "Corridor"
    
    # Filter by "101"
    room_101 = filter_spaces(spaces, "101")
    assert len(room_101) == 1
    assert room_101[0].number == "101"


def test_ui_state_management():
    """Test UI state management logic."""
    # Simulate UI state
    class MockUIState:
        def __init__(self):
            self.current_space_guid = None
            self.spaces = []
            self.is_file_loaded = False
            
        def load_spaces(self, spaces_list):
            self.spaces = spaces_list
            self.is_file_loaded = len(spaces_list) > 0
            
        def select_space(self, guid):
            for space in self.spaces:
                if space.guid == guid:
                    self.current_space_guid = guid
                    return True
            return False
            
        def get_selected_space(self):
            if self.current_space_guid:
                for space in self.spaces:
                    if space.guid == self.current_space_guid:
                        return space
            return None
            
        def clear_selection(self):
            self.current_space_guid = None
            
        def close_file(self):
            self.spaces = []
            self.current_space_guid = None
            self.is_file_loaded = False
    
    # Test state management
    ui_state = MockUIState()
    
    # Initially empty
    assert not ui_state.is_file_loaded
    assert ui_state.current_space_guid is None
    assert ui_state.get_selected_space() is None
    
    # Load spaces
    test_spaces = [
        SpaceData(
            guid="TEST001", name="Room1", long_name="Test Room 1",
            description="", object_type="Office", zone_category="Office",
            number="R1", elevation=0.0
        ),
        SpaceData(
            guid="TEST002", name="Room2", long_name="Test Room 2",
            description="", object_type="Office", zone_category="Office",
            number="R2", elevation=0.0
        )
    ]
    
    ui_state.load_spaces(test_spaces)
    assert ui_state.is_file_loaded
    assert len(ui_state.spaces) == 2
    
    # Select space
    success = ui_state.select_space("TEST001")
    assert success
    assert ui_state.current_space_guid == "TEST001"
    
    selected_space = ui_state.get_selected_space()
    assert selected_space is not None
    assert selected_space.name == "Room1"
    
    # Clear selection
    ui_state.clear_selection()
    assert ui_state.current_space_guid is None
    assert ui_state.get_selected_space() is None
    
    # Close file
    ui_state.close_file()
    assert not ui_state.is_file_loaded
    assert len(ui_state.spaces) == 0


if __name__ == "__main__":
    pytest.main([__file__])