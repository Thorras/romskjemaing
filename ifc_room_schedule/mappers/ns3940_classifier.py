"""
NS 3940 Classifier

Maps NS 3940 function codes to room types and properties following Norwegian building standards.
"""

from typing import Dict, Optional, List, Any
from dataclasses import dataclass


@dataclass
class RoomClassification:
    """Classification result for a room based on NS 3940."""
    
    function_code: str
    label: str
    category: str
    occupancy_type: str
    is_wet_room: bool
    typical_equipment: List[str]
    performance_defaults: Dict[str, Any]
    accessibility_requirements: Dict[str, Any]
    confidence: float = 1.0


class NS3940Classifier:
    """Maps NS 3940 function codes to room types and properties."""
    
    # NS 3940 function codes with comprehensive Norwegian building data
    FUNCTION_CODES = {
        "111": {
            "label": "Oppholdsrom",
            "category": "Bolig",
            "occupancy_type": "Opphold",
            "is_wet_room": False,
            "typical_equipment": [
                {"discipline": "RIE", "type": "Stikkontakt", "count": 6},
                {"discipline": "RIE", "type": "TV-punkt", "count": 1},
                {"discipline": "RIE", "type": "Lysbryter", "count": 2},
                {"discipline": "RIE", "type": "Taklampe", "count": 1}
            ],
            "performance_defaults": {
                "lighting": {
                    "task_lux": 200,
                    "color_rendering_CRI": 80,
                    "emergency_lighting": False,
                    "UGR_max": 22
                },
                "acoustics": {
                    "class_ns8175": "C",
                    "rw_dB": 52,
                    "background_noise_dB": 35
                },
                "ventilation": {
                    "airflow_supply_m3h": 7.2,  # Per m2
                    "co2_setpoint_ppm": 1000
                },
                "thermal": {
                    "setpoint_heating_C": 20,
                    "setpoint_cooling_C": 26
                }
            },
            "accessibility_requirements": {
                "universal_design": True,
                "turning_radius_m": 1.5,
                "clear_width_door_mm": 850
            }
        },
        "121": {
            "label": "Soverom",
            "category": "Bolig",
            "occupancy_type": "Opphold",
            "is_wet_room": False,
            "typical_equipment": [
                {"discipline": "RIE", "type": "Stikkontakt", "count": 4},
                {"discipline": "RIE", "type": "Lysbryter", "count": 2},
                {"discipline": "RIE", "type": "Taklampe", "count": 1}
            ],
            "performance_defaults": {
                "lighting": {
                    "task_lux": 150,
                    "color_rendering_CRI": 80,
                    "emergency_lighting": False
                },
                "acoustics": {
                    "class_ns8175": "B",  # Higher requirement for bedrooms
                    "rw_dB": 55,
                    "background_noise_dB": 30
                },
                "ventilation": {
                    "airflow_supply_m3h": 5.4,  # Per m2, lower for bedrooms
                    "co2_setpoint_ppm": 1000
                },
                "thermal": {
                    "setpoint_heating_C": 18,  # Cooler for sleeping
                    "setpoint_cooling_C": 24
                }
            },
            "accessibility_requirements": {
                "universal_design": True,
                "clear_width_door_mm": 850
            }
        },
        "130": {
            "label": "Våtrom",
            "category": "Bolig",
            "occupancy_type": "Våtrom",
            "is_wet_room": True,
            "typical_equipment": [
                {"discipline": "RIV", "type": "Dusjarmatur", "count": 1},
                {"discipline": "RIV", "type": "WC", "count": 1},
                {"discipline": "RIV", "type": "Servant", "count": 1},
                {"discipline": "RIA", "type": "Ventilator", "count": 1},
                {"discipline": "RIE", "type": "Stikkontakt", "count": 2},
                {"discipline": "RIE", "type": "Lysbryter", "count": 1}
            ],
            "performance_defaults": {
                "lighting": {
                    "task_lux": 200,
                    "emergency_lighting": True,
                    "color_rendering_CRI": 90,  # Higher for grooming tasks
                    "UGR_max": 22
                },
                "acoustics": {
                    "class_ns8175": "C",
                    "background_noise_dB": 40  # Higher tolerance due to ventilation
                },
                "ventilation": {
                    "airflow_extract_m3h": 54,  # TEK17 requirement
                    "pressure_room_Pa": -5  # Negative pressure
                },
                "thermal": {
                    "setpoint_heating_C": 22,  # Warmer for comfort
                    "u_values": {
                        "floor_W_m2K": 0.15  # Heated floors common
                    }
                },
                "water_sanitary": {
                    "hot_cold_water": True,
                    "drainage_required": True,
                    "fixtures": ["shower", "wc", "sink"]
                }
            },
            "accessibility_requirements": {
                "universal_design": True,
                "turning_radius_m": 1.5,
                "clear_width_door_mm": 850,
                "slip_resistance_class": "R10"
            }
        },
        "131": {
            "label": "WC",
            "category": "Bolig",
            "occupancy_type": "Våtrom",
            "is_wet_room": True,
            "typical_equipment": [
                {"discipline": "RIV", "type": "WC", "count": 1},
                {"discipline": "RIV", "type": "Servant", "count": 1},
                {"discipline": "RIA", "type": "Ventilator", "count": 1},
                {"discipline": "RIE", "type": "Stikkontakt", "count": 1},
                {"discipline": "RIE", "type": "Lysbryter", "count": 1}
            ],
            "performance_defaults": {
                "lighting": {
                    "task_lux": 150,
                    "emergency_lighting": False,
                    "color_rendering_CRI": 80
                },
                "ventilation": {
                    "airflow_extract_m3h": 36,  # TEK17 requirement for WC
                    "pressure_room_Pa": -5
                },
                "thermal": {
                    "setpoint_heating_C": 20
                },
                "water_sanitary": {
                    "hot_cold_water": False,  # Often only cold water
                    "drainage_required": True,
                    "fixtures": ["wc", "sink"]
                }
            },
            "accessibility_requirements": {
                "universal_design": True,
                "turning_radius_m": 1.5,
                "clear_width_door_mm": 850
            }
        },
        "132": {
            "label": "Baderom",
            "category": "Bolig",
            "occupancy_type": "Våtrom",
            "is_wet_room": True,
            "typical_equipment": [
                {"discipline": "RIV", "type": "Badekar", "count": 1},
                {"discipline": "RIV", "type": "Dusjarmatur", "count": 1},
                {"discipline": "RIV", "type": "Servant", "count": 1},
                {"discipline": "RIA", "type": "Ventilator", "count": 1},
                {"discipline": "RIE", "type": "Stikkontakt", "count": 3},
                {"discipline": "RIE", "type": "Lysbryter", "count": 2}
            ],
            "performance_defaults": {
                "lighting": {
                    "task_lux": 200,
                    "emergency_lighting": True,
                    "color_rendering_CRI": 90
                },
                "ventilation": {
                    "airflow_extract_m3h": 54,
                    "pressure_room_Pa": -5
                },
                "thermal": {
                    "setpoint_heating_C": 24,  # Warmer for bathing
                    "u_values": {
                        "floor_W_m2K": 0.15
                    }
                },
                "water_sanitary": {
                    "hot_cold_water": True,
                    "drainage_required": True,
                    "fixtures": ["bathtub", "shower", "sink"]
                }
            },
            "accessibility_requirements": {
                "universal_design": True,
                "turning_radius_m": 1.5,
                "clear_width_door_mm": 850,
                "slip_resistance_class": "R10"
            }
        },
        "140": {
            "label": "Kjøkken",
            "category": "Bolig",
            "occupancy_type": "Opphold",
            "is_wet_room": False,
            "typical_equipment": [
                {"discipline": "RIV", "type": "Kjøkkenvask", "count": 1},
                {"discipline": "RIV", "type": "Oppvaskmaskin tilkobling", "count": 1},
                {"discipline": "RIE", "type": "Stikkontakt", "count": 8},
                {"discipline": "RIE", "type": "Komfyr tilkobling", "count": 1},
                {"discipline": "RIA", "type": "Avtrekksvifte", "count": 1}
            ],
            "performance_defaults": {
                "lighting": {
                    "task_lux": 500,  # High for food preparation
                    "color_rendering_CRI": 90,
                    "UGR_max": 22
                },
                "acoustics": {
                    "class_ns8175": "C",
                    "background_noise_dB": 40
                },
                "ventilation": {
                    "airflow_extract_m3h": 108,  # Higher for cooking
                    "airflow_supply_m3h": 7.2
                },
                "water_sanitary": {
                    "hot_cold_water": True,
                    "drainage_required": True,
                    "fixtures": ["sink"]
                }
            },
            "accessibility_requirements": {
                "universal_design": True,
                "clear_width_door_mm": 850
            }
        }
    }
    
    # Norwegian room name patterns for inference
    NORWEGIAN_INFERENCE_PATTERNS = {
        'stue': '111',
        'opphold': '111',
        'living': '111',
        'soverom': '121',
        'bedroom': '121',
        'bad': '130',
        'våtrom': '130',
        'wc': '131',
        'toalett': '131',
        'baderom': '132',
        'bath': '132',
        'kjøkken': '140',
        'kitchen': '140',
    }
    
    def classify_from_code(self, function_code: str) -> Optional[RoomClassification]:
        """
        Get classification data from NS 3940 function code.
        
        Args:
            function_code: NS 3940 function code (e.g., "111", "130")
            
        Returns:
            RoomClassification if code exists, None otherwise
        """
        if function_code not in self.FUNCTION_CODES:
            return None
        
        data = self.FUNCTION_CODES[function_code]
        
        return RoomClassification(
            function_code=function_code,
            label=data["label"],
            category=data["category"],
            occupancy_type=data["occupancy_type"],
            is_wet_room=data["is_wet_room"],
            typical_equipment=data["typical_equipment"],
            performance_defaults=data["performance_defaults"],
            accessibility_requirements=data["accessibility_requirements"],
            confidence=1.0
        )
    
    def infer_code_from_name(self, room_name: str) -> Optional[str]:
        """
        Infer NS 3940 code from room name using Norwegian patterns.
        
        Args:
            room_name: Room name to analyze
            
        Returns:
            Function code if inference successful, None otherwise
        """
        if not room_name:
            return None
        
        name_lower = room_name.lower()
        
        # Look for exact matches first
        for pattern, code in self.NORWEGIAN_INFERENCE_PATTERNS.items():
            if pattern in name_lower:
                return code
        
        return None
    
    def classify_from_name(self, room_name: str) -> Optional[RoomClassification]:
        """
        Classify room directly from name using inference.
        
        Args:
            room_name: Room name to classify
            
        Returns:
            RoomClassification if inference successful, None otherwise
        """
        inferred_code = self.infer_code_from_name(room_name)
        if inferred_code:
            classification = self.classify_from_code(inferred_code)
            if classification:
                # Reduce confidence for inferred classifications
                classification.confidence = 0.8
                return classification
        
        return None
    
    def get_all_function_codes(self) -> List[str]:
        """Get all supported NS 3940 function codes."""
        return list(self.FUNCTION_CODES.keys())
    
    def get_wet_room_codes(self) -> List[str]:
        """Get all function codes that represent wet rooms."""
        return [code for code, data in self.FUNCTION_CODES.items() if data["is_wet_room"]]
    
    def is_wet_room(self, function_code: str) -> bool:
        """Check if function code represents a wet room."""
        return function_code in self.get_wet_room_codes()
    
    def classify_space(self, space_name: str, long_name: str = None) -> Optional[RoomClassification]:
        """
        Classify space using both name and long name for better accuracy.
        
        Args:
            space_name: Primary space name
            long_name: Optional long name for additional context
            
        Returns:
            RoomClassification if classification successful, None otherwise
        """
        # Try primary name first
        classification = self.classify_from_name(space_name)
        if classification:
            return classification
        
        # Try long name if available
        if long_name:
            classification = self.classify_from_name(long_name)
            if classification:
                # Slightly lower confidence for long name inference
                classification.confidence *= 0.9
                return classification
        
        return None


# Example usage and testing
if __name__ == "__main__":
    classifier = NS3940Classifier()
    
    # Test function code classification
    print("NS 3940 Classifier Test Results:")
    print("=" * 50)
    
    test_codes = ["111", "130", "131", "132", "140"]
    
    for code in test_codes:
        classification = classifier.classify_from_code(code)
        if classification:
            print(f"\nFunction Code: {code}")
            print(f"Label: {classification.label}")
            print(f"Category: {classification.category}")
            print(f"Wet Room: {classification.is_wet_room}")
            print(f"Equipment Count: {len(classification.typical_equipment)}")
            print(f"Lighting Task Lux: {classification.performance_defaults.get('lighting', {}).get('task_lux', 'N/A')}")
    
    # Test name inference
    print("\n" + "=" * 50)
    print("Name Inference Test:")
    
    test_names = ["Stue", "Bad", "Kjøkken", "Soverom", "WC"]
    
    for name in test_names:
        classification = classifier.classify_from_name(name)
        if classification:
            print(f"\nRoom Name: '{name}'")
            print(f"Inferred Code: {classification.function_code}")
            print(f"Label: {classification.label}")
            print(f"Confidence: {classification.confidence}")
