"""
Unit tests for GeometryExtractor class.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor, GeometryExtractionError
from ifc_room_schedule.visualization.geometry_models import Point2D, Polygon2D, FloorLevel, FloorGeometry


class TestGeometryExtractor:
    """Test GeometryExtractor functionality."""
    
    def test_extractor_initialization(self):
        """Test basic extractor initialization."""
        extractor = GeometryExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'logger')
    
    @patch('ifc_room_schedule.visualization.geometry_extractor.IFC_AVAILABLE', False)
    def test_initialization_without_ifcopenshell(self):
        """Test initialization fails without ifcopenshell."""
        with pytest.raises(ImportError):
            GeometryExtractor()
    
    def test_extract_floor_geometry_no_floors(self):
        """Test extraction with no building storeys."""
        extractor = GeometryExtractor()
        
        # Mock IFC file with no storeys
        mock_ifc_file = Mock()
        mock_ifc_file.by_type.return_value = []
        
        with pytest.raises(GeometryExtractionError) as exc_info:
            extractor.extract_floor_geometry(mock_ifc_file)
        
        assert exc_info.value.error_type == "no_floors"
    
    def test_get_floor_levels_with_storeys(self):
        """Test floor level extraction with building storeys."""
        extractor = GeometryExtractor()
        
        # Mock building storey
        mock_storey = Mock()
        mock_storey.GlobalId = "storey_1"
        mock_storey.Name = "Ground Floor"
        mock_storey.Elevation = 0.0
        
        # Mock IFC file
        mock_ifc_file = Mock()
        mock_ifc_file.by_type.side_effect = lambda entity_type: {
            "IfcBuildingStorey": [mock_storey],
            "IfcRelAggregates": [],
            "IfcRelContainedInSpatialStructure": []
        }.get(entity_type, [])
        
        # Mock elevation extraction
        with patch.object(extractor, '_extract_storey_elevation_enhanced', return_value=0.0):
            with patch.object(extractor, '_get_spaces_on_storey_enhanced', return_value=['space1', 'space2']):
                floor_levels = extractor.get_floor_levels(mock_ifc_file)
        
        assert len(floor_levels) == 1
        assert floor_levels[0].id == "storey_1"
        assert floor_levels[0].name == "Ground Floor"
        assert floor_levels[0].elevation == 0.0
        assert len(floor_levels[0].spaces) == 2
    
    def test_get_floor_levels_no_storeys_creates_default(self):
        """Test default floor creation when no storeys found."""
        extractor = GeometryExtractor()
        
        # Mock IFC file with no storeys but with spaces
        mock_space1 = Mock()
        mock_space1.GlobalId = "space1"
        mock_space2 = Mock()
        mock_space2.GlobalId = "space2"
        
        mock_ifc_file = Mock()
        mock_ifc_file.by_type.side_effect = lambda entity_type: {
            "IfcBuildingStorey": [],
            "IfcSpace": [mock_space1, mock_space2]
        }.get(entity_type, [])
        
        floor_levels = extractor.get_floor_levels(mock_ifc_file)
        
        assert len(floor_levels) >= 1
        # The new implementation groups by elevation, so the ID and name will be different
        assert floor_levels[0].elevation == 0.0
        assert len(floor_levels[0].spaces) == 2
    
    def test_extract_space_boundaries_with_boundaries(self):
        """Test space boundary extraction."""
        extractor = GeometryExtractor()
        
        # Mock IFC space
        mock_space = Mock()
        mock_space.GlobalId = "space1"
        mock_space.Name = "Test Room"
        
        # Mock space boundaries
        mock_boundary = Mock()
        
        with patch.object(extractor, '_get_space_boundaries_enhanced', return_value=[mock_boundary]):
            with patch.object(extractor, '_extract_boundary_polygon_enhanced') as mock_extract:
                # Mock polygon creation
                points = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)]
                mock_polygon = Polygon2D(points, "space1", "Test Room")
                mock_extract.return_value = mock_polygon
                
                polygons = extractor.extract_space_boundaries(mock_space)
        
        assert len(polygons) == 1
        assert polygons[0].space_guid == "space1"
        assert polygons[0].space_name == "Test Room"
    
    def test_extract_space_boundaries_fallback_to_direct(self):
        """Test fallback to direct geometry extraction."""
        extractor = GeometryExtractor()
        
        # Mock IFC space
        mock_space = Mock()
        mock_space.GlobalId = "space1"
        mock_space.Name = "Test Room"
        
        with patch.object(extractor, '_get_space_boundaries_enhanced', return_value=[]):
            with patch.object(extractor, '_extract_space_geometry_enhanced') as mock_direct:
                # Mock polygon creation
                points = [Point2D(0, 0), Point2D(2, 0), Point2D(2, 2), Point2D(0, 2)]
                mock_polygon = Polygon2D(points, "space1", "Test Room")
                mock_direct.return_value = mock_polygon
                
                polygons = extractor.extract_space_boundaries(mock_space)
        
        assert len(polygons) == 1
        assert polygons[0].space_guid == "space1"
    
    def test_extract_storey_elevation_from_placement(self):
        """Test elevation extraction from object placement."""
        extractor = GeometryExtractor()
        
        # Mock placement hierarchy
        mock_location = Mock()
        mock_location.Coordinates = [0.0, 0.0, 3.0]  # Z = 3.0
        
        mock_rel_placement = Mock()
        mock_rel_placement.Location = mock_location
        
        mock_placement = Mock()
        mock_placement.RelativePlacement = mock_rel_placement
        
        mock_storey = Mock()
        mock_storey.ObjectPlacement = mock_placement
        
        elevation = extractor._extract_storey_elevation_enhanced(mock_storey)
        assert elevation == 3.0
    
    def test_extract_storey_elevation_from_elevation_property(self):
        """Test elevation extraction from Elevation property."""
        extractor = GeometryExtractor()
        
        mock_storey = Mock()
        mock_storey.ObjectPlacement = None
        mock_storey.Elevation = 2.5
        
        elevation = extractor._extract_storey_elevation_enhanced(mock_storey)
        assert elevation == 2.5
    
    def test_extract_storey_elevation_default(self):
        """Test default elevation when no data available."""
        extractor = GeometryExtractor()
        
        mock_storey = Mock()
        mock_storey.ObjectPlacement = None
        mock_storey.Elevation = None
        
        elevation = extractor._extract_storey_elevation_enhanced(mock_storey)
        assert elevation == 0.0
    
    def test_get_spaces_on_storey_aggregates(self):
        """Test space extraction via IfcRelAggregates."""
        extractor = GeometryExtractor()
        
        # Mock storey object
        mock_storey = Mock()
        mock_storey.GlobalId = "storey1"
        mock_storey.Name = "Ground Floor"
        
        # Mock spaces
        mock_space1 = Mock()
        mock_space1.GlobalId = "space1"
        mock_space1.Name = "Room 1"
        mock_space1.is_a.return_value = True
        
        mock_space2 = Mock()
        mock_space2.GlobalId = "space2"
        mock_space2.Name = "Room 2"
        mock_space2.is_a.return_value = True
        
        # Mock relationship
        mock_rel = Mock()
        mock_rel.RelatingObject = mock_storey
        mock_rel.RelatedObjects = [mock_space1, mock_space2]
        
        # Mock IFC file
        mock_ifc_file = Mock()
        mock_ifc_file.by_type.side_effect = lambda entity_type: {
            "IfcRelAggregates": [mock_rel],
            "IfcRelContainedInSpatialStructure": [],
            "IfcSpace": []  # No additional spaces to avoid method 3
        }.get(entity_type, [])
        
        # Mock the validation and helper methods
        with patch.object(extractor, '_get_space_by_guid') as mock_get_space:
            with patch.object(extractor, '_validate_space_for_floor_plan', return_value=True):
                # Set up space retrieval
                mock_get_space.side_effect = lambda ifc_file, guid: {
                    "space1": mock_space1,
                    "space2": mock_space2
                }.get(guid)
                
                space_guids = extractor._get_spaces_on_storey_enhanced(mock_ifc_file, mock_storey)
        
        assert len(space_guids) == 2
        assert "space1" in space_guids
        assert "space2" in space_guids
    
    def test_memory_error_handling(self):
        """Test memory error handling."""
        extractor = GeometryExtractor()
        
        mock_ifc_file = Mock()
        mock_ifc_file.by_type.return_value = []  # Mock empty file to avoid progressive loading
        
        # Patch at the method level that directly raises MemoryError
        with patch.object(extractor, '_extract_geometry_standard', side_effect=MemoryError("Out of memory")):
            with pytest.raises(GeometryExtractionError) as exc_info:
                extractor.extract_floor_geometry(mock_ifc_file)
            
            assert exc_info.value.error_type == "memory_error"
    
    def test_general_error_handling(self):
        """Test general error handling."""
        extractor = GeometryExtractor()
        
        mock_ifc_file = Mock()
        
        with patch.object(extractor, 'get_floor_levels', side_effect=Exception("General error")):
            with pytest.raises(GeometryExtractionError) as exc_info:
                extractor.extract_floor_geometry(mock_ifc_file)
            
            assert exc_info.value.error_type == "extraction_error"
    
    def test_convert_to_2d_coordinates_with_geometry(self):
        """Test 3D to 2D coordinate conversion."""
        extractor = GeometryExtractor()
        
        # Mock 3D geometry with vertices
        mock_geometry = Mock()
        mock_geometry.verts = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0]  # 4 points
        mock_geometry.faces = [0, 1, 2, 3]
        
        polygon = extractor.convert_to_2d_coordinates(mock_geometry)
        
        assert polygon is not None
        assert len(polygon.points) >= 3
        assert polygon.points[0].x == 0.0
        assert polygon.points[0].y == 0.0
        assert polygon.points[1].x == 1.0
        assert polygon.points[1].y == 0.0
    
    def test_convert_to_2d_coordinates_invalid_geometry(self):
        """Test conversion with invalid geometry."""
        extractor = GeometryExtractor()
        
        # Mock invalid geometry
        mock_geometry = Mock()
        mock_geometry.verts = []
        
        polygon = extractor.convert_to_2d_coordinates(mock_geometry)
        assert polygon is None
    
    def test_extract_space_geometry_direct_with_quantities(self):
        """Test direct space geometry extraction with quantities."""
        extractor = GeometryExtractor()
        
        # Mock quantity
        mock_quantity = Mock()
        mock_quantity.is_a.return_value = True
        mock_quantity.Name = "NetFloorArea"
        mock_quantity.AreaValue = 16.0
        
        # Mock property definition
        mock_prop_def = Mock()
        mock_prop_def.is_a.return_value = True
        mock_prop_def.Quantities = [mock_quantity]
        
        # Mock definition relationship
        mock_definition = Mock()
        mock_definition.RelatingPropertyDefinition = mock_prop_def
        
        # Mock IFC space
        mock_space = Mock()
        mock_space.GlobalId = "space1"
        mock_space.Name = "Test Room"
        mock_space.IsDefinedBy = [mock_definition]
        
        with patch('ifcopenshell.geom.create_shape', side_effect=Exception("No shape")):
            polygon = extractor._extract_space_geometry_enhanced(mock_space, "space1", "Test Room")
        
        assert polygon is not None
        assert polygon.space_guid == "space1"
        assert polygon.space_name == "Test Room"
        # Should create a 4x4 square (area = 16)
        assert abs(polygon.get_area() - 16.0) < 1e-10