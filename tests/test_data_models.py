"""
Unit tests for data models and storage operations.
"""

import pytest
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.data.surface_model import SurfaceData
from ifc_room_schedule.data.relationship_model import RelationshipData
from ifc_room_schedule.data.space_repository import SpaceRepository


class TestSpaceData:
    """Test cases for SpaceData class."""
    
    def test_space_data_creation(self):
        """Test creating a valid SpaceData instance."""
        space = SpaceData(
            guid="test-guid-123",
            name="Test Room",
            long_name="Test Room Long Name",
            description="A test room",
            object_type="Room",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        
        assert space.guid == "test-guid-123"
        assert space.name == "Test Room"
        assert space.elevation == 0.0
        assert space.processed is False
        assert len(space.surfaces) == 0
        assert len(space.relationships) == 0
    
    def test_space_data_validation_missing_guid(self):
        """Test validation fails when GUID is missing."""
        with pytest.raises(ValueError, match="GUID is required"):
            SpaceData(
                guid="",
                name="Test Room",
                long_name="Test Room Long Name",
                description="A test room",
                object_type="Room",
                zone_category="Office",
                number="101",
                elevation=0.0
            )
    
    def test_space_data_validation_invalid_guid_type(self):
        """Test validation fails when GUID is not a string."""
        with pytest.raises(TypeError, match="GUID must be a string"):
            SpaceData(
                guid=123,
                name="Test Room",
                long_name="Test Room Long Name",
                description="A test room",
                object_type="Room",
                zone_category="Office",
                number="101",
                elevation=0.0
            )
    
    def test_space_data_validation_missing_name(self):
        """Test validation allows missing name if long_name is present."""
        # This should NOT raise an error since long_name is provided
        space = SpaceData(
            guid="test-guid-123",
            name="",
            long_name="Test Room Long Name",
            description="A test room",
            object_type="Room",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        assert space.long_name == "Test Room Long Name"
    
    def test_space_data_validation_invalid_elevation_type(self):
        """Test validation fails when elevation is not a number."""
        with pytest.raises(TypeError, match="Elevation must be a number"):
            SpaceData(
                guid="test-guid-123",
                name="Test Room",
                long_name="Test Room Long Name",
                description="A test room",
                object_type="Room",
                zone_category="Office",
                number="101",
                elevation="not a number"
            )
    
    def test_add_surface(self):
        """Test adding surfaces to a space."""
        space = SpaceData(
            guid="test-guid-123",
            name="Test Room",
            long_name="Test Room Long Name",
            description="A test room",
            object_type="Room",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        
        surface = SurfaceData(
            id="surface-1",
            type="Wall",
            area=10.5,
            material="Concrete",
            ifc_type="IfcWall",
            related_space_guid="test-guid-123"
        )
        
        space.add_surface(surface)
        assert len(space.surfaces) == 1
        assert space.surfaces[0] == surface
        
        # Test adding duplicate surface (should not add)
        space.add_surface(surface)
        assert len(space.surfaces) == 1
    
    def test_add_surface_invalid_type(self):
        """Test adding invalid surface type raises error."""
        space = SpaceData(
            guid="test-guid-123",
            name="Test Room",
            long_name="Test Room Long Name",
            description="A test room",
            object_type="Room",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        
        with pytest.raises(TypeError, match="Surface must be a SurfaceData instance"):
            space.add_surface("not a surface")
    
    def test_add_relationship(self):
        """Test adding relationships to a space."""
        space = SpaceData(
            guid="test-guid-123",
            name="Test Room",
            long_name="Test Room Long Name",
            description="A test room",
            object_type="Room",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        
        relationship = RelationshipData(
            related_entity_guid="related-guid-456",
            related_entity_name="Adjacent Room",
            related_entity_description="Room next door",
            relationship_type="Adjacent",
            ifc_relationship_type="IfcRelSpaceBoundary"
        )
        
        space.add_relationship(relationship)
        assert len(space.relationships) == 1
        assert space.relationships[0] == relationship
        
        # Test adding duplicate relationship (should not add)
        space.add_relationship(relationship)
        assert len(space.relationships) == 1
    
    def test_add_relationship_invalid_type(self):
        """Test adding invalid relationship type raises error."""
        space = SpaceData(
            guid="test-guid-123",
            name="Test Room",
            long_name="Test Room Long Name",
            description="A test room",
            object_type="Room",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        
        with pytest.raises(TypeError, match="Relationship must be a RelationshipData instance"):
            space.add_relationship("not a relationship")
    
    def test_get_total_surface_area(self):
        """Test calculating total surface area."""
        space = SpaceData(
            guid="test-guid-123",
            name="Test Room",
            long_name="Test Room Long Name",
            description="A test room",
            object_type="Room",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        
        # Add surfaces with different areas
        surface1 = SurfaceData(
            id="surface-1",
            type="Wall",
            area=10.5,
            material="Concrete",
            ifc_type="IfcWall",
            related_space_guid="test-guid-123"
        )
        
        surface2 = SurfaceData(
            id="surface-2",
            type="Floor",
            area=25.0,
            material="Tile",
            ifc_type="IfcSlab",
            related_space_guid="test-guid-123"
        )
        
        surface3 = SurfaceData(
            id="surface-3",
            type="Wall",
            area=0.0,  # Should be excluded
            material="Glass",
            ifc_type="IfcWall",
            related_space_guid="test-guid-123"
        )
        
        space.add_surface(surface1)
        space.add_surface(surface2)
        space.add_surface(surface3)
        
        total_area = space.get_total_surface_area()
        assert total_area == 35.5  # 10.5 + 25.0, excluding 0.0
    
    def test_get_surface_area_by_type(self):
        """Test getting surface areas grouped by type."""
        space = SpaceData(
            guid="test-guid-123",
            name="Test Room",
            long_name="Test Room Long Name",
            description="A test room",
            object_type="Room",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        
        # Add surfaces of different types
        wall1 = SurfaceData(
            id="wall-1",
            type="Wall",
            area=10.5,
            material="Concrete",
            ifc_type="IfcWall",
            related_space_guid="test-guid-123"
        )
        
        wall2 = SurfaceData(
            id="wall-2",
            type="Wall",
            area=12.0,
            material="Concrete",
            ifc_type="IfcWall",
            related_space_guid="test-guid-123"
        )
        
        floor = SurfaceData(
            id="floor-1",
            type="Floor",
            area=25.0,
            material="Tile",
            ifc_type="IfcSlab",
            related_space_guid="test-guid-123"
        )
        
        space.add_surface(wall1)
        space.add_surface(wall2)
        space.add_surface(floor)
        
        areas_by_type = space.get_surface_area_by_type()
        assert areas_by_type["Wall"] == 22.5  # 10.5 + 12.0
        assert areas_by_type["Floor"] == 25.0
        assert len(areas_by_type) == 2
    
    def test_user_descriptions(self):
        """Test setting and getting user descriptions."""
        space = SpaceData(
            guid="test-guid-123",
            name="Test Room",
            long_name="Test Room Long Name",
            description="A test room",
            object_type="Room",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        
        # Test setting description
        space.set_user_description("general", "This is a test room")
        assert space.get_user_description("general") == "This is a test room"
        
        # Test getting non-existent description
        assert space.get_user_description("nonexistent") is None
        
        # Test invalid types
        with pytest.raises(TypeError, match="Key and description must be strings"):
            space.set_user_description(123, "description")
        
        with pytest.raises(TypeError, match="Key and description must be strings"):
            space.set_user_description("key", 123)


class TestSurfaceData:
    """Test cases for SurfaceData class."""
    
    def test_surface_data_creation(self):
        """Test creating a valid SurfaceData instance."""
        surface = SurfaceData(
            id="surface-1",
            type="Wall",
            area=10.5,
            material="Concrete",
            ifc_type="IfcWall",
            related_space_guid="space-guid-123"
        )
        
        assert surface.id == "surface-1"
        assert surface.type == "Wall"
        assert surface.area == 10.5
        assert surface.material == "Concrete"
        assert surface.user_description == ""
        assert len(surface.properties) == 0


class TestRelationshipData:
    """Test cases for RelationshipData class."""
    
    def test_relationship_data_creation(self):
        """Test creating a valid RelationshipData instance."""
        relationship = RelationshipData(
            related_entity_guid="related-guid-456",
            related_entity_name="Adjacent Room",
            related_entity_description="Room next door",
            relationship_type="Adjacent",
            ifc_relationship_type="IfcRelSpaceBoundary"
        )
        
        assert relationship.related_entity_guid == "related-guid-456"
        assert relationship.related_entity_name == "Adjacent Room"
        assert relationship.relationship_type == "Adjacent"


class TestSpaceRepository:
    """Test cases for SpaceRepository class."""
    
    def test_space_repository_creation(self):
        """Test creating a SpaceRepository instance."""
        repository = SpaceRepository()
        assert repository is not None
        # Add more tests when SpaceRepository is implemented


if __name__ == "__main__":
    pytest.main([__file__])