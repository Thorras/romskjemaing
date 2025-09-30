#!/usr/bin/env python3
"""
Demo: Comprehensive Room Schedule Export

Demonstrates the new comprehensive room schedule functionality
that matches the JSON template structure.
"""

import json
from pathlib import Path

from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.export.comprehensive_json_builder import ComprehensiveJsonBuilder


def create_demo_spaces():
    """Create demo space data."""
    spaces = [
        SpaceData(
            guid="demo-space-001",
            name="SPC-02-A101-111-003",
            long_name="Stue | 02/A101 | NS3940:111",
            description="Hovedoppholdsrom i leilighet A101",
            object_type="IfcSpace",
            zone_category="A101",
            number="003",
            elevation=0.0,
            quantities={
                "NetArea": 25.5,
                "GrossArea": 27.0,
                "Height": 2.4,
                "Perimeter": 20.0,
                "Volume": 61.2
            }
        ),
        SpaceData(
            guid="demo-space-002",
            name="SPC-02-A101-130-001",
            long_name="Bad | 02/A101 | NS3940:130",
            description="Hovedbad med dusj og WC",
            object_type="IfcSpace",
            zone_category="A101",
            number="001",
            elevation=0.0,
            quantities={
                "NetArea": 5.2,
                "GrossArea": 5.8,
                "Height": 2.4,
                "Perimeter": 9.4,
                "Volume": 12.5
            }
        ),
        SpaceData(
            guid="demo-space-003",
            name="SPC-02-A101-140-002",
            long_name="Kjøkken | 02/A101 | NS3940:140",
            description="Kjøkken med øy",
            object_type="IfcSpace",
            zone_category="A101",
            number="002",
            elevation=0.0,
            quantities={
                "NetArea": 12.8,
                "GrossArea": 13.5,
                "Height": 2.4,
                "Perimeter": 15.2,
                "Volume": 30.7
            }
        )
    ]
    return spaces


def create_demo_project_info():
    """Create demo project information."""
    return {
        "project_id": "PRJ-2024-DEMO",
        "project_name": "Demo Boligprosjekt",
        "building_id": "BLD-A",
        "building_name": "Blokk A - Sentrum",
        "phase": "Detaljprosjektering",
        "state": "Utkast",
        "created_by": "Demo Bruker"
    }


def create_demo_user_data():
    """Create demo user data for spaces."""
    return {
        "demo-space-001": {  # Stue
            "performance_requirements": {
                "fire": {
                    "fire_class": "Standard",
                    "door_rating": "EI30"
                },
                "acoustics": {
                    "class_ns8175": "B",
                    "rw_dB": 45.0,
                    "background_noise_dB": 35.0
                },
                "thermal": {
                    "setpoint_heating_C": 21.0,
                    "setpoint_cooling_C": 26.0
                },
                "lighting": {
                    "task_lux": 200,
                    "emergency_lighting": False,
                    "color_rendering_CRI": 80
                },
                "power_data": {
                    "sockets_count": 6,
                    "data_outlets_count": 2,
                    "cleaning_socket": False
                }
            },
            "finishes": {
                "floor": {
                    "system": "Parkett",
                    "layers": [
                        {
                            "product": "Eik parkett 3-stav",
                            "thickness_mm": 14,
                            "supplier": "Tarkett",
                            "color_code": "Naturell"
                        }
                    ]
                },
                "ceiling": {
                    "system": "Malt gips",
                    "height_m": 2.4,
                    "acoustic_class": "C"
                },
                "walls": [
                    {
                        "name": "Alle vegger",
                        "system": "Malt gips",
                        "finish": "Matt maling",
                        "color_code": "RAL 9010"
                    }
                ]
            },
            "notes": "Hovedoppholdsrom med god dagslysstilgang"
        },
        "demo-space-002": {  # Bad
            "performance_requirements": {
                "fire": {
                    "fire_class": "Standard",
                    "door_rating": "EI30"
                },
                "acoustics": {
                    "class_ns8175": "C",
                    "rw_dB": 40.0
                },
                "ventilation": {
                    "airflow_extract_m3h": 108.0,  # 30 l/s
                    "pressure_room_Pa": -5.0
                },
                "lighting": {
                    "task_lux": 300,
                    "emergency_lighting": False
                },
                "water_sanitary": {
                    "fixtures": ["Dusjbatteri", "Servant", "WC"],
                    "hot_cold_water": True,
                    "drainage_required": True
                }
            },
            "finishes": {
                "floor": {
                    "system": "Keramiske fliser",
                    "layers": [
                        {
                            "product": "Porselensfliser 30x60",
                            "thickness_mm": 10,
                            "supplier": "Marazzi",
                            "color_code": "Grå"
                        }
                    ]
                },
                "walls": [
                    {
                        "name": "Dusjsone",
                        "system": "Keramiske fliser",
                        "finish": "Porselensfliser 30x60",
                        "color_code": "Grå"
                    },
                    {
                        "name": "Øvrige vegger",
                        "system": "Malt gips",
                        "finish": "Fuktsikker maling",
                        "color_code": "RAL 9010"
                    }
                ]
            },
            "hse_and_accessibility": {
                "universal_design": True,
                "slip_resistance_class": "R10"
            },
            "notes": "Våtrom med dusjnisje og god ventilasjon"
        },
        "demo-space-003": {  # Kjøkken
            "performance_requirements": {
                "fire": {
                    "fire_class": "Forhøyet",
                    "door_rating": "EI30"
                },
                "ventilation": {
                    "airflow_extract_m3h": 144.0,  # 40 l/s
                    "airflow_supply_m3h": 108.0   # 30 l/s
                },
                "lighting": {
                    "task_lux": 500,
                    "emergency_lighting": False,
                    "color_rendering_CRI": 90
                },
                "power_data": {
                    "sockets_count": 8,
                    "data_outlets_count": 1,
                    "cleaning_socket": True,
                    "circuits": ["Komfyr", "Oppvaskmaskin", "Kjøleskap"]
                },
                "water_sanitary": {
                    "fixtures": ["Kjøkkenvask", "Oppvaskmaskin tilkobling"],
                    "hot_cold_water": True,
                    "drainage_required": True
                }
            },
            "fixtures_and_equipment": [
                {
                    "discipline": "ARK",
                    "type": "Kjøkkeninnredning",
                    "description": "Komplett kjøkken med øy",
                    "supplier": "IKEA",
                    "product_code": "METOD"
                },
                {
                    "discipline": "RIE",
                    "type": "Komfyr",
                    "description": "Induksjonstopp med stekeovn",
                    "connections": {"power": "400V 16A"}
                }
            ],
            "notes": "Moderne kjøkken med kjøkkenøy og god arbeidsflyt"
        }
    }


def main():
    """Run the comprehensive export demo."""
    print("🏗️  Comprehensive Room Schedule Export Demo")
    print("=" * 50)
    
    # Create demo data
    print("📋 Creating demo data...")
    spaces = create_demo_spaces()
    project_info = create_demo_project_info()
    user_data = create_demo_user_data()
    
    print(f"   - Created {len(spaces)} demo spaces")
    print(f"   - Project: {project_info['project_name']}")
    print(f"   - User data for {len(user_data)} spaces")
    
    # Initialize comprehensive JSON builder
    print("\n🔧 Initializing comprehensive JSON builder...")
    builder = ComprehensiveJsonBuilder()
    builder.set_source_file("demo_building.ifc")
    builder.set_ifc_version("IFC4")
    
    # Create output directory
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    # Export comprehensive JSON
    print("\n📤 Exporting comprehensive JSON...")
    json_file = output_dir / "demo_comprehensive_room_schedule.json"
    
    success = builder.write_comprehensive_json_file(
        str(json_file),
        spaces,
        project_info,
        user_data
    )
    
    if success:
        print(f"   ✅ Successfully exported to: {json_file}")
        
        # Show file size
        file_size = json_file.stat().st_size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        print(f"   📊 File size: {size_str}")
        
        # Show structure preview
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n📋 Export contains {len(data)} rooms:")
        for i, room_data in enumerate(data, 1):
            room_name = room_data.get('identification', {}).get('room_name', 'Unknown')
            area = room_data.get('geometry', {}).get('area_nett_m2', 0)
            print(f"   {i}. {room_name} ({area} m²)")
    else:
        print("   ❌ Export failed")
        return
    
    # Create user input templates
    print("\n📝 Creating user input templates...")
    templates_dir = output_dir / "user_input_templates"
    
    created_templates = builder.create_user_input_templates(spaces, str(templates_dir))
    
    if created_templates:
        print(f"   ✅ Created {len(created_templates)} user input templates:")
        for template_file in created_templates:
            template_path = Path(template_file)
            print(f"      - {template_path.name}")
    else:
        print("   ❌ Failed to create templates")
    
    # Validate exported data
    print("\n🔍 Validating exported data...")
    with open(json_file, 'r', encoding='utf-8') as f:
        exported_data = json.load(f)
    
    is_valid, errors = builder.validate_comprehensive_data(exported_data)
    
    if is_valid:
        print("   ✅ Data validation passed")
    else:
        print(f"   ⚠️  Data validation found {len(errors)} issues:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"      - {error}")
        if len(errors) > 5:
            print(f"      ... and {len(errors) - 5} more")
    
    print(f"\n🎉 Demo completed! Check the output in: {output_dir}")
    print("\n💡 Next steps:")
    print("   1. Review the comprehensive JSON structure")
    print("   2. Fill out user input templates with additional data")
    print("   3. Re-export with updated user data")
    print("   4. Use the GUI for interactive export configuration")


if __name__ == "__main__":
    main()