#!/usr/bin/env python3
"""
NS Standards Prototype Test

Test script to demonstrate NS 8360/NS 3940 standards integration prototype.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ifc_room_schedule.parsers.ns8360_name_parser import NS8360NameParser
from ifc_room_schedule.mappers.ns3940_classifier import NS3940Classifier
from ifc_room_schedule.mappers.enhanced_identification_mapper import EnhancedIdentificationMapper
from ifc_room_schedule.data.space_model import SpaceData


def test_ns8360_parsing():
    """Test NS 8360 name parsing functionality."""
    print("🔍 Testing NS 8360 Name Parsing")
    print("=" * 50)
    
    parser = NS8360NameParser()
    
    test_cases = [
        "SPC-02-A101-111-003",  # Valid with zone - Stue
        "SPC-01-A101-130-001",  # Valid with zone - Våtrom
        "SPC-02-111-003",       # Valid without zone
        "Bad 2. etasje",        # Norwegian inference
        "Stue leilighet A101",  # Norwegian inference
        "Kjøkken",              # Simple Norwegian
        "Living room 3",        # English inference
        "InvalidName123",       # Invalid
    ]
    
    for test_case in test_cases:
        result = parser.parse(test_case)
        print(f"\n📝 Input: '{test_case}'")
        print(f"   ✅ Valid: {result.is_valid}")
        print(f"   📊 Confidence: {result.confidence:.2f}")
        if result.function_code:
            print(f"   🏠 Function Code: {result.function_code}")
        if result.storey:
            print(f"   🏢 Storey: {result.storey}")
        if result.zone:
            print(f"   📍 Zone: {result.zone}")
        if result.sequence:
            print(f"   🔢 Sequence: {result.sequence}")


def test_ns3940_classification():
    """Test NS 3940 classification functionality."""
    print("\n\n🏷️ Testing NS 3940 Classification")
    print("=" * 50)
    
    classifier = NS3940Classifier()
    
    # Test function codes
    test_codes = ["111", "121", "130", "131", "132", "140"]
    
    for code in test_codes:
        classification = classifier.classify_from_code(code)
        if classification:
            print(f"\n🔑 Function Code: {code}")
            print(f"   📋 Label: {classification.label}")
            print(f"   🏠 Category: {classification.category}")
            print(f"   💧 Wet Room: {classification.is_wet_room}")
            print(f"   🔧 Equipment Types: {len(classification.typical_equipment)}")
            
            # Show lighting requirements
            lighting = classification.performance_defaults.get('lighting', {})
            if lighting.get('task_lux'):
                print(f"   💡 Task Lighting: {lighting['task_lux']} lux")
            
            # Show ventilation requirements  
            ventilation = classification.performance_defaults.get('ventilation', {})
            if ventilation.get('airflow_supply_m3h'):
                print(f"   🌬️ Supply Air: {ventilation['airflow_supply_m3h']} m³/h per m²")
            if ventilation.get('airflow_extract_m3h'):
                print(f"   🌬️ Extract Air: {ventilation['airflow_extract_m3h']} m³/h")
    
    # Test name inference
    print(f"\n📝 Testing Name Inference:")
    test_names = ["Stue", "Bad", "Kjøkken", "Soverom", "WC", "Baderom"]
    
    for name in test_names:
        classification = classifier.classify_from_name(name)
        if classification:
            print(f"   '{name}' → {classification.function_code} ({classification.label})")


def test_enhanced_identification_mapping():
    """Test enhanced identification mapping with real scenarios."""
    print("\n\n🗺️ Testing Enhanced Identification Mapping")
    print("=" * 50)
    
    # Create realistic test spaces
    test_spaces = [
        SpaceData(
            guid="3M7XjWNGH0ORjOm8bMFrr3",
            name="SPC-02-A101-111-003",
            long_name="Stue | 02/A101 | NS3940:111",
            description="Oppholdsrom i leilighet A101",
            object_type="IfcSpace",
            zone_category="Residential",
            number="003",
            elevation=6.0,
            quantities={"NetFloorArea": 24.0, "GrossFloorArea": 25.5, "Height": 2.4}
        ),
        SpaceData(
            guid="1A2B3C4D5E6F7G8H9I0J1K",
            name="Bad 2. etasje",  # Non-compliant name
            long_name="",
            description="Bad med dusj og WC",
            object_type="IfcSpace", 
            zone_category="Residential",
            number="001",
            elevation=6.0,
            quantities={"NetFloorArea": 4.8, "GrossFloorArea": 5.2, "Height": 2.4}
        ),
        SpaceData(
            guid="9Z8Y7X6W5V4U3T2S1R0Q9P",
            name="Kjøkken A101",
            long_name="Kjøkken i leilighet A101",
            description="Kjøkken med øy",
            object_type="IfcSpace",
            zone_category="Residential", 
            number="002",
            elevation=6.0,
            quantities={"NetFloorArea": 12.5, "GrossFloorArea": 13.2, "Height": 2.4}
        )
    ]
    
    mapper = EnhancedIdentificationMapper()
    
    for i, space in enumerate(test_spaces, 1):
        print(f"\n🏠 Test Space {i}: '{space.name}'")
        print("-" * 40)
        
        # Test identification mapping
        identification = mapper.map_identification(space, "AkkordSvingen_23_ARK.ifc")
        print(f"📍 Project: {identification.project_name}")
        print(f"🏢 Building: {identification.building_name}")
        print(f"📊 Storey: {identification.storey_name}")
        print(f"🔢 Room Number: {identification.room_number}")
        print(f"📝 Room Name: {identification.room_name}")
        print(f"🏷️ Function: {identification.function}")
        print(f"👥 Occupancy: {identification.occupancy_type}")
        
        # Test classification
        classification = mapper.map_classification(space)
        if classification.ns3940:
            ns3940 = classification.ns3940
            print(f"🔑 NS 3940 Code: {ns3940['code']} ({ns3940['label']})")
            print(f"📊 Confidence: {ns3940['confidence']:.2f}")
            print(f"📋 Source: {ns3940['source']}")
        
        ns8360 = classification.ns8360_compliance
        print(f"✅ NS 8360 Compliant: {ns8360['name_pattern_valid']}")
        
        # Test IFC metadata
        ifc_metadata = mapper.map_ifc_metadata(space, "AkkordSvingen_23_ARK.ifc")
        print(f"🆔 Space GUID: {ifc_metadata.space_global_id[:8]}...")
        print(f"📁 Source File: {ifc_metadata.model_source['file_name']}")
        
        if ifc_metadata.parsed_name_components:
            components = ifc_metadata.parsed_name_components
            print(f"🧩 Parsed Components: {components}")


def generate_sample_json_output():
    """Generate sample JSON output to demonstrate the enhanced structure."""
    print("\n\n📄 Sample Enhanced JSON Output")
    print("=" * 50)
    
    # Create a sample space
    space = SpaceData(
        guid="3M7XjWNGH0ORjOm8bMFrr3",
        name="SPC-02-A101-111-003",
        long_name="Stue | 02/A101 | NS3940:111",
        description="Oppholdsrom i leilighet A101",
        object_type="IfcSpace",
        zone_category="Residential",
        number="003",
        elevation=6.0,
        quantities={"NetFloorArea": 24.0, "GrossFloorArea": 25.5, "Height": 2.4}
    )
    
    mapper = EnhancedIdentificationMapper()
    
    # Generate all sections
    meta = mapper.map_meta(space, "IFC Room Schedule Generator")
    identification = mapper.map_identification(space, "AkkordSvingen_23_ARK.ifc")
    ifc_metadata = mapper.map_ifc_metadata(space, "AkkordSvingen_23_ARK.ifc")
    classification = mapper.map_classification(space)
    
    # Get performance defaults
    classifier = NS3940Classifier()
    room_classification = classifier.classify_from_code("111")
    
    # Build sample JSON structure
    sample_json = {
        "meta": {
            "schema_version": meta.schema_version,
            "locale": meta.locale,
            "created_at": meta.created_at,
            "status": meta.status
        },
        "identification": {
            "project_name": identification.project_name,
            "building_name": identification.building_name,
            "storey_name": identification.storey_name,
            "room_number": identification.room_number,
            "room_name": identification.room_name,
            "function": identification.function,
            "occupancy_type": identification.occupancy_type
        },
        "ifc": {
            "space_global_id": ifc_metadata.space_global_id,
            "space_long_name": ifc_metadata.space_long_name,
            "ns8360_compliant": ifc_metadata.ns8360_compliant,
            "parsed_name_components": ifc_metadata.parsed_name_components,
            "model_source": ifc_metadata.model_source
        },
        "classification": {
            "ns3940": classification.ns3940,
            "ns8360_compliance": classification.ns8360_compliance
        },
        "geometry": {
            "area_nett_m2": space.quantities.get("NetFloorArea"),
            "area_brutto_m2": space.quantities.get("GrossFloorArea"), 
            "clear_height_m": space.quantities.get("Height")
        }
    }
    
    # Add performance requirements from NS 3940
    if room_classification:
        sample_json["performance_requirements"] = room_classification.performance_defaults
        sample_json["fixtures_and_equipment"] = room_classification.typical_equipment
        sample_json["hse_and_accessibility"] = room_classification.accessibility_requirements
    
    import json
    print(json.dumps(sample_json, indent=2, ensure_ascii=False))


def main():
    """Run all prototype tests."""
    print("🚀 NS 8360/NS 3940 Standards Integration Prototype")
    print("=" * 60)
    print("Testing core components for Norwegian building standards integration")
    
    try:
        test_ns8360_parsing()
        test_ns3940_classification()
        test_enhanced_identification_mapping()
        generate_sample_json_output()
        
        print("\n\n✅ All prototype tests completed successfully!")
        print("\n📋 Summary of Capabilities Demonstrated:")
        print("   🔍 NS 8360 compliant name parsing with fallback inference")
        print("   🏷️ NS 3940 room classification with performance defaults")
        print("   🗺️ Enhanced identification mapping with Norwegian standards")
        print("   📄 Structured JSON output with enriched metadata")
        print("   💡 Automatic performance requirements per room type")
        print("   🔧 Equipment inference based on room function")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
