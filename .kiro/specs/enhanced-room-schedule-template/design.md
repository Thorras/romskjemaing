# Enhanced Room Schedule Template Design

## Overview

The enhanced room schedule template extends the existing JSON schema (v1.1.0) to support modern construction workflows including activity management, digital integration, sustainability tracking, cost management, and facility operations. The design maintains full backward compatibility while adding comprehensive new data structures that align with Norwegian building standards and emerging industry practices.

## Architecture

### Schema Versioning Strategy
- Current schema version: 1.1.0
- Enhanced schema version: 2.0.0
- Backward compatibility maintained through optional field design
- Migration path provided for existing data

### Data Structure Hierarchy
The enhanced template follows the existing hierarchical structure:
```
Root
├── meta (enhanced with activity tracking)
├── identification (unchanged)
├── ifc (unchanged)
├── classification (unchanged)
├── geometry (unchanged)
├── performance_requirements (unchanged)
├── finishes (unchanged)
├── openings (unchanged)
├── fixtures_and_equipment (unchanged)
├── hse_and_accessibility (unchanged)
├── environment (enhanced with circularity data)
├── tolerances_and_quality (unchanged)
├── qa_qc (unchanged)
├── interfaces (unchanged)
├── logistics_and_site (unchanged)
├── commissioning (unchanged)
├── attachments (unchanged)
├── notes (unchanged)
├── deviations (unchanged)
├── links (enhanced with digital twin references)
├── catalogs (enhanced with new enumerations)
├── activity (NEW)
├── digital_integration (NEW)
├── circularity (NEW)
├── economics (NEW)
└── maintenance (NEW)
```

## Components and Interfaces

### 1. Activity Management Component

**Purpose:** Track construction activities, phases, and dependencies

**Structure:**
```json
"activity": {
  "type": "bygging | riving | renovering | ombygging | vedlikehold | null",
  "phase": "planlegging | utførelse | ferdigstillelse | drift | null",
  "priority": "kritisk | høy | normal | lav | null",
  "dependencies": [
    {
      "room_id": "string",
      "activity_type": "string",
      "dependency_type": "finish_to_start | start_to_start | finish_to_finish | start_to_finish"
    }
  ],
  "estimated_duration_days": null,
  "actual_start_date": "ISO 8601 date string | null",
  "actual_completion_date": "ISO 8601 date string | null",
  "progress_percentage": null,
  "responsible_contractor": null
}
```

**Interfaces:**
- Links to project management systems via room_id references
- Integrates with scheduling tools through dependency mapping
- Connects to progress tracking systems

### 2. Digital Integration Component

**Purpose:** Enable IoT, BIM, and digital twin connectivity

**Structure:**
```json
"digital_integration": {
  "sensor_ids": ["string array"],
  "iot_devices": [
    {
      "device_id": "string",
      "device_type": "temperature | humidity | co2 | occupancy | energy | other",
      "manufacturer": "string",
      "model": "string",
      "installation_date": "ISO 8601 date string",
      "communication_protocol": "LoRaWAN | WiFi | Ethernet | BLE | Zigbee | other"
    }
  ],
  "bim_model_references": [
    {
      "model_id": "string",
      "model_uri": "string",
      "discipline": "ARK | RIV | RIE | RIB | RIA | RIBr | Annet",
      "version": "string",
      "last_updated": "ISO 8601 date string"
    }
  ],
  "digital_twin_id": "string | null",
  "monitoring_parameters": [
    {
      "parameter": "string",
      "unit": "string",
      "target_value": "number",
      "tolerance": "number"
    }
  ]
}
```

**Interfaces:**
- REST APIs for IoT device management
- IFC model linking through GUID references
- Digital twin platform integration via unique identifiers

### 3. Circularity Component

**Purpose:** Support circular economy and sustainability tracking

**Structure:**
```json
"circularity": {
  "material_passport_id": "string | null",
  "reuse_potential": "høy | medium | lav | null",
  "disassembly_plan": {
    "plan_reference": "string",
    "estimated_disassembly_time_hours": "number",
    "special_tools_required": ["string array"],
    "hazardous_materials": ["string array"]
  },
  "carbon_footprint_kg_co2": "number | null",
  "lca_reference": {
    "study_id": "string",
    "methodology": "EN 15978 | ISO 14040 | other",
    "system_boundary": "cradle_to_gate | cradle_to_grave | gate_to_gate",
    "reference_service_life_years": "number"
  },
  "recycled_content_percentage": "number | null",
  "end_of_life_scenario": "reuse | recycle | energy_recovery | disposal | null"
}
```

**Interfaces:**
- Material passport databases
- LCA calculation tools
- Circular economy reporting platforms

### 4. Economics Component

**Purpose:** Comprehensive cost tracking and analysis

**Structure:**
```json
"economics": {
  "estimated_cost_nok": "number | null",
  "cost_per_m2_nok": "number | null",
  "cost_breakdown": {
    "materials_nok": "number | null",
    "labor_nok": "number | null",
    "equipment_nok": "number | null",
    "overhead_nok": "number | null"
  },
  "lcc_analysis_reference": {
    "study_id": "string",
    "analysis_period_years": "number",
    "discount_rate_percentage": "number",
    "npv_nok": "number"
  },
  "value_engineering_notes": "string | null",
  "cost_certainty_level": "conceptual | preliminary | definitive | control | null"
}
```

**Interfaces:**
- ERP systems for cost tracking
- Project management tools for budget control
- Financial reporting systems

### 5. Maintenance Component

**Purpose:** Facility management and operational planning

**Structure:**
```json
"maintenance": {
  "cleaning_frequency": {
    "daily": "boolean",
    "weekly": "boolean", 
    "monthly": "boolean",
    "quarterly": "boolean",
    "annually": "boolean",
    "special_requirements": "string"
  },
  "maintenance_schedule": [
    {
      "activity": "string",
      "frequency": "daily | weekly | monthly | quarterly | annually | as_needed",
      "estimated_duration_hours": "number",
      "required_skills": ["string array"],
      "tools_required": ["string array"]
    }
  ],
  "service_life_years": {
    "finishes": "number | null",
    "equipment": "number | null",
    "systems": "number | null"
  },
  "warranty_period_years": {
    "materials": "number | null",
    "workmanship": "number | null",
    "equipment": "number | null"
  },
  "fdv_requirements": [
    {
      "category": "forvaltning | drift | vedlikehold",
      "requirement": "string",
      "reference_standard": "string",
      "compliance_level": "mandatory | recommended | optional"
    }
  ]
}
```

**Interfaces:**
- CMMS (Computerized Maintenance Management Systems)
- Facility management platforms
- Warranty tracking systems

## Data Models

### Enhanced Schema Structure

The enhanced template maintains the existing structure while adding new top-level sections. All new fields are optional to ensure backward compatibility.

### Validation Rules

1. **Date Validation:** All date fields must follow ISO 8601 format
2. **Numeric Constraints:** Cost and measurement fields must be non-negative
3. **Reference Integrity:** All ID references must be valid UUIDs or conform to specified formats
4. **Enumeration Validation:** All enumerated fields must match predefined catalog values
5. **Dependency Logic:** Activity dependencies must not create circular references

### Schema Migration

```json
{
  "migration": {
    "from_version": "1.1.0",
    "to_version": "2.0.0",
    "changes": [
      "Added activity section",
      "Added digital_integration section", 
      "Added circularity section",
      "Added economics section",
      "Added maintenance section",
      "Enhanced catalogs with new enumerations"
    ],
    "backward_compatible": true
  }
}
```

## Error Handling

### Validation Errors
- Invalid enumeration values: Return specific error with valid options
- Missing required dependencies: Validate dependency chains
- Date logic errors: Ensure start dates precede end dates
- Reference errors: Validate external ID references

### Data Integrity
- Null value handling: All new fields default to null for compatibility
- Type coercion: Automatic conversion where safe and logical
- Range validation: Numeric fields within reasonable bounds
- Format validation: Structured data follows defined schemas

## Testing Strategy

### Unit Testing
- Schema validation for each new component
- Data type validation and constraints
- Enumeration value validation
- Date format and logic validation

### Integration Testing  
- Backward compatibility with existing v1.1.0 data
- Migration testing from old to new schema
- External system integration (IoT, BIM, etc.)
- Cross-component data consistency

### Performance Testing
- Large dataset handling with enhanced schema
- Query performance with additional fields
- Memory usage with expanded data structure

### User Acceptance Testing
- Template usability with new fields
- Data entry workflow validation
- Report generation with enhanced data
- Export/import functionality testing

The design ensures that the enhanced room schedule template provides comprehensive functionality for modern construction projects while maintaining full compatibility with existing systems and data.