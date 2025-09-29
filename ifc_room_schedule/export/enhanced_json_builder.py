"""
Enhanced JSON Builder

Handles building enhanced JSON export structure with NS 8360/NS 3940 standards integration.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

from ..data.space_model import SpaceData
from ..data.enhanced_room_schedule_model import EnhancedRoomScheduleData
from ..mappers.meta_mapper import MetaMapper
from ..mappers.enhanced_identification_mapper import EnhancedIdentificationMapper
from ..mappers.ifc_metadata_mapper import IFCMetadataMapper
from ..mappers.geometry_enhanced_mapper import GeometryEnhancedMapper
from ..mappers.enhanced_classification_mapper import EnhancedClassificationMapper
from ..mappers.ns3940_performance_mapper import NS3940PerformanceMapper
from ..mappers.performance_requirements_mapper import PerformanceRequirementsMapper
from ..mappers.finishes_mapper import FinishesMapper
from ..mappers.openings_mapper import OpeningsMapper
from ..mappers.fixtures_mapper import FixturesMapper
from ..mappers.hse_mapper import HSEMapper
from ..mappers.qaqc_mapper import QAQCMapper
from ..mappers.interfaces_mapper import InterfacesMapper
from ..mappers.logistics_mapper import LogisticsMapper
from ..mappers.commissioning_mapper import CommissioningMapper
from ..validation.ns8360_validator import NS8360Validator
from ..validation.ns3940_validator import NS3940Validator


class EnhancedJsonBuilder:
    """Builds enhanced JSON export structure with NS standards integration."""
    
    def __init__(self):
        """Initialize the enhanced JSON builder."""
        self.source_file_path: Optional[str] = None
        self.ifc_version: Optional[str] = None
        self.application_version: str = "2.0.0"
        
        # Initialize mappers
        self.meta_mapper = MetaMapper()
        self.identification_mapper = EnhancedIdentificationMapper()
        self.ifc_metadata_mapper = IFCMetadataMapper()
        self.geometry_mapper = GeometryEnhancedMapper()
        self.classification_mapper = EnhancedClassificationMapper()
        self.performance_mapper = NS3940PerformanceMapper()
        
        # Phase 2B mappers
        self.performance_requirements_mapper = PerformanceRequirementsMapper()
        self.finishes_mapper = FinishesMapper()
        self.openings_mapper = OpeningsMapper()
        self.fixtures_mapper = FixturesMapper()
        self.hse_mapper = HSEMapper()
        
        # Phase 2C mappers
        self.qaqc_mapper = QAQCMapper()
        self.interfaces_mapper = InterfacesMapper()
        self.logistics_mapper = LogisticsMapper()
        self.commissioning_mapper = CommissioningMapper()
        
        # Initialize validators
        self.ns8360_validator = NS8360Validator()
        self.ns3940_validator = NS3940Validator()
    
    def set_source_file(self, file_path: str) -> None:
        """Set the source IFC file path."""
        self.source_file_path = file_path
    
    def set_ifc_version(self, version: str) -> None:
        """Set the IFC version."""
        self.ifc_version = version
    
    def build_enhanced_json_structure(self, spaces: List[SpaceData], 
                                    ifc_file_metadata: Optional[Dict[str, Any]] = None,
                                    export_profile: str = "production") -> Dict[str, Any]:
        """
        Build enhanced JSON structure with NS standards integration.
        
        Args:
            spaces: List of SpaceData objects to export
            ifc_file_metadata: Optional IFC file metadata
            export_profile: Export profile (core, advanced, production)
            
        Returns:
            Enhanced JSON structure ready for export
        """
        # Generate enhanced metadata
        enhanced_metadata = self._generate_enhanced_metadata(ifc_file_metadata)
        
        # Build enhanced spaces data
        enhanced_spaces = []
        compliance_stats = {
            "total_spaces": len(spaces),
            "ns8360_compliant": 0,
            "ns3940_classified": 0,
            "performance_requirements": 0
        }
        
        for space in spaces:
            space_data = self._build_enhanced_space_dict(space, export_profile)
            enhanced_spaces.append(space_data)
            
            # Update compliance statistics
            if space_data.get("ns8360_compliance", {}).get("name_pattern_valid", False):
                compliance_stats["ns8360_compliant"] += 1
            
            if space_data.get("classification", {}).get("ns3940"):
                compliance_stats["ns3940_classified"] += 1
            
            if space_data.get("performance_requirements"):
                compliance_stats["performance_requirements"] += 1
        
        # Generate enhanced summary
        enhanced_summary = self._generate_enhanced_summary(spaces, compliance_stats)
        
        # Build complete enhanced structure
        enhanced_json = {
            "metadata": enhanced_metadata,
            "spaces": enhanced_spaces,
            "summary": enhanced_summary,
            "ns_standards_compliance": self._generate_compliance_report(compliance_stats)
        }
        
        return enhanced_json
    
    def _generate_enhanced_metadata(self, ifc_file_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate enhanced metadata with NS standards information."""
        # Use MetaMapper to generate metadata
        meta_data = self.meta_mapper.extract_meta_data(
            self.source_file_path or "unknown.ifc",
            ifc_file_metadata
        )
        
        # Convert to dictionary format
        enhanced_metadata = {
            "export_date": meta_data.timestamps["export_date"],
            "application_version": self.application_version,
            "schema_version": "2.0.0",
            "ns_standards": {
                "ns8360_version": meta_data.ns_compliance["ns8360_version"],
                "ns3940_version": meta_data.ns_compliance["ns3940_version"],
                "tek17_version": meta_data.ns_compliance["tek17_version"],
                "compliance_status": meta_data.ns_compliance["compliance_status"]
            },
            "file_info": meta_data.file_info,
            "project_info": meta_data.project_info,
            "timestamps": meta_data.timestamps
        }
        
        return enhanced_metadata
    
    def _build_enhanced_space_dict(self, space: SpaceData, export_profile: str) -> Dict[str, Any]:
        """Build enhanced dictionary representation of a space."""
        # Basic space properties
        space_dict = {
            "guid": space.guid,
            "properties": {
                "name": space.name,
                "long_name": space.long_name,
                "description": space.description,
                "object_type": space.object_type,
                "zone_category": space.zone_category,
                "number": space.number,
                "elevation": space.elevation,
                "quantities": space.quantities,
                "processed": space.processed,
                "user_descriptions": space.user_descriptions
            }
        }
        
        # Add NS standards sections based on export profile
        if export_profile in ["advanced", "production"]:
            # Identification section
            identification = self.identification_mapper.map_identification(space, self.source_file_path)
            space_dict["identification"] = {
                "project_id": identification.project_id,
                "project_name": identification.project_name,
                "building_id": identification.building_id,
                "building_name": identification.building_name,
                "storey_name": identification.storey_name,
                "storey_elevation_m": identification.storey_elevation_m,
                "room_number": identification.room_number,
                "room_name": identification.room_name,
                "function": identification.function,
                "occupancy_type": identification.occupancy_type
            }
            
            # IFC metadata section
            ifc_metadata = self.identification_mapper.map_ifc_metadata(space, self.source_file_path)
            space_dict["ifc_metadata"] = {
                "space_global_id": ifc_metadata.space_global_id,
                "space_long_name": ifc_metadata.space_long_name,
                "space_number": ifc_metadata.space_number,
                "ns8360_compliant": ifc_metadata.ns8360_compliant,
                "parsed_name_components": ifc_metadata.parsed_name_components,
                "model_source": ifc_metadata.model_source
            }
            
            # Enhanced geometry section
            geometry = self.geometry_mapper.calculate_enhanced_geometry(space)
            space_dict["geometry"] = {
                "length_m": geometry.length_m,
                "width_m": geometry.width_m,
                "height_m": geometry.height_m,
                "net_floor_area_m2": geometry.net_floor_area_m2,
                "gross_floor_area_m2": geometry.gross_floor_area_m2,
                "wall_area_m2": geometry.wall_area_m2,
                "ceiling_area_m2": geometry.ceiling_area_m2,
                "net_volume_m3": geometry.net_volume_m3,
                "gross_volume_m3": geometry.gross_volume_m3,
                "room_origin": geometry.room_origin,
                "room_orientation_deg": geometry.room_orientation_deg,
                "room_shape_type": geometry.room_shape_type,
                "room_aspect_ratio": geometry.room_aspect_ratio,
                "clear_width_m": geometry.clear_width_m,
                "clear_height_m": geometry.clear_height_m,
                "turning_radius_m": geometry.turning_radius_m,
                "estimated_dimensions": geometry.estimated_dimensions,
                "estimation_confidence": geometry.estimation_confidence,
                "estimation_method": geometry.estimation_method
            }
            
            # Enhanced classification section
            classification = self.classification_mapper.map_classification(space)
            space_dict["classification"] = {
                "ns3940": classification.ns3940,
                "ns8360_compliance": classification.ns8360_compliance,
                "tfm": classification.tfm,
                "custom_codes": classification.custom_codes,
                "validation_status": classification.validation_status,
                "overall_confidence": classification.overall_confidence,
                "classification_source": classification.classification_source
            }
            
            # Phase 2B: Performance requirements section
            if export_profile == "production":
                # Use new Phase 2B mappers
                performance_req = self.performance_requirements_mapper.extract_performance_requirements(space)
                space_dict["performance_requirements"] = self._build_performance_requirements_dict(performance_req)
                
                # Add other Phase 2B sections
                finishes = self.finishes_mapper.extract_surface_finishes(space)
                space_dict["finishes"] = self._build_finishes_dict(finishes)
                
                openings = self.openings_mapper.extract_openings(space)
                space_dict["openings"] = self._build_openings_dict(openings)
                
                fixtures = self.fixtures_mapper.extract_fixtures(space)
                space_dict["fixtures_and_equipment"] = self._build_fixtures_dict(fixtures)
                
                hse = self.hse_mapper.extract_hse_requirements(space)
                space_dict["hse_and_accessibility"] = self._build_hse_dict(hse)
                
                # Phase 2C: Advanced sections
                qaqc = self.qaqc_mapper.extract_qa_qc_requirements(space)
                space_dict["qa_qc"] = self._build_qaqc_dict(qaqc)
                
                interfaces = self.interfaces_mapper.extract_interfaces(space)
                space_dict["interfaces"] = self._build_interfaces_dict(interfaces)
                
                logistics = self.logistics_mapper.extract_logistics(space)
                space_dict["logistics_and_site"] = self._build_logistics_dict(logistics)
                
                commissioning = self.commissioning_mapper.extract_commissioning(space)
                space_dict["commissioning"] = self._build_commissioning_dict(commissioning)
        
        # Add traditional sections (always included)
        space_dict["surfaces"] = [self._build_surface_dict(surface) for surface in space.surfaces]
        space_dict["space_boundaries"] = [self._build_space_boundary_dict(boundary) for boundary in space.space_boundaries]
        space_dict["relationships"] = [self._build_relationship_dict(relationship) for relationship in space.relationships]
        
        return space_dict
    
    def _build_performance_requirements_dict(self, performance_req) -> Dict[str, Any]:
        """Build performance requirements dictionary."""
        return {
            "fire": {
                "fire_compartment": performance_req.fire.fire_compartment,
                "fire_class": performance_req.fire.fire_class,
                "door_rating": performance_req.fire.door_rating,
                "penetration_sealing_class": performance_req.fire.penetration_sealing_class,
                "fire_resistance_rating": performance_req.fire.fire_resistance_rating,
                "smoke_control": performance_req.fire.smoke_control,
                "escape_route": performance_req.fire.escape_route
            },
            "acoustics": {
                "class_ns8175": performance_req.acoustics.class_ns8175,
                "rw_dB": performance_req.acoustics.rw_dB,
                "ln_w_dB": performance_req.acoustics.ln_w_dB,
                "background_noise_dB": performance_req.acoustics.background_noise_dB,
                "reverberation_time_s": performance_req.acoustics.reverberation_time_s,
                "speech_intelligibility": performance_req.acoustics.speech_intelligibility
            },
            "thermal": {
                "setpoint_heating_C": performance_req.thermal.setpoint_heating_C,
                "setpoint_cooling_C": performance_req.thermal.setpoint_cooling_C,
                "u_values": performance_req.thermal.u_values,
                "thermal_comfort_class": performance_req.thermal.thermal_comfort_class,
                "heating_load_W": performance_req.thermal.heating_load_W,
                "cooling_load_W": performance_req.thermal.cooling_load_W
            },
            "ventilation": {
                "airflow_supply_m3h": performance_req.ventilation.airflow_supply_m3h,
                "airflow_extract_m3h": performance_req.ventilation.airflow_extract_m3h,
                "co2_setpoint_ppm": performance_req.ventilation.co2_setpoint_ppm,
                "pressure_room_Pa": performance_req.ventilation.pressure_room_Pa,
                "air_changes_per_hour": performance_req.ventilation.air_changes_per_hour,
                "ventilation_type": performance_req.ventilation.ventilation_type,
                "filtration_class": performance_req.ventilation.filtration_class
            },
            "lighting": {
                "task_lux": performance_req.lighting.task_lux,
                "emergency_lighting": performance_req.lighting.emergency_lighting,
                "color_rendering_CRI": performance_req.lighting.color_rendering_CRI,
                "UGR_max": performance_req.lighting.UGR_max,
                "daylight_factor": performance_req.lighting.daylight_factor,
                "lighting_control": performance_req.lighting.lighting_control,
                "energy_efficiency_class": performance_req.lighting.energy_efficiency_class
            },
            "power_data": {
                "sockets_count": performance_req.power_data.sockets_count,
                "data_outlets_count": performance_req.power_data.data_outlets_count,
                "cleaning_socket": performance_req.power_data.cleaning_socket,
                "circuits": performance_req.power_data.circuits,
                "power_density_W_m2": performance_req.power_data.power_density_W_m2,
                "emergency_power": performance_req.power_data.emergency_power,
                "UPS_required": performance_req.power_data.UPS_required
            },
            "water_sanitary": {
                "fixtures": performance_req.water_sanitary.fixtures,
                "hot_cold_water": performance_req.water_sanitary.hot_cold_water,
                "drainage_required": performance_req.water_sanitary.drainage_required,
                "water_pressure_bar": performance_req.water_sanitary.water_pressure_bar,
                "water_temperature_C": performance_req.water_sanitary.water_temperature_C,
                "water_quality_standard": performance_req.water_sanitary.water_quality_standard
            }
        }
    
    def _build_finishes_dict(self, finishes) -> Dict[str, Any]:
        """Build finishes dictionary."""
        return {
            "floor": {
                "system": finishes.floor.system,
                "layers": [
                    {
                        "product": layer.product,
                        "thickness_mm": layer.thickness_mm,
                        "color_code": layer.color_code,
                        "finish_code": layer.finish_code,
                        "supplier": layer.supplier,
                        "notes": layer.notes
                    } for layer in finishes.floor.layers
                ],
                "tolerances": finishes.floor.tolerances
            },
            "ceiling": {
                "system": finishes.ceiling.system,
                "height_m": finishes.ceiling.height_m,
                "acoustic_class": finishes.ceiling.acoustic_class,
                "notes": finishes.ceiling.notes
            },
            "walls": [
                {
                    "name": wall.name,
                    "system": wall.system,
                    "finish": wall.finish,
                    "color_code": wall.color_code,
                    "impact_resistance": wall.impact_resistance,
                    "notes": wall.notes
                } for wall in finishes.walls
            ],
            "skirting": {
                "type": finishes.skirting.type,
                "height_mm": finishes.skirting.height_mm,
                "material": finishes.skirting.material
            }
        }
    
    def _build_openings_dict(self, openings) -> Dict[str, Any]:
        """Build openings dictionary."""
        return {
            "doors": [
                {
                    "id": door.id,
                    "width_mm": door.width_mm,
                    "height_mm": door.height_mm,
                    "fire_rating": door.fire_rating,
                    "sound_rating_rw_db": door.sound_rating_rw_db,
                    "threshold": door.threshold,
                    "hardware_set": door.hardware_set,
                    "access_control": door.access_control,
                    "notes": door.notes,
                    "material": door.material,
                    "frame_material": door.frame_material,
                    "door_type": door.door_type,
                    "swing_direction": door.swing_direction
                } for door in openings.doors
            ],
            "windows": [
                {
                    "id": window.id,
                    "width_mm": window.width_mm,
                    "height_mm": window.height_mm,
                    "u_value_w_m2k": window.u_value_w_m2k,
                    "g_value": window.g_value,
                    "safety_glass": window.safety_glass,
                    "solar_shading": window.solar_shading,
                    "frame_material": window.frame_material,
                    "glazing_type": window.glazing_type,
                    "window_type": window.window_type,
                    "opening_direction": window.opening_direction
                } for window in openings.windows
            ],
            "penetrations": [
                {
                    "id": penetration.id,
                    "type": penetration.type,
                    "diameter_mm": penetration.diameter_mm,
                    "width_mm": penetration.width_mm,
                    "height_mm": penetration.height_mm,
                    "fire_sealing": penetration.fire_sealing,
                    "acoustic_sealing": penetration.acoustic_sealing,
                    "notes": penetration.notes
                } for penetration in openings.penetrations
            ]
        }
    
    def _build_fixtures_dict(self, fixtures) -> List[Dict[str, Any]]:
        """Build fixtures dictionary."""
        return [
            {
                "discipline": fixture.discipline,
                "type": fixture.type,
                "id": fixture.id,
                "description": fixture.description,
                "mounting_height_m": fixture.mounting_height_m,
                "location_xyz_m": fixture.location_xyz_m,
                "connections": {
                    "power": fixture.connections.power,
                    "data": fixture.connections.data,
                    "water": fixture.connections.water,
                    "drain": fixture.connections.drain,
                    "vent": fixture.connections.vent,
                    "gas": fixture.connections.gas,
                    "compressed_air": fixture.connections.compressed_air,
                    "fire_suppression": fixture.connections.fire_suppression,
                    "security": fixture.connections.security,
                    "notes": fixture.connections.notes
                },
                "supplier": fixture.supplier,
                "product_code": fixture.product_code,
                "epd_reference": fixture.epd_reference,
                "remarks": fixture.remarks,
                "quantity": fixture.quantity,
                "power_consumption_W": fixture.power_consumption_W,
                "water_flow_l_min": fixture.water_flow_l_min,
                "air_flow_m3h": fixture.air_flow_m3h
            } for fixture in fixtures.fixtures
        ]
    
    def _build_hse_dict(self, hse) -> Dict[str, Any]:
        """Build HSE dictionary."""
        return {
            "universal_design": {
                "universal_design": hse.universal_design.universal_design,
                "turning_radius_m": hse.universal_design.turning_radius_m,
                "clear_width_door_mm": hse.universal_design.clear_width_door_mm,
                "slip_resistance_class": hse.universal_design.slip_resistance_class,
                "emissions_class": hse.universal_design.emissions_class,
                "accessible_height_mm": hse.universal_design.accessible_height_mm,
                "contrast_requirements": hse.universal_design.contrast_requirements,
                "tactile_guidance": hse.universal_design.tactile_guidance,
                "visual_guidance": hse.universal_design.visual_guidance
            },
            "safety": {
                "fire_safety_class": hse.safety.fire_safety_class,
                "escape_route_width_mm": hse.safety.escape_route_width_mm,
                "emergency_exit": hse.safety.emergency_exit,
                "smoke_detection": hse.safety.smoke_detection,
                "fire_suppression": hse.safety.fire_suppression,
                "first_aid_equipment": hse.safety.first_aid_equipment,
                "safety_signage": hse.safety.safety_signage,
                "emergency_lighting": hse.safety.emergency_lighting,
                "handrail_required": hse.safety.handrail_required,
                "guardrail_required": hse.safety.guardrail_required
            },
            "environmental": {
                "breeam_credits": hse.environmental.breeam_credits,
                "reused_materials": hse.environmental.reused_materials,
                "epd_requirements": hse.environmental.epd_requirements,
                "waste_sorting_fraction": hse.environmental.waste_sorting_fraction,
                "energy_efficiency_class": hse.environmental.energy_efficiency_class,
                "co2_emissions_kg_m2": hse.environmental.co2_emissions_kg_m2,
                "renewable_energy": hse.environmental.renewable_energy,
                "daylight_factor": hse.environmental.daylight_factor,
                "natural_ventilation": hse.environmental.natural_ventilation
            },
            "accessibility": {
                "wheelchair_accessible": hse.accessibility.wheelchair_accessible,
                "hearing_loop": hse.accessibility.hearing_loop,
                "visual_alerts": hse.accessibility.visual_alerts,
                "accessible_controls": hse.accessibility.accessible_controls,
                "accessible_furniture": hse.accessibility.accessible_furniture,
                "assistive_technology": hse.accessibility.assistive_technology,
                "quiet_space": hse.accessibility.quiet_space,
                "sensory_friendly": hse.accessibility.sensory_friendly
            }
        }
    
    def _build_qaqc_dict(self, qaqc) -> Dict[str, Any]:
        """Build QA/QC dictionary."""
        return {
            "hold_points": [
                {
                    "code": hp.code,
                    "description": hp.description,
                    "by_trade": hp.by_trade,
                    "required": hp.required,
                    "critical": hp.critical,
                    "phase": hp.phase,
                    "prerequisites": hp.prerequisites,
                    "acceptance_criteria": hp.acceptance_criteria,
                    "responsible_party": hp.responsible_party
                }
                for hp in qaqc.hold_points
            ],
            "inspections": [
                {
                    "type": insp.type.value,
                    "checklist_id": insp.checklist_id,
                    "acceptance_criteria": insp.acceptance_criteria,
                    "evidence": insp.evidence.value,
                    "responsible": insp.responsible,
                    "scheduled_date": insp.scheduled_date.isoformat() if insp.scheduled_date else None,
                    "completed_date": insp.completed_date.isoformat() if insp.completed_date else None,
                    "status": insp.status,
                    "notes": insp.notes,
                    "photos": insp.photos,
                    "measurements": insp.measurements
                }
                for insp in qaqc.inspections
            ],
            "handover_docs_required": [doc.value for doc in qaqc.handover_docs_required],
            "quality_control_plan": qaqc.quality_control_plan,
            "last_updated": qaqc.last_updated.isoformat() if qaqc.last_updated else None
        }
    
    def _build_interfaces_dict(self, interfaces) -> Dict[str, Any]:
        """Build interfaces dictionary."""
        return {
            "adjacent_rooms": [
                {
                    "room_id": room.room_id,
                    "room_name": room.room_name,
                    "room_type": room.room_type,
                    "shared_boundary_length_m": room.shared_boundary_length_m,
                    "interface_type": room.interface_type.value,
                    "fire_compartment": room.fire_compartment,
                    "acoustic_rating": room.acoustic_rating,
                    "thermal_interface": room.thermal_interface,
                    "notes": room.notes
                }
                for room in interfaces.adjacent_rooms
            ],
            "trade_interfaces": [
                {
                    "from_trade": interface.from_trade.value,
                    "to_trade": interface.to_trade.value,
                    "scope_boundary": interface.scope_boundary,
                    "interface_description": interface.interface_description,
                    "critical": interface.critical,
                    "sequence_dependency": interface.sequence_dependency,
                    "coordination_required": interface.coordination_required,
                    "handover_requirements": interface.handover_requirements,
                    "quality_requirements": interface.quality_requirements,
                    "notes": interface.notes
                }
                for interface in interfaces.trade_interfaces
            ],
            "sequence_notes": [
                {
                    "phase": note.phase,
                    "description": note.description,
                    "dependencies": note.dependencies,
                    "constraints": note.constraints,
                    "responsible_trade": note.responsible_trade.value if note.responsible_trade else None,
                    "critical_path": note.critical_path,
                    "notes": note.notes
                }
                for note in interfaces.sequence_notes
            ],
            "last_updated": interfaces.last_updated.isoformat() if interfaces.last_updated else None
        }
    
    def _build_logistics_dict(self, logistics) -> Dict[str, Any]:
        """Build logistics dictionary."""
        return {
            "access_route": {
                "route_id": logistics.access_route.route_id,
                "description": logistics.access_route.description,
                "width_m": logistics.access_route.width_m,
                "height_m": logistics.access_route.height_m,
                "load_capacity_kg": logistics.access_route.load_capacity_kg,
                "restrictions": logistics.access_route.restrictions,
                "notes": logistics.access_route.notes
            } if logistics.access_route else None,
            "work_constraints": {
                "work_hours": logistics.work_constraints.work_hours,
                "noise_constraints": logistics.work_constraints.noise_constraints,
                "cleanliness_requirements": logistics.work_constraints.cleanliness_requirements,
                "temperature_requirements": logistics.work_constraints.temperature_requirements,
                "ventilation_requirements": logistics.work_constraints.ventilation_requirements,
                "notes": logistics.work_constraints.notes
            },
            "rigging_drift": {
                "site_facilities": logistics.rigging_drift.site_facilities,
                "temporary_utilities": logistics.rigging_drift.temporary_utilities,
                "material_handling": logistics.rigging_drift.material_handling,
                "storage": logistics.rigging_drift.storage,
                "waste_management": logistics.rigging_drift.waste_management,
                "winter_measures": logistics.rigging_drift.winter_measures,
                "snow_ice_plan": logistics.rigging_drift.snow_ice_plan
            },
            "sha_plan": {
                "risk_activities": logistics.sha_plan.risk_activities,
                "permits_required": [p.value for p in logistics.sha_plan.permits_required],
                "ppe": [p.value for p in logistics.sha_plan.ppe],
                "sja_required": logistics.sha_plan.sja_required,
                "responsible_roles": logistics.sha_plan.responsible_roles,
                "emergency_procedures": logistics.sha_plan.emergency_procedures,
                "environmental_considerations": logistics.sha_plan.environmental_considerations
            },
            "lean_takt": {
                "takt_area_id": logistics.lean_takt.takt_area_id,
                "takt_time_days": logistics.lean_takt.takt_time_days,
                "sequence": logistics.lean_takt.sequence,
                "constraints": logistics.lean_takt.constraints,
                "handoff_criteria": logistics.lean_takt.handoff_criteria,
                "quality_gates": logistics.lean_takt.quality_gates,
                "notes": logistics.lean_takt.notes
            },
            "last_updated": logistics.last_updated.isoformat() if logistics.last_updated else None
        }
    
    def _build_commissioning_dict(self, commissioning) -> Dict[str, Any]:
        """Build commissioning dictionary."""
        return {
            "tests": [
                {
                    "name": test.name,
                    "test_type": test.test_type.value,
                    "method": test.method.value,
                    "criteria": test.criteria,
                    "witnessed_by": test.witnessed_by,
                    "scheduled_date": test.scheduled_date.isoformat() if test.scheduled_date else None,
                    "completed_date": test.completed_date.isoformat() if test.completed_date else None,
                    "status": test.status,
                    "results": test.results,
                    "notes": test.notes,
                    "photos": test.photos,
                    "certificates": test.certificates
                }
                for test in commissioning.tests
            ],
            "balancing": [
                {
                    "system_type": balance.system_type.value,
                    "required": balance.required,
                    "description": balance.description,
                    "criteria": balance.criteria,
                    "responsible": balance.responsible,
                    "scheduled_date": balance.scheduled_date.isoformat() if balance.scheduled_date else None,
                    "completed_date": balance.completed_date.isoformat() if balance.completed_date else None,
                    "status": balance.status,
                    "results": balance.results,
                    "notes": balance.notes,
                    "certificates": balance.certificates
                }
                for balance in commissioning.balancing
            ],
            "handover_requirements": commissioning.handover_requirements,
            "commissioning_plan": commissioning.commissioning_plan,
            "last_updated": commissioning.last_updated.isoformat() if commissioning.last_updated else None
        }
    
    def _build_surface_dict(self, surface) -> Dict[str, Any]:
        """Build dictionary representation of a surface."""
        return {
            "id": surface.id,
            "type": surface.type,
            "area": surface.area,
            "material": surface.material,
            "ifc_type": surface.ifc_type,
            "related_space_guid": surface.related_space_guid,
            "user_description": surface.user_description,
            "properties": surface.properties
        }
    
    def _build_space_boundary_dict(self, boundary) -> Dict[str, Any]:
        """Build dictionary representation of a space boundary."""
        return boundary.to_dict()
    
    def _build_relationship_dict(self, relationship) -> Dict[str, Any]:
        """Build dictionary representation of a relationship."""
        return {
            "related_entity_guid": relationship.related_entity_guid,
            "related_entity_name": relationship.related_entity_name,
            "related_entity_description": relationship.related_entity_description,
            "relationship_type": relationship.relationship_type,
            "ifc_relationship_type": relationship.ifc_relationship_type
        }
    
    def _generate_enhanced_summary(self, spaces: List[SpaceData], compliance_stats: Dict[str, int]) -> Dict[str, Any]:
        """Generate enhanced summary with NS standards statistics."""
        # Basic summary
        total_spaces = len(spaces)
        processed_spaces = sum(1 for space in spaces if space.processed)
        
        # Calculate areas
        total_surface_area = sum(space.get_total_surface_area() for space in spaces)
        total_boundary_area = sum(space.get_total_boundary_area() for space in spaces)
        
        # NS standards compliance
        ns8360_compliance_percentage = (compliance_stats["ns8360_compliant"] / total_spaces * 100) if total_spaces > 0 else 0
        ns3940_classification_percentage = (compliance_stats["ns3940_classified"] / total_spaces * 100) if total_spaces > 0 else 0
        performance_requirements_percentage = (compliance_stats["performance_requirements"] / total_spaces * 100) if total_spaces > 0 else 0
        
        # Room type distribution
        room_type_distribution = {}
        for space in spaces:
            # Try to get room type from classification
            classification = self.classification_mapper.map_classification(space)
            if classification.ns3940 and classification.ns3940.get("label"):
                room_type = classification.ns3940["label"]
                room_type_distribution[room_type] = room_type_distribution.get(room_type, 0) + 1
        
        enhanced_summary = {
            "total_spaces": total_spaces,
            "processed_spaces": processed_spaces,
            "total_surface_area": round(total_surface_area, 2),
            "total_boundary_area": round(total_boundary_area, 2),
            "ns_standards_compliance": {
                "ns8360_compliant_spaces": compliance_stats["ns8360_compliant"],
                "ns8360_compliance_percentage": round(ns8360_compliance_percentage, 1),
                "ns3940_classified_spaces": compliance_stats["ns3940_classified"],
                "ns3940_classification_percentage": round(ns3940_classification_percentage, 1),
                "performance_requirements_spaces": compliance_stats["performance_requirements"],
                "performance_requirements_percentage": round(performance_requirements_percentage, 1)
            },
            "room_type_distribution": room_type_distribution,
            "export_profile": "enhanced_with_ns_standards",
            "standards_versions": {
                "ns8360": "NS 8360:2023",
                "ns3940": "NS 3940:2023",
                "tek17": "TEK17"
            }
        }
        
        return enhanced_summary
    
    def _generate_compliance_report(self, compliance_stats: Dict[str, int]) -> Dict[str, Any]:
        """Generate NS standards compliance report."""
        total_spaces = compliance_stats["total_spaces"]
        
        return {
            "overall_compliance": {
                "total_spaces": total_spaces,
                "ns8360_compliant": compliance_stats["ns8360_compliant"],
                "ns3940_classified": compliance_stats["ns3940_classified"],
                "performance_requirements": compliance_stats["performance_requirements"]
            },
            "compliance_percentages": {
                "ns8360": round((compliance_stats["ns8360_compliant"] / total_spaces * 100) if total_spaces > 0 else 0, 1),
                "ns3940": round((compliance_stats["ns3940_classified"] / total_spaces * 100) if total_spaces > 0 else 0, 1),
                "performance": round((compliance_stats["performance_requirements"] / total_spaces * 100) if total_spaces > 0 else 0, 1)
            },
            "recommendations": self._generate_compliance_recommendations(compliance_stats),
            "validation_timestamp": datetime.now().isoformat()
        }
    
    def _generate_compliance_recommendations(self, compliance_stats: Dict[str, int]) -> List[str]:
        """Generate compliance improvement recommendations."""
        recommendations = []
        total_spaces = compliance_stats["total_spaces"]
        
        if total_spaces == 0:
            return recommendations
        
        ns8360_percentage = (compliance_stats["ns8360_compliant"] / total_spaces * 100)
        ns3940_percentage = (compliance_stats["ns3940_classified"] / total_spaces * 100)
        
        if ns8360_percentage < 50:
            recommendations.append("Improve NS 8360 naming compliance - use SPC-{storey}-{zone}-{function}-{sequence} format")
        
        if ns3940_percentage < 70:
            recommendations.append("Improve NS 3940 classification - ensure room names contain recognizable function keywords")
        
        if compliance_stats["performance_requirements"] < total_spaces * 0.8:
            recommendations.append("Add performance requirements for more spaces using NS 3940 defaults")
        
        return recommendations
    
    def validate_enhanced_export_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate enhanced export data for completeness and correctness."""
        errors = []
        
        # Check required top-level keys
        required_keys = ["metadata", "spaces", "summary", "ns_standards_compliance"]
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
        
        # Validate metadata
        if "metadata" in data:
            metadata = data["metadata"]
            if "ns_standards" not in metadata:
                errors.append("Missing ns_standards in metadata")
            if "export_date" not in metadata:
                errors.append("Missing export_date in metadata")
        
        # Validate spaces
        if "spaces" in data:
            spaces = data["spaces"]
            if not isinstance(spaces, list):
                errors.append("Spaces must be a list")
            else:
                for i, space in enumerate(spaces):
                    space_errors = self._validate_enhanced_space_data(space, i)
                    errors.extend(space_errors)
        
        return len(errors) == 0, errors
    
    def _validate_enhanced_space_data(self, space_data: Dict[str, Any], space_index: int) -> List[str]:
        """Validate enhanced space data."""
        errors = []
        prefix = f"Space {space_index}"
        
        # Check required keys
        required_keys = ["guid", "properties", "identification", "classification"]
        for key in required_keys:
            if key not in space_data:
                errors.append(f"{prefix}: Missing required key {key}")
        
        # Validate NS standards sections
        if "classification" in space_data:
            classification = space_data["classification"]
            if "ns3940" not in classification and "ns8360_compliance" not in classification:
                errors.append(f"{prefix}: Missing NS standards classification data")
        
        return errors
    
    def export_enhanced_json(self, spaces: List[SpaceData], filename: str,
                           ifc_file_metadata: Optional[Dict[str, Any]] = None,
                           export_profile: str = "production",
                           validate: bool = True) -> Tuple[bool, List[str]]:
        """
        Complete enhanced export workflow with NS standards integration.
        
        Args:
            spaces: List of SpaceData objects to export
            filename: Output filename
            ifc_file_metadata: Optional IFC file metadata
            export_profile: Export profile (core, advanced, production)
            validate: Whether to validate data before export
            
        Returns:
            Tuple of (success, list_of_errors_or_messages)
        """
        try:
            # Build enhanced JSON structure
            json_data = self.build_enhanced_json_structure(spaces, ifc_file_metadata, export_profile)
            
            # Validate if requested
            if validate:
                is_valid, validation_errors = self.validate_enhanced_export_data(json_data)
                if not is_valid:
                    return False, validation_errors
            
            # Write to file
            success, write_message = self._write_enhanced_json_file(filename, json_data)
            if success:
                return True, [f"Successfully exported {len(spaces)} spaces with NS standards to {filename}"]
            else:
                return False, [f"Failed to write enhanced JSON file: {write_message}"]
                
        except Exception as e:
            return False, [f"Enhanced export failed: {str(e)}"]
    
    def _write_enhanced_json_file(self, filename: str, data: Dict[str, Any], indent: int = 2) -> Tuple[bool, str]:
        """Write enhanced JSON data to file with error handling."""
        try:
            if not filename:
                return False, "Filename cannot be empty"
            
            file_path = Path(filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check write permissions
            if file_path.exists():
                if not os.access(file_path, os.W_OK):
                    return False, f"No write permission for file: {filename}"
            else:
                if not os.access(file_path.parent, os.W_OK):
                    return False, f"No write permission for directory: {file_path.parent}"
            
            # Check disk space
            free_space = shutil.disk_usage(file_path.parent).free
            if free_space < 1024 * 1024:  # 1MB minimum
                return False, f"Insufficient disk space. Available: {free_space / (1024*1024):.1f}MB"
            
            # Validate JSON serialization
            try:
                json.dumps(data, indent=indent, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                return False, f"Data cannot be serialized to JSON: {str(e)}"
            
            # Write to temporary file first, then rename for atomic operation
            temp_filename = str(file_path) + '.tmp'
            try:
                with open(temp_filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=indent, ensure_ascii=False)
                
                # Atomic rename
                if os.name == 'nt':  # Windows
                    if file_path.exists():
                        os.remove(file_path)
                os.rename(temp_filename, filename)
                
                return True, "Enhanced JSON file written successfully"
                
            except Exception as e:
                # Clean up temp file
                if os.path.exists(temp_filename):
                    try:
                        os.remove(temp_filename)
                    except:
                        pass
                raise e
            
        except PermissionError as e:
            return False, f"Permission denied: {str(e)}"
        except OSError as e:
            return False, f"OS error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error writing enhanced JSON file: {str(e)}"


# Example usage and testing
if __name__ == "__main__":
    from ..data.space_model import SpaceData
    
    # Create test space data
    test_spaces = [
        SpaceData(
            guid="GUID-STUE-001",
            name="SPC-02-A101-111-003",
            long_name="Stue | 02/A101 | NS3940:111",
            description="Oppholdsrom i A101",
            object_type="IfcSpace",
            zone_category="Residential",
            number="003",
            elevation=6.0,
            quantities={"NetFloorArea": 24.0, "GrossFloorArea": 25.5}
        ),
        SpaceData(
            guid="GUID-BAD-001",
            name="Bad 2. etasje",
            description="Bad med dusj",
            object_type="IfcSpace",
            zone_category="Residential",
            number="001",
            elevation=6.0,
            quantities={"NetFloorArea": 4.8, "GrossFloorArea": 5.2}
        )
    ]
    
    builder = EnhancedJsonBuilder()
    builder.set_source_file("AkkordSvingen_23_ARK.ifc")
    builder.set_ifc_version("IFC4")
    
    print("Enhanced JSON Builder Test Results:")
    print("=" * 60)
    
    # Test enhanced export
    success, messages = builder.export_enhanced_json(
        test_spaces, 
        "test_enhanced_export.json",
        export_profile="production"
    )
    
    print(f"Export Success: {success}")
    for message in messages:
        print(f"Message: {message}")
    
    # Test JSON structure building
    json_data = builder.build_enhanced_json_structure(test_spaces, export_profile="production")
    
    print(f"\nJSON Structure Keys: {list(json_data.keys())}")
    print(f"Number of Spaces: {len(json_data['spaces'])}")
    print(f"NS Standards Compliance: {json_data['ns_standards_compliance']['compliance_percentages']}")
    
    # Test validation
    is_valid, errors = builder.validate_enhanced_export_data(json_data)
    print(f"Validation Valid: {is_valid}")
    if errors:
        print(f"Validation Errors: {errors}")
