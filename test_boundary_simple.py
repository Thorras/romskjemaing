#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ifc_room_schedule.parser.ifc_space_boundary_parser import IfcSpaceBoundaryParser
from ifc_room_schedule.data.space_boundary_model import SpaceBoundaryData

def test_basic_functionality():
    """Test basic functionality of the space boundary parser."""
    parser = IfcSpaceBoundaryParser()
    
    # Test initialization
    assert parser.ifc_file is None
    assert parser._boundaries_cache is None
    
    # Test boundary count with no file
    count = parser.get_boundary_count()
    assert count == 0
    
    # Test surface type classification
    assert parser._classify_boundary_surface_type("IfcWall") == "Wall"
    assert parser._classify_boundary_surface_type("IfcSlab") == "Floor"
    assert parser._classify_boundary_surface_type("") == "Unknown"
    
    print("All basic tests passed!")

if __name__ == "__main__":
    test_basic_functionality()