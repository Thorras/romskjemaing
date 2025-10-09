#!/usr/bin/env python3
"""
Configuration management for IFC Plan View Generator
Supports JSON schema-based configuration with Norwegian documentation
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ClassFilters:
    """Filtre for IFC-klasser som inngår i snitt"""
    include_ifc_classes: List[str] = field(default_factory=list)
    exclude_ifc_classes: List[str] = field(default_factory=list)

@dataclass
class Units:
    """Enhetshåndtering"""
    unit_scale_to_m: Optional[float] = None
    auto_detect_units: bool = True

@dataclass
class Geometry:
    """Geometrigenerering via IfcOpenShell"""
    use_world_coords: bool = True
    subtract_openings: bool = True
    sew_shells: bool = True

@dataclass
class Tolerances:
    """Numeriske toleranser for snitt og kjeding"""
    slice_tol: float = 1e-6
    chain_tol: float = 1e-6

@dataclass
class ClassStyle:
    """Stil for en spesifikk IFC-klasse"""
    color: str = "#000000"
    linewidth_px: float = 0.8

@dataclass
class Rendering:
    """Stil for tegning i SVG"""
    invert_y: bool = True
    background: str = ""  # Tom for transparent
    default_color: str = "#000000"
    default_linewidth_px: float = 0.8
    class_styles: Dict[str, ClassStyle] = field(default_factory=dict)

@dataclass
class Output:
    """Utdata og navnekonvensjoner"""
    svg_filename_pattern: str = "{index:02d}_{storey_name_sanitized}.svg"
    manifest_filename: str = "manifest.json"
    write_geojson: bool = False
    geojson_filename_pattern: str = "{index:02d}_{storey_name_sanitized}.geojson"

@dataclass
class Performance:
    """Ytelsesinnstillinger"""
    multiprocessing: bool = False
    max_workers: int = 4
    cache_geometry: bool = True

@dataclass
class StoreyOverride:
    """Overstyring per etasje"""
    cut_offset_m: float

@dataclass
class IFCPlanViewConfig:
    """Hovedkonfigurasjon for IFC Plan View Generator"""
    input_path: str
    output_dir: str
    cut_offset_m: float = 1.10
    per_storey_overrides: Dict[str, StoreyOverride] = field(default_factory=dict)
    class_filters: ClassFilters = field(default_factory=ClassFilters)
    units: Units = field(default_factory=Units)
    geometry: Geometry = field(default_factory=Geometry)
    tolerances: Tolerances = field(default_factory=Tolerances)
    rendering: Rendering = field(default_factory=Rendering)
    output: Output = field(default_factory=Output)
    performance: Performance = field(default_factory=Performance)

    @classmethod
    def from_json_file(cls, config_path: str) -> 'IFCPlanViewConfig':
        """Last konfigurasjon fra JSON-fil"""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IFCPlanViewConfig':
        """Opprett konfigurasjon fra dictionary"""
        # Handle nested objects
        if 'class_filters' in data:
            data['class_filters'] = ClassFilters(**data['class_filters'])
        
        if 'units' in data:
            data['units'] = Units(**data['units'])
        
        if 'geometry' in data:
            data['geometry'] = Geometry(**data['geometry'])
        
        if 'tolerances' in data:
            data['tolerances'] = Tolerances(**data['tolerances'])
        
        if 'rendering' in data:
            rendering_data = data['rendering']
            if 'class_styles' in rendering_data:
                class_styles = {}
                for class_name, style_data in rendering_data['class_styles'].items():
                    class_styles[class_name] = ClassStyle(**style_data)
                rendering_data['class_styles'] = class_styles
            data['rendering'] = Rendering(**rendering_data)
        
        if 'output' in data:
            data['output'] = Output(**data['output'])
        
        if 'performance' in data:
            data['performance'] = Performance(**data['performance'])
        
        if 'per_storey_overrides' in data:
            overrides = {}
            for storey_name, override_data in data['per_storey_overrides'].items():
                overrides[storey_name] = StoreyOverride(**override_data)
            data['per_storey_overrides'] = overrides
        
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary for JSON-serialisering"""
        result = {}
        
        for key, value in self.__dict__.items():
            if isinstance(value, dict):
                if key == 'per_storey_overrides':
                    result[key] = {k: v.__dict__ for k, v in value.items()}
                elif key == 'class_styles':
                    result[key] = {k: v.__dict__ for k, v in value.items()}
                else:
                    result[key] = value
            elif hasattr(value, '__dict__'):
                if key == 'rendering' and hasattr(value, 'class_styles'):
                    rendering_dict = value.__dict__.copy()
                    rendering_dict['class_styles'] = {k: v.__dict__ for k, v in value.class_styles.items()}
                    result[key] = rendering_dict
                else:
                    result[key] = value.__dict__
            else:
                result[key] = value
        
        return result

    def save_to_file(self, config_path: str):
        """Lagre konfigurasjon til JSON-fil"""
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def get_cut_height_for_storey(self, storey_name: str, storey_elevation: float) -> float:
        """Få snitthøyde for en spesifikk etasje"""
        if storey_name in self.per_storey_overrides:
            return storey_elevation + self.per_storey_overrides[storey_name].cut_offset_m
        return storey_elevation + self.cut_offset_m

    def should_include_ifc_class(self, ifc_class: str) -> bool:
        """Sjekk om en IFC-klasse skal inkluderes"""
        # Hvis include_ifc_classes er tom, inkluder alle (minus exclude)
        if not self.class_filters.include_ifc_classes:
            return ifc_class not in self.class_filters.exclude_ifc_classes
        
        # Hvis include_ifc_classes har verdier, må klassen være der
        if ifc_class not in self.class_filters.include_ifc_classes:
            return False
        
        # Sjekk at den ikke er ekskludert
        return ifc_class not in self.class_filters.exclude_ifc_classes

    def get_style_for_class(self, ifc_class: str) -> ClassStyle:
        """Få stil for en IFC-klasse"""
        if ifc_class in self.rendering.class_styles:
            return self.rendering.class_styles[ifc_class]
        
        # Return default style
        return ClassStyle(
            color=self.rendering.default_color,
            linewidth_px=self.rendering.default_linewidth_px
        )

def create_default_config(input_path: str, output_dir: str) -> IFCPlanViewConfig:
    """Opprett standardkonfigurasjon"""
    return IFCPlanViewConfig(
        input_path=input_path,
        output_dir=output_dir,
        cut_offset_m=1.10,
        class_filters=ClassFilters(
            include_ifc_classes=[],  # Tom = alle relevante
            exclude_ifc_classes=["IfcSpace", "IfcOpeningElement"]
        ),
        rendering=Rendering(
            class_styles={
                "IfcWall": ClassStyle(color="#000000", linewidth_px=1.0),
                "IfcSlab": ClassStyle(color="#666666", linewidth_px=0.8),
                "IfcColumn": ClassStyle(color="#333333", linewidth_px=1.2),
                "IfcBeam": ClassStyle(color="#444444", linewidth_px=0.6),
                "IfcDoor": ClassStyle(color="#8B4513", linewidth_px=0.8),
                "IfcWindow": ClassStyle(color="#4169E1", linewidth_px=0.8)
            }
        )
    )

def load_config_with_fallback(config_path: Optional[str], input_path: str, output_dir: str) -> IFCPlanViewConfig:
    """Last konfigurasjon med fallback til standard"""
    if config_path and os.path.exists(config_path):
        try:
            return IFCPlanViewConfig.from_json_file(config_path)
        except Exception as e:
            print(f"[WARNING] Kunne ikke laste konfigurasjon fra {config_path}: {e}")
            print("[INFO] Bruker standardkonfigurasjon")
    
    return create_default_config(input_path, output_dir)