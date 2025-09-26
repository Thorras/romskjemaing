"""
Tests for IFC Relationship Parser

Tests the extraction of relationships between IFC entities.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ifc_room_schedule.parser.ifc_relationship_parser import IfcRelationshipParser
from ifc_room_schedule.data.relationship_model import RelationshipData


class TestIfcRelationshipParser:
    """Test cases for IfcRelationshipParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = IfcRelationshipParser()

    def test_init_without_file(self):
        """Test initialization without IFC file."""
        parser = IfcRelationshipParser()
        assert parser.ifc_file is None
        assert parser._relationships_cache == {}

    def test_init_with_file(self):
        """Test initialization with IFC file."""
        mock_file = Mock()
        parser = IfcRelationshipParser(mock_file)
        assert parser.ifc_file == mock_file

    def test_set_ifc_file(self):
        """Test setting IFC file."""
        mock_file = Mock()
        self.parser.set_ifc_file(mock_file)
        assert self.parser.ifc_file == mock_file
        assert self.parser._relationships_cache == {}

    def test_get_space_relationships_no_file(self):
        """Test getting relationships without loaded file."""
        with pytest.raises(ValueError, match="No IFC file loaded"):
            self.parser.get_space_relationships("TEST_GUID")

    def test_get_space_relationships_space_not_found(self):
        """Test getting relationships for non-existent space."""
        mock_file = Mock()
        mock_file.by_guid.side_effect = Exception("Not found")
        
        self.parser.set_ifc_file(mock_file)
        relationships = self.parser.get_space_relationships("NONEXISTENT")
        
        assert relationships == []

    def test_get_space_relationships_success(self):
        """Test successful relationship extraction."""
        # Create mock space entity
        mock_space = Mock()
        mock_space.GlobalId = "SPACE123456789ABC"
        mock_space.ContainedInStructure = []
        mock_space.ContainsElements = []
        mock_space.BoundedBy = []
        mock_space.ServicedBySystems = []
        mock_space.HasAssignments = []
        mock_space.IsAssignedTo = []
        mock_space.IsDefinedBy = []

        mock_file = Mock()
        mock_file.by_guid.return_value = mock_space
        
        self.parser.set_ifc_file(mock_file)
        relationships = self.parser.get_space_relationships("SPACE123456789ABC")
        
        assert isinstance(relationships, list)
        mock_file.by_guid.assert_called_once_with("SPACE123456789ABC")

    def test_extract_containment_relationships(self):
        """Test extraction of containment relationships."""
        # Create mock relating structure
        mock_structure = Mock()
        mock_structure.GlobalId = "STRUCTURE123"
        mock_structure.Name = "Building Level"
        mock_structure.Description = "Ground Floor"
        mock_structure.is_a.return_value = "IfcBuildingStorey"

        # Create mock containment relationship
        mock_rel = Mock()
        mock_rel.is_a.return_value = True
        mock_rel.RelatingStructure = mock_structure

        # Create mock space
        mock_space = Mock()
        mock_space.ContainedInStructure = [mock_rel]
        mock_space.ContainsElements = []

        def mock_is_a(type_name):
            return type_name == 'IfcRelContainedInSpatialStructure'

        mock_rel.is_a = mock_is_a

        relationships = self.parser._extract_containment_relationships(mock_space)
        
        assert len(relationships) == 1
        rel = relationships[0]
        assert isinstance(rel, RelationshipData)
        assert rel.related_entity_guid == "STRUCTURE123"
        assert rel.related_entity_name == "Building Level"
        assert rel.relationship_type == "Contains"

    def test_extract_adjacency_relationships(self):
        """Test extraction of adjacency relationships."""
        # Create mock adjacent space
        mock_adjacent_space = Mock()
        mock_adjacent_space.GlobalId = "ADJACENT123"
        mock_adjacent_space.Name = "Adjacent Room"
        mock_adjacent_space.Description = "Next door room"
        mock_adjacent_space.is_a.return_value = "IfcSpace"

        # Create mock corresponding boundary
        mock_corresponding_boundary = Mock()
        mock_corresponding_boundary.RelatingSpace = mock_adjacent_space

        # Create mock space boundary relationship
        mock_boundary_rel = Mock()
        mock_boundary_rel.is_a.return_value = True
        mock_boundary_rel.RelatedBuildingElement = Mock()
        mock_boundary_rel.CorrespondingBoundary = mock_corresponding_boundary

        # Create mock space
        mock_space = Mock()
        mock_space.BoundedBy = [mock_boundary_rel]

        def mock_is_a(type_name):
            return type_name == 'IfcRelSpaceBoundary'

        mock_boundary_rel.is_a = mock_is_a

        relationships = self.parser._extract_adjacency_relationships(mock_space)
        
        assert len(relationships) == 1
        rel = relationships[0]
        assert rel.related_entity_guid == "ADJACENT123"
        assert rel.relationship_type == "Adjacent"

    def test_extract_service_relationships(self):
        """Test extraction of service relationships."""
        # Create mock system
        mock_system = Mock()
        mock_system.GlobalId = "SYSTEM123"
        mock_system.Name = "HVAC System"
        mock_system.Description = "Heating and cooling"
        mock_system.is_a.return_value = "IfcSystem"

        # Create mock service relationship
        mock_service_rel = Mock()
        mock_service_rel.is_a.return_value = True
        mock_service_rel.RelatingSystem = mock_system

        # Create mock space
        mock_space = Mock()
        mock_space.ServicedBySystems = [mock_service_rel]

        def mock_is_a(type_name):
            return type_name == 'IfcRelServicesBuildings'

        mock_service_rel.is_a = mock_is_a

        relationships = self.parser._extract_service_relationships(mock_space)
        
        assert len(relationships) == 1
        rel = relationships[0]
        assert rel.related_entity_guid == "SYSTEM123"
        assert rel.relationship_type == "Serves"

    def test_extract_assignment_relationships(self):
        """Test extraction of assignment relationships."""
        # Create mock relating object
        mock_object = Mock()
        mock_object.GlobalId = "OBJECT123"
        mock_object.Name = "Assignment Object"
        mock_object.Description = "Assigned object"
        mock_object.is_a.return_value = "IfcGroup"

        # Create mock assignment relationship
        mock_assignment_rel = Mock()
        mock_assignment_rel.is_a.return_value = True
        mock_assignment_rel.RelatingObject = mock_object

        # Create mock space
        mock_space = Mock()
        mock_space.HasAssignments = [mock_assignment_rel]
        mock_space.IsAssignedTo = []

        def mock_is_a(type_name=None):
            if type_name:
                return type_name == 'IfcRelAssigns'
            return 'IfcRelAssigns'

        mock_assignment_rel.is_a = mock_is_a

        relationships = self.parser._extract_assignment_relationships(mock_space)
        
        assert len(relationships) == 1
        rel = relationships[0]
        assert rel.related_entity_guid == "OBJECT123"
        assert rel.relationship_type == "AssignedTo"

    def test_extract_definition_relationships(self):
        """Test extraction of definition relationships."""
        # Create mock property definition
        mock_property_def = Mock()
        mock_property_def.GlobalId = "PROPDEF123"
        mock_property_def.Name = "Property Set"
        mock_property_def.Description = "Space properties"
        mock_property_def.is_a.return_value = "IfcPropertySet"

        # Create mock definition relationship
        mock_def_rel = Mock()
        mock_def_rel.is_a.return_value = True
        mock_def_rel.RelatingPropertyDefinition = mock_property_def

        # Create mock space
        mock_space = Mock()
        mock_space.IsDefinedBy = [mock_def_rel]

        def mock_is_a(type_name):
            return type_name == 'IfcRelDefinesByProperties'

        mock_def_rel.is_a = mock_is_a

        relationships = self.parser._extract_definition_relationships(mock_space)
        
        assert len(relationships) == 1
        rel = relationships[0]
        assert rel.related_entity_guid == "PROPDEF123"
        assert rel.relationship_type == "DefinedBy"

    def test_create_relationship_data_success(self):
        """Test successful creation of relationship data."""
        mock_entity = Mock()
        mock_entity.GlobalId = "ENTITY123"
        mock_entity.Name = "Test Entity"
        mock_entity.Description = "Test description"
        mock_entity.is_a.return_value = "IfcWall"

        rel_data = self.parser._create_relationship_data(
            mock_entity, "Contains", "IfcRelContainedInSpatialStructure"
        )
        
        assert rel_data is not None
        assert rel_data.related_entity_guid == "ENTITY123"
        assert rel_data.related_entity_name == "Test Entity"
        assert rel_data.related_entity_description == "Test description"
        assert rel_data.relationship_type == "Contains"
        assert rel_data.ifc_relationship_type == "IfcRelContainedInSpatialStructure"

    def test_create_relationship_data_no_guid(self):
        """Test relationship data creation with missing GUID."""
        mock_entity = Mock()
        mock_entity.GlobalId = ""  # Empty GUID
        mock_entity.Name = "Test Entity"
        mock_entity.Description = "Test description"

        rel_data = self.parser._create_relationship_data(
            mock_entity, "Contains", "IfcRelContainedInSpatialStructure"
        )
        
        assert rel_data is None

    def test_create_relationship_data_no_name(self):
        """Test relationship data creation with missing name."""
        mock_entity = Mock()
        mock_entity.GlobalId = "ENTITY123"
        mock_entity.Name = ""  # Empty name
        mock_entity.Description = "Test description"
        mock_entity.is_a.return_value = "IfcWall"

        rel_data = self.parser._create_relationship_data(
            mock_entity, "Contains", "IfcRelContainedInSpatialStructure"
        )
        
        assert rel_data is not None
        assert rel_data.related_entity_name == "IfcWall"  # Should use entity type

    def test_categorize_relationships(self):
        """Test categorizing relationships by type."""
        relationships = [
            RelationshipData("GUID1", "Entity1", "Desc1", "Contains", "IfcRel1"),
            RelationshipData("GUID2", "Entity2", "Desc2", "Contains", "IfcRel2"),
            RelationshipData("GUID3", "Entity3", "Desc3", "Adjacent", "IfcRel3"),
            RelationshipData("GUID4", "Entity4", "Desc4", "Serves", "IfcRel4"),
        ]

        categorized = self.parser.categorize_relationships(relationships)
        
        assert "Contains" in categorized
        assert "Adjacent" in categorized
        assert "Serves" in categorized
        assert len(categorized["Contains"]) == 2
        assert len(categorized["Adjacent"]) == 1
        assert len(categorized["Serves"]) == 1

    def test_get_relationship_summary(self):
        """Test getting relationship summary."""
        # Mock the get_space_relationships method
        mock_relationships = [
            RelationshipData("GUID1", "Entity1", "Desc1", "Contains", "IfcRel1"),
            RelationshipData("GUID2", "Entity2", "Desc2", "Contains", "IfcRel2"),
            RelationshipData("GUID3", "Entity3", "Desc3", "Adjacent", "IfcRel3"),
        ]

        with patch.object(self.parser, 'get_space_relationships', return_value=mock_relationships):
            summary = self.parser.get_relationship_summary("TEST_GUID")
            
            assert summary["Contains"] == 2
            assert summary["Adjacent"] == 1

    def test_get_all_relationships(self):
        """Test getting relationships for all spaces."""
        # Create mock spaces
        mock_space1 = Mock()
        mock_space1.GlobalId = "SPACE1"
        mock_space2 = Mock()
        mock_space2.GlobalId = "SPACE2"

        mock_file = Mock()
        mock_file.by_type.return_value = [mock_space1, mock_space2]

        # Mock get_space_relationships
        mock_relationships = [
            RelationshipData("GUID1", "Entity1", "Desc1", "Contains", "IfcRel1")
        ]

        with patch.object(self.parser, 'get_space_relationships', return_value=mock_relationships):
            self.parser.set_ifc_file(mock_file)
            all_relationships = self.parser.get_all_relationships()
            
            assert "SPACE1" in all_relationships
            assert "SPACE2" in all_relationships
            assert len(all_relationships["SPACE1"]) == 1
            assert len(all_relationships["SPACE2"]) == 1

    def test_clear_cache(self):
        """Test clearing the relationships cache."""
        # Add something to cache
        self.parser._relationships_cache["TEST"] = []
        assert len(self.parser._relationships_cache) == 1
        
        # Clear cache
        self.parser.clear_cache()
        assert len(self.parser._relationships_cache) == 0

    def test_get_space_relationships_with_cache(self):
        """Test getting relationships with cached results."""
        mock_relationships = [
            RelationshipData("GUID1", "Entity1", "Desc1", "Contains", "IfcRel1")
        ]
        
        # Set up mock file first
        mock_file = Mock()
        self.parser.set_ifc_file(mock_file)
        
        # Add to cache
        self.parser._relationships_cache["TEST_GUID"] = mock_relationships
        
        # Should return cached results without calling IFC file
        relationships = self.parser.get_space_relationships("TEST_GUID")
        assert relationships == mock_relationships
        # Verify that by_guid was not called since we used cache
        mock_file.by_guid.assert_not_called()

    def test_get_space_relationships_runtime_error(self):
        """Test runtime error during relationship extraction."""
        mock_file = Mock()
        # Make the by_guid method raise an exception that's not caught by _find_entity_by_guid
        mock_file.by_guid.return_value = Mock()
        
        # Mock the _extract_containment_relationships to raise an exception
        with patch.object(self.parser, '_extract_containment_relationships', side_effect=Exception("Processing error")):
            self.parser.set_ifc_file(mock_file)
            
            with pytest.raises(RuntimeError, match="Failed to extract relationships"):
                self.parser.get_space_relationships("TEST_GUID")

    def test_find_entity_by_guid_success(self):
        """Test finding entity by GUID successfully."""
        mock_entity = Mock()
        mock_file = Mock()
        mock_file.by_guid.return_value = mock_entity
        
        self.parser.set_ifc_file(mock_file)
        entity = self.parser._find_entity_by_guid("TEST_GUID")
        
        assert entity == mock_entity
        mock_file.by_guid.assert_called_once_with("TEST_GUID")

    def test_find_entity_by_guid_not_found(self):
        """Test finding entity by GUID when not found."""
        mock_file = Mock()
        mock_file.by_guid.side_effect = Exception("Not found")
        
        self.parser.set_ifc_file(mock_file)
        entity = self.parser._find_entity_by_guid("NONEXISTENT")
        
        assert entity is None

    def test_duplicate_relationship_removal(self):
        """Test that duplicate relationships are removed."""
        # Create mock space with duplicate relationships
        mock_entity = Mock()
        mock_entity.GlobalId = "DUPLICATE_GUID"
        mock_entity.Name = "Duplicate Entity"
        mock_entity.Description = "Description"
        mock_entity.is_a.return_value = "IfcWall"

        mock_rel1 = Mock()
        mock_rel1.is_a.return_value = True
        mock_rel1.RelatingStructure = mock_entity

        mock_rel2 = Mock()
        mock_rel2.is_a.return_value = True
        mock_rel2.RelatingStructure = mock_entity

        mock_space = Mock()
        mock_space.ContainedInStructure = [mock_rel1, mock_rel2]  # Duplicate relationships
        mock_space.ContainsElements = []
        mock_space.BoundedBy = []
        mock_space.ServicedBySystems = []
        mock_space.HasAssignments = []
        mock_space.IsAssignedTo = []
        mock_space.IsDefinedBy = []

        def mock_is_a(type_name):
            return type_name == 'IfcRelContainedInSpatialStructure'

        mock_rel1.is_a = mock_is_a
        mock_rel2.is_a = mock_is_a

        mock_file = Mock()
        mock_file.by_guid.return_value = mock_space
        
        self.parser.set_ifc_file(mock_file)
        relationships = self.parser.get_space_relationships("TEST_GUID")
        
        # Should only have one relationship despite two identical ones
        assert len(relationships) == 1
        assert relationships[0].related_entity_guid == "DUPLICATE_GUID"

    def test_get_boundary_level_relationships(self):
        """Test getting relationships categorized by boundary level."""
        # Create mock building element for 1st level
        mock_building_element = Mock()
        mock_building_element.GlobalId = "ELEMENT123"
        mock_building_element.Name = "Wall Element"
        mock_building_element.Description = "Exterior wall"
        mock_building_element.is_a.return_value = "IfcWall"

        # Create mock adjacent space for 2nd level
        mock_adjacent_space = Mock()
        mock_adjacent_space.GlobalId = "ADJACENT123"
        mock_adjacent_space.Name = "Adjacent Room"
        mock_adjacent_space.Description = "Next room"
        mock_adjacent_space.is_a.return_value = "IfcSpace"

        # Create mock corresponding boundary
        mock_corresponding_boundary = Mock()
        mock_corresponding_boundary.RelatingSpace = mock_adjacent_space

        # Create mock space boundary relationship
        mock_boundary_rel = Mock()
        mock_boundary_rel.is_a.return_value = True
        mock_boundary_rel.RelatedBuildingElement = mock_building_element
        mock_boundary_rel.CorrespondingBoundary = mock_corresponding_boundary

        # Create mock space
        mock_space = Mock()
        mock_space.BoundedBy = [mock_boundary_rel]

        def mock_is_a(type_name):
            return type_name == 'IfcRelSpaceBoundary'

        mock_boundary_rel.is_a = mock_is_a

        mock_file = Mock()
        mock_file.by_guid.return_value = mock_space
        
        self.parser.set_ifc_file(mock_file)
        boundary_relationships = self.parser.get_boundary_level_relationships("TEST_GUID")
        
        assert 'first_level' in boundary_relationships
        assert 'second_level' in boundary_relationships
        assert len(boundary_relationships['first_level']) == 1
        assert len(boundary_relationships['second_level']) == 1
        
        # Check 1st level relationship
        first_level_rel = boundary_relationships['first_level'][0]
        assert first_level_rel.related_entity_guid == "ELEMENT123"
        assert first_level_rel.relationship_type == "BoundedBy"
        
        # Check 2nd level relationship
        second_level_rel = boundary_relationships['second_level'][0]
        assert second_level_rel.related_entity_guid == "ADJACENT123"
        assert second_level_rel.relationship_type == "AdjacentSpace"

    def test_extract_thermal_and_material_properties(self):
        """Test extraction of thermal and material properties."""
        # Create mock property with thermal information
        mock_thermal_prop = Mock()
        mock_thermal_prop.is_a.return_value = True
        mock_thermal_prop.Name = "ThermalConductivity"
        mock_thermal_prop.NominalValue = Mock()
        mock_thermal_prop.NominalValue.wrappedValue = 0.15

        # Create mock thermal property set
        mock_thermal_pset = Mock()
        mock_thermal_pset.is_a.return_value = True
        mock_thermal_pset.Name = "Pset_ThermalProperties"
        mock_thermal_pset.HasProperties = [mock_thermal_prop]

        # Create mock property relationship
        mock_prop_rel = Mock()
        mock_prop_rel.is_a.return_value = True
        mock_prop_rel.RelatingPropertyDefinition = mock_thermal_pset

        # Create mock building element
        mock_element = Mock()
        mock_element.IsDefinedBy = [mock_prop_rel]
        mock_element.HasAssociations = []

        def mock_is_a_prop_rel(type_name):
            return type_name == 'IfcRelDefinesByProperties'

        def mock_is_a_pset(type_name):
            return type_name == 'IfcPropertySet'

        def mock_is_a_prop(type_name):
            return type_name == 'IfcPropertySingleValue'

        mock_prop_rel.is_a = mock_is_a_prop_rel
        mock_thermal_pset.is_a = mock_is_a_pset
        mock_thermal_prop.is_a = mock_is_a_prop

        mock_file = Mock()
        mock_file.by_guid.return_value = mock_element
        
        self.parser.set_ifc_file(mock_file)
        properties = self.parser.extract_thermal_and_material_properties("ELEMENT123")
        
        assert 'thermal_properties' in properties
        assert 'material_properties' in properties
        assert 'ThermalConductivity' in properties['thermal_properties']
        assert properties['thermal_properties']['ThermalConductivity'] == 0.15

    def test_analyze_boundary_hierarchies(self):
        """Test analysis of boundary hierarchies."""
        # Mock the get_boundary_level_relationships method
        mock_boundary_relationships = {
            'first_level': [
                RelationshipData("WALL1", "Wall 1", "Exterior wall", "BoundedBy", "IfcRelSpaceBoundary"),
                RelationshipData("FLOOR1", "Floor 1", "Floor slab", "BoundedBy", "IfcRelSpaceBoundary")
            ],
            'second_level': [
                RelationshipData("SPACE2", "Room 102", "Adjacent room", "AdjacentSpace", "IfcRelSpaceBoundary")
            ]
        }

        with patch.object(self.parser, 'get_boundary_level_relationships', return_value=mock_boundary_relationships):
            self.parser.set_ifc_file(Mock())
            analysis = self.parser.analyze_boundary_hierarchies("TEST_GUID")
            
            assert analysis['first_level_count'] == 2
            assert analysis['second_level_count'] == 1
            assert analysis['hierarchy_depth'] == 2
            assert 'building_elements' in analysis
            assert 'adjacent_spaces' in analysis
            assert 'SPACE2' in analysis['adjacent_spaces']

    def test_extract_properties_from_set(self):
        """Test extraction of properties from property set."""
        # Create mock single value property
        mock_single_prop = Mock()
        mock_single_prop.is_a.return_value = True
        mock_single_prop.Name = "SingleValue"
        mock_single_prop.NominalValue = Mock()
        mock_single_prop.NominalValue.wrappedValue = 42.0

        # Create mock enumerated property
        mock_enum_prop = Mock()
        mock_enum_prop.is_a.return_value = False
        mock_enum_prop.Name = "EnumValue"

        # Create mock property set
        mock_pset = Mock()
        mock_pset.HasProperties = [mock_single_prop, mock_enum_prop]

        def mock_is_a_single(type_name):
            return type_name == 'IfcPropertySingleValue'

        def mock_is_a_enum(type_name):
            return type_name == 'IfcPropertyEnumeratedValue'

        mock_single_prop.is_a = mock_is_a_single
        mock_enum_prop.is_a = mock_is_a_enum

        properties = self.parser._extract_properties_from_set(mock_pset)
        
        assert 'SingleValue' in properties
        assert properties['SingleValue'] == 42.0

    def test_extract_material_info(self):
        """Test extraction of material information."""
        # Create mock material
        mock_material = Mock()
        mock_material.is_a.return_value = True
        mock_material.Name = "Concrete"
        mock_material.Description = "Structural concrete"
        mock_material.Category = "Structural"

        def mock_is_a(type_name):
            return type_name == 'IfcMaterial'

        mock_material.is_a = mock_is_a

        material_info = self.parser._extract_material_info(mock_material)
        
        assert material_info['name'] == "Concrete"
        assert material_info['description'] == "Structural concrete"
        assert material_info['category'] == "Structural"

    def test_classify_boundary_level_relationships(self):
        """Test classification of boundary level relationships."""
        # Mock the get_boundary_level_relationships method
        mock_boundary_relationships = {
            'first_level': [
                RelationshipData("WALL1", "Wall 1", "Exterior wall", "BoundedBy", "IfcRelSpaceBoundary"),
                RelationshipData("FLOOR1", "Floor 1", "Floor slab", "BoundedBy", "IfcRelSpaceBoundary")
            ],
            'second_level': [
                RelationshipData("SPACE2", "Room 102", "Adjacent room", "AdjacentSpace", "IfcRelSpaceBoundary")
            ]
        }

        # Mock thermal and material properties extraction
        mock_properties = {
            'thermal_properties': {'ThermalConductivity': 0.15, 'ThermalResistance': 2.5},
            'material_properties': {'MaterialName': 'Concrete', 'Density': 2400}
        }

        with patch.object(self.parser, 'get_boundary_level_relationships', return_value=mock_boundary_relationships):
            with patch.object(self.parser, 'extract_thermal_and_material_properties', return_value=mock_properties):
                self.parser.set_ifc_file(Mock())
                classification = self.parser.classify_boundary_level_relationships("TEST_GUID")
                
                assert classification['first_level']['count'] == 2
                assert classification['second_level']['count'] == 1
                assert classification['hierarchy_analysis']['max_depth'] == 2
                assert classification['hierarchy_analysis']['has_space_to_space_connections'] == True
                assert len(classification['first_level']['building_elements']) == 2
                assert len(classification['second_level']['adjacent_spaces']) == 1

    def test_get_boundary_hierarchy_tree(self):
        """Test getting boundary hierarchy tree."""
        # Mock the classify_boundary_level_relationships method
        mock_classification = {
            'first_level': {
                'count': 2,
                'building_elements': {
                    'WALL1': {
                        'name': 'Wall 1',
                        'description': 'Exterior wall',
                        'thermal_properties': {'ThermalConductivity': 0.15},
                        'material_properties': {'MaterialName': 'Concrete'}
                    }
                },
                'thermal_properties': {'ThermalConductivity': [0.15]},
                'material_properties': {'MaterialName': ['Concrete']}
            },
            'second_level': {
                'count': 1,
                'adjacent_spaces': {
                    'SPACE2': {
                        'name': 'Room 102',
                        'description': 'Adjacent room',
                        'connection_type': 'space_to_space'
                    }
                }
            },
            'hierarchy_analysis': {
                'total_boundary_count': 3,
                'max_depth': 2
            }
        }

        with patch.object(self.parser, 'classify_boundary_level_relationships', return_value=mock_classification):
            with patch.object(self.parser, '_get_space_name', return_value='Test Space'):
                self.parser.set_ifc_file(Mock())
                hierarchy_tree = self.parser.get_boundary_hierarchy_tree("TEST_GUID")
                
                assert hierarchy_tree['space_name'] == 'Test Space'
                assert hierarchy_tree['boundary_levels']['level_1']['count'] == 2
                assert hierarchy_tree['boundary_levels']['level_2']['count'] == 1
                assert hierarchy_tree['summary']['total_boundaries'] == 3
                assert hierarchy_tree['summary']['max_hierarchy_depth'] == 2

    def test_validate_boundary_hierarchy(self):
        """Test validation of boundary hierarchy."""
        # Mock the classify_boundary_level_relationships method
        mock_classification = {
            'first_level': {
                'count': 4,
                'relationships': [
                    RelationshipData("WALL1", "Wall 1", "Wall", "BoundedBy", "IfcRelSpaceBoundary"),
                    RelationshipData("WALL2", "Wall 2", "Wall", "BoundedBy", "IfcRelSpaceBoundary"),
                    RelationshipData("FLOOR1", "Floor 1", "Floor", "BoundedBy", "IfcRelSpaceBoundary"),
                    RelationshipData("CEILING1", "Ceiling 1", "Ceiling", "BoundedBy", "IfcRelSpaceBoundary")
                ],
                'building_elements': {
                    'WALL1': {'thermal_properties': {'ThermalConductivity': 0.15}, 'material_properties': {'MaterialName': 'Concrete'}},
                    'WALL2': {'thermal_properties': {}, 'material_properties': {}},
                    'FLOOR1': {'thermal_properties': {'ThermalConductivity': 0.20}, 'material_properties': {'MaterialName': 'Concrete'}},
                    'CEILING1': {'thermal_properties': {}, 'material_properties': {}}
                }
            },
            'second_level': {
                'count': 1,
                'relationships': [
                    RelationshipData("SPACE2", "Room 102", "Adjacent", "AdjacentSpace", "IfcRelSpaceBoundary")
                ]
            }
        }

        with patch.object(self.parser, 'classify_boundary_level_relationships', return_value=mock_classification):
            self.parser.set_ifc_file(Mock())
            validation = self.parser.validate_boundary_hierarchy("TEST_GUID")
            
            assert validation['is_valid'] == True
            assert validation['statistics']['first_level_boundaries'] == 4
            assert validation['statistics']['second_level_boundaries'] == 1
            assert validation['statistics']['elements_with_thermal_properties'] == 2
            assert validation['statistics']['elements_with_material_properties'] == 2

    def test_extract_thermal_properties_from_materials(self):
        """Test extraction of thermal properties from materials."""
        # Create mock material layer
        mock_layer = Mock()
        mock_layer.LayerThickness = 0.2
        mock_layer_material = Mock()
        mock_layer_material.HasProperties = []
        mock_layer.Material = mock_layer_material

        # Create mock material layer set
        mock_material_layer_set = Mock()
        mock_material_layer_set.is_a.return_value = True
        mock_material_layer_set.MaterialLayers = [mock_layer]

        # Create mock association
        mock_association = Mock()
        mock_association.is_a.return_value = True
        mock_association.RelatingMaterial = mock_material_layer_set

        # Create mock building element
        mock_element = Mock()
        mock_element.HasAssociations = [mock_association]

        def mock_is_a_assoc(type_name):
            return type_name == 'IfcRelAssociatesMaterial'

        def mock_is_a_material(type_name):
            return type_name == 'IfcMaterialLayerSet'

        mock_association.is_a = mock_is_a_assoc
        mock_material_layer_set.is_a = mock_is_a_material

        thermal_props = self.parser._extract_thermal_properties_from_materials(mock_element)
        
        assert 'layer_count' in thermal_props
        assert 'total_thickness' in thermal_props
        assert thermal_props['layer_count'] == 1
        assert thermal_props['total_thickness'] == 0.2