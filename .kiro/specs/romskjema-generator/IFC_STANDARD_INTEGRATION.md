# IFC Standard Integration - room_scheduel_req.json

## Oversikt

`room_scheduel_req.json` definerer en norsk standard for IFC Space strukturering som må integreres i romskjema generator-implementeringen. Denne standarden komplementerer den omfattende `room_scheduel_input_template.json` ved å standardisere input-siden.

---

## NS 8360 Navngivningsstandard

### Strukturert Naming Pattern
```
Primary: SPC-{storey}-{zone}-{func}-{seq}
No Zone: SPC-{storey}-{func}-{seq}

Eksempler:
- "SPC-02-A101-111-003" (Stue, etasje 2, leilighet A101)
- "SPC-01-A101-130-001" (Bad, etasje 1, leilighet A101)
```

### Implementering i Romskjema Generator

#### 1. Room Name Parser
```python
# ifc_room_schedule/parsers/ns8360_name_parser.py
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class NS8360ParsedName:
    prefix: str  # "SPC"
    storey: str  # "02", "01", "U1"
    zone: Optional[str]  # "A101", None
    function_code: str  # "111", "130"
    sequence: str  # "003", "001"
    is_valid: bool
    raw_name: str

class NS8360NameParser:
    """Parser for NS 8360 compliant IFC Space names"""
    
    # Regex patterns from standard
    PATTERN_WITH_ZONE = re.compile(r'^SPC-([A-Z0-9]{1,3})-([A-Z0-9]{1,6})-(\d{3})-(\d{3})$')
    PATTERN_NO_ZONE = re.compile(r'^SPC-([A-Z0-9]{1,3})-(\d{3})-(\d{3})$')
    
    def parse(self, space_name: str) -> NS8360ParsedName:
        """Parse NS 8360 compliant space name"""
        # Try pattern with zone first
        match = self.PATTERN_WITH_ZONE.match(space_name)
        if match:
            return NS8360ParsedName(
                prefix="SPC",
                storey=match.group(1),
                zone=match.group(2),
                function_code=match.group(3),
                sequence=match.group(4),
                is_valid=True,
                raw_name=space_name
            )
        
        # Try pattern without zone
        match = self.PATTERN_NO_ZONE.match(space_name)
        if match:
            return NS8360ParsedName(
                prefix="SPC",
                storey=match.group(1),
                zone=None,
                function_code=match.group(2),
                sequence=match.group(3),
                is_valid=True,
                raw_name=space_name
            )
        
        # Invalid pattern - create fallback
        return NS8360ParsedName(
            prefix="",
            storey="",
            zone=None,
            function_code="",
            sequence="",
            is_valid=False,
            raw_name=space_name
        )
    
    def validate(self, space_name: str) -> bool:
        """Validate if space name follows NS 8360"""
        return self.parse(space_name).is_valid
```

#### 2. NS 3940 Classification Mapper
```python
# ifc_room_schedule/mappers/ns3940_classifier.py
from typing import Dict, Optional

class NS3940Classifier:
    """Maps NS 3940 function codes to room types and properties"""
    
    # NS 3940 function codes from standard
    FUNCTION_CODES = {
        "111": {
            "label": "Oppholdsrom",
            "category": "Bolig",
            "occupancy_type": "Opphold",
            "is_wet_room": False,
            "typical_equipment": ["TV-punkt", "Stikkontakter"],
            "performance_defaults": {
                "lighting": {"task_lux": 200},
                "acoustics": {"class_ns8175": "C"},
                "ventilation": {"airflow_supply_m3h": 7.2}  # Per m2
            }
        },
        "130": {
            "label": "Våtrom",
            "category": "Bolig", 
            "occupancy_type": "Våtrom",
            "is_wet_room": True,
            "typical_equipment": ["Dusjarmatur", "WC", "Ventilator"],
            "performance_defaults": {
                "lighting": {"task_lux": 200, "emergency_lighting": True},
                "ventilation": {"airflow_extract_m3h": 54},
                "thermal": {"setpoint_heating_C": 22}
            }
        },
        "131": {
            "label": "WC",
            "category": "Bolig",
            "occupancy_type": "Våtrom", 
            "is_wet_room": True,
            "typical_equipment": ["WC", "Ventilator"],
            "performance_defaults": {
                "lighting": {"task_lux": 150},
                "ventilation": {"airflow_extract_m3h": 36}
            }
        },
        "132": {
            "label": "Baderom",
            "category": "Bolig",
            "occupancy_type": "Våtrom",
            "is_wet_room": True,
            "typical_equipment": ["Badekar", "Dusjarmatur", "Ventilator"],
            "performance_defaults": {
                "lighting": {"task_lux": 200},
                "ventilation": {"airflow_extract_m3h": 54},
                "thermal": {"setpoint_heating_C": 24}
            }
        }
    }
    
    def classify_from_code(self, function_code: str) -> Optional[Dict]:
        """Get classification data from NS 3940 function code"""
        return self.FUNCTION_CODES.get(function_code)
    
    def infer_code_from_name(self, room_name: str) -> Optional[str]:
        """Infer NS 3940 code from room name (fallback)"""
        name_lower = room_name.lower()
        
        # Norwegian room name patterns
        if any(word in name_lower for word in ['stue', 'opphold', 'living']):
            return "111"
        elif any(word in name_lower for word in ['bad', 'våtrom']):
            return "130"  
        elif any(word in name_lower for word in ['wc', 'toalett']):
            return "131"
        elif any(word in name_lower for word in ['baderom', 'bath']):
            return "132"
        
        return None
```

#### 3. Enhanced Identification Mapper
```python
# ifc_room_schedule/mappers/enhanced_identification_mapper.py
from ..parsers.ns8360_name_parser import NS8360NameParser, NS8360ParsedName
from ..mappers.ns3940_classifier import NS3940Classifier

class EnhancedIdentificationMapper:
    """Enhanced identification mapper using NS 8360 and NS 3940 standards"""
    
    def __init__(self):
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def map_identification(self, space: SpaceData) -> 'IdentificationData':
        """Map space to identification section using Norwegian standards"""
        
        # Parse NS 8360 compliant name
        parsed_name = self.name_parser.parse(space.name)
        
        # Get NS 3940 classification
        classification = None
        if parsed_name.is_valid:
            classification = self.classifier.classify_from_code(parsed_name.function_code)
        else:
            # Fallback: infer from name
            inferred_code = self.classifier.infer_code_from_name(space.name)
            if inferred_code:
                classification = self.classifier.classify_from_code(inferred_code)
        
        return IdentificationData(
            project_id=self._extract_project_id(space),
            project_name=self._extract_project_name(space),
            building_id=self._extract_building_id(space),
            building_name=self._extract_building_name(space),
            storey_name=parsed_name.storey if parsed_name.is_valid else self._fallback_storey(space),
            storey_elevation_m=space.elevation,
            room_number=f"{parsed_name.sequence}" if parsed_name.is_valid else space.number,
            room_name=space.long_name or self._generate_readable_name(space, classification),
            function=classification.get("label") if classification else None,
            occupancy_type=classification.get("occupancy_type") if classification else None
        )
    
    def _generate_readable_name(self, space: SpaceData, classification: Dict) -> str:
        """Generate human-readable room name"""
        if classification:
            return f"{classification['label']} | {space.name}"
        return space.long_name or space.name
```

---

## Validation Rules Integration

### 1. NS 8360 Name Validation
```python
# ifc_room_schedule/validation/ns8360_validator.py
class NS8360Validator:
    """Validator for NS 8360 naming compliance"""
    
    def validate_space_name(self, space: SpaceData) -> ValidationResult:
        """Validate space name against NS 8360 patterns"""
        parser = NS8360NameParser()
        parsed = parser.parse(space.name)
        
        if not parsed.is_valid:
            return ValidationResult(
                valid=False,
                rule_id="R-NS8360-Name-Pattern",
                message="IfcSpace.Name oppfyller ikke NS 8360-mønsteret.",
                suggestion=f"Forventet format: SPC-{{etasje}}-{{sone}}-{{funksjon}}-{{nr}} (f.eks. SPC-02-A101-111-003)"
            )
        
        return ValidationResult(valid=True)
```

### 2. NS 3940 Classification Validation  
```python
# ifc_room_schedule/validation/ns3940_validator.py
class NS3940Validator:
    """Validator for NS 3940 classification compliance"""
    
    def validate_classification_consistency(self, space: SpaceData, room_data: Dict) -> ValidationResult:
        """Validate consistency between name and classification"""
        parser = NS8360NameParser()
        parsed = parser.parse(space.name)
        
        if parsed.is_valid:
            name_function_code = parsed.function_code
            classification_code = room_data.get('classification', {}).get('ns3940', {}).get('code')
            
            if classification_code and name_function_code != classification_code:
                return ValidationResult(
                    valid=False,
                    rule_id="R-NS3940-Name-Consistency", 
                    message="IfcSpace.Name og NS 3940-koden er inkonsistente.",
                    current_value=f"Navn: {name_function_code}, Klassifisering: {classification_code}",
                    suggestion="Oppdater enten navn eller klassifisering for konsistens"
                )
        
        return ValidationResult(valid=True)
    
    def validate_wet_room_consistency(self, space: SpaceData, room_data: Dict) -> ValidationResult:
        """Validate wet room classification consistency"""
        classification_code = room_data.get('classification', {}).get('ns3940', {}).get('code')
        is_wet_room = room_data.get('performance_requirements', {}).get('water_sanitary', {}).get('drainage_required', False)
        
        wet_room_codes = ['130', '131', '132']  # Våtrom, WC, Baderom
        
        if classification_code in wet_room_codes and not is_wet_room:
            return ValidationResult(
                valid=False,
                rule_id="R-WetRoom-Consistency",
                message="Våtromskonsistens: NS 3940-kode indikerer våtrom, men drainage_required er ikke true.",
                suggestion="Aktiver drainage_required for våtrom"
            )
        
        return ValidationResult(valid=True)
```

---

## Integration med Eksisterende Planverk

### Fase 1 Utvidelser (Uke 1-2)
**Utvid 1.1 Meta og Identification Mapping:**

- [ ] **1.1.4 Implementer NS 8360 Name Parser**
  - Opprett `NS8360NameParser` klasse
  - Implementer regex-basert parsing av romnavn
  - Lag fallback for ikke-konforme navn
  - **Testing**: Unit tests med eksempel-navn fra standard
  - _Requirements: 1.1, 5.1_

- [ ] **1.1.5 Implementer NS 3940 Classifier**
  - Opprett `NS3940Classifier` med funksjonskoder
  - Implementer intelligent inference fra romnavn
  - Koble til performance requirements defaults
  - **Testing**: Classification accuracy testing
  - _Requirements: 2.1, 2.2_

- [ ] **1.1.6 Integrer standarder i Enhanced Identification Mapper**
  - Oppdater `EnhancedIdentificationMapper` til å bruke NS-standarder
  - Implementer automatisk readable name generation
  - Lag structured identification basert på parsed name
  - **Testing**: Integration tests med AkkordSvingen-filen
  - _Requirements: 1.2, 5.2_

### Validation Integration (Fase 1, Uke 4)
**Utvid 6.2 Build validation reporting:**

- [ ] **6.2.3 NS 8360/3940 Validation**
  - Implementer `NS8360Validator` og `NS3940Validator`
  - Integrer med existing validation system
  - Lag detailed error messages med suggestions
  - **Standards**: Compliance med NS 8360 og NS 3940
  - _Requirements: 4.1, 4.2_

---

## Forbedringer til Template Integration

### Enhanced Classification Section
```json
{
  "classification": {
    "ns3940": {
      "code": "111",
      "label": "Oppholdsrom",
      "category": "Bolig",
      "confidence": 0.95,
      "source": "parsed_from_name"
    },
    "ns8360_compliance": {
      "name_pattern_valid": true,
      "parsed_components": {
        "storey": "02",
        "zone": "A101", 
        "function_code": "111",
        "sequence": "003"
      }
    },
    "tfm": null,
    "custom_codes": []
  }
}
```

### Enhanced IFC Section
```json
{
  "ifc": {
    "space_global_id": "GUID-STUE",
    "space_long_name": "Stue | 02/A101 | NS3940:111",
    "space_number": "003",
    "ns8360_compliant": true,
    "parsed_name_components": {
      "storey": "02",
      "zone": "A101",
      "function_code": "111", 
      "sequence": "003"
    },
    "site_guid": null,
    "building_guid": null,
    "storey_guid": null,
    "model_source": {
      "file_name": null,
      "file_version": "IFC4",
      "discipline": "ARK"
    }
  }
}
```

---

## Performance Defaults Integration

### Room Type Specific Defaults
```python
# ifc_room_schedule/defaults/ns3940_defaults.py
NS3940_PERFORMANCE_DEFAULTS = {
    "111": {  # Oppholdsrom
        "performance_requirements": {
            "lighting": {"task_lux": 200, "color_rendering_CRI": 80},
            "acoustics": {"class_ns8175": "C", "background_noise_dB": 35},
            "ventilation": {"airflow_supply_m3h": 7.2},  # Per m2
            "thermal": {"setpoint_heating_C": 20, "setpoint_cooling_C": 26}
        },
        "fixtures_and_equipment": [
            {"discipline": "RIE", "type": "Stikkontakt", "count": 6},
            {"discipline": "RIE", "type": "TV-punkt", "count": 1},
            {"discipline": "RIE", "type": "Lysbryter", "count": 2}
        ]
    },
    "130": {  # Våtrom
        "performance_requirements": {
            "lighting": {"task_lux": 200, "emergency_lighting": True},
            "ventilation": {"airflow_extract_m3h": 54},
            "thermal": {"setpoint_heating_C": 22},
            "water_sanitary": {"hot_cold_water": True, "drainage_required": True}
        },
        "finishes": {
            "floor": {"slip_resistance_class": "R10"},
            "walls": [{"impact_resistance": "Høy", "finish": "Fliser"}]
        },
        "hse_and_accessibility": {
            "universal_design": True,
            "slip_resistance_class": "R10"
        }
    }
}
```

---

## Testing Integration

### Standard Compliance Tests
```python
# tests/standards/test_ns8360_ns3940_integration.py
class TestNorwegianStandardsIntegration:
    
    def test_ns8360_name_parsing(self):
        """Test NS 8360 name parsing with standard examples"""
        parser = NS8360NameParser()
        
        # Test valid patterns
        parsed = parser.parse("SPC-02-A101-111-003")
        assert parsed.is_valid
        assert parsed.storey == "02"
        assert parsed.zone == "A101"
        assert parsed.function_code == "111"
        assert parsed.sequence == "003"
    
    def test_ns3940_classification_mapping(self):
        """Test NS 3940 classification mapping"""
        classifier = NS3940Classifier()
        
        classification = classifier.classify_from_code("111")
        assert classification["label"] == "Oppholdsrom"
        assert classification["is_wet_room"] == False
        
        classification = classifier.classify_from_code("130") 
        assert classification["label"] == "Våtrom"
        assert classification["is_wet_room"] == True
    
    def test_room_schedule_integration(self):
        """Test complete integration with room schedule template"""
        space = create_mock_space(
            name="SPC-02-A101-111-003",
            long_name="Stue | 02/A101 | NS3940:111"
        )
        
        mapper = EnhancedIdentificationMapper()
        identification = mapper.map_identification(space)
        
        assert identification.room_number == "003"
        assert identification.function == "Oppholdsrom"
        assert identification.occupancy_type == "Opphold"
```

---

## Implementeringsprioritet

### Høy Prioritet (Fase 1, Uke 1-2)
1. **NS8360NameParser** - Kritisk for structured data extraction
2. **NS3940Classifier** - Nødvendig for intelligent defaults
3. **Enhanced IdentificationMapper** - Kobler alt sammen

### Middels Prioritet (Fase 1, Uke 3-4)  
1. **Validation integration** - Sikrer data quality
2. **Performance defaults** - Automatisk population av technical requirements
3. **Template enhancements** - Structured classification og IFC sections

### Lav Prioritet (Fase 2)
1. **Extended NS 3940 codes** - Flere romtyper
2. **Advanced name inference** - Machine learning for edge cases
3. **Multi-language support** - English fallbacks

---

## Konklusjon

`room_scheduel_req.json` er en **game-changer** for romskjema generator-prosjektet fordi den:

1. **Standardiserer input-siden** med NS 8360 og NS 3940
2. **Enabler intelligent parsing** av eksisterende IFC-data
3. **Gir structured fallback-strategier** basert på norske standarder
4. **Reduserer manual configuration** gjennom automatic classification

Integreringen av denne standarden vil gjøre romskjema generator-en betydelig mer robust og brukervennlig for norske byggeprosjekter.
