#!/usr/bin/env python3
"""
IFC Floor Plan Generator - Creates SVG floor plans for each building storey
Based on horizontal slicing of IFC geometry with advanced configuration support
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_planview_config import IFCPlanViewConfig, load_config_with_fallback
import ifcopenshell
import ifcopenshell.geom
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon as MPLPolygon
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import math
import json
import re
from pathlib import Path

@dataclass
class SliceResult:
    """Result of slicing geometry at a specific height"""
    lines: List[Tuple[Tuple[float, float], Tuple[float, float]]]
    element_type: str
    element_name: str
    element_guid: str

@dataclass
class StoreyManifest:
    """Manifest entry for a building storey"""
    index: int
    storey_name: str
    storey_name_sanitized: str
    elevation: float
    cut_height: float
    svg_filename: str
    geojson_filename: Optional[str] = None
    element_count: int = 0
    line_count: int = 0

class IFCFloorPlanGenerator:
    """Generates 2D floor plans from IFC files using horizontal slicing with advanced configuration"""
    
    def __init__(self, config: IFCPlanViewConfig):
        self.config = config
        self.ifc_file = None
        self.unit_scale = 1.0
        self.geometry_cache = {} if config.performance.cache_geometry else None
        
    def load_ifc_file(self, file_path: str) -> bool:
        """Load IFC file and determine unit scale"""
        try:
            reader = IfcFileReader()
            success, message = reader.load_file(file_path)
            
            if not success:
                print(f"[ERROR] Failed to load IFC file: {message}")
                return False
                
            self.ifc_file = reader.get_ifc_file()
            self.unit_scale = self._get_unit_scale()
            print(f"[OK] IFC file loaded, unit scale: {self.unit_scale}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Exception loading IFC file: {e}")
            return False
    
    def _get_unit_scale(self) -> float:
        """Get unit scale factor to convert to meters"""
        # Check for manual override first
        if self.config.units.unit_scale_to_m is not None:
            return self.config.units.unit_scale_to_m
        
        # Auto-detect if enabled
        if not self.config.units.auto_detect_units:
            return 1.0
        
        try:
            units = self.ifc_file.by_type('IfcUnitAssignment')
            if units:
                for unit in units[0].Units:
                    if hasattr(unit, 'UnitType') and unit.UnitType == 'LENGTHUNIT':
                        if hasattr(unit, 'Name'):
                            if unit.Name == 'METRE':
                                return 1.0
                            elif unit.Name == 'MILLIMETRE':
                                return 0.001
                            elif unit.Name == 'FOOT':
                                return 0.3048
            return 1.0  # Default to meters
        except:
            return 1.0
    
    def get_building_storeys(self) -> List:
        """Get all building storeys from the IFC file"""
        if not self.ifc_file:
            return []
        return self.ifc_file.by_type('IfcBuildingStorey')
    
    def get_storey_elevation(self, storey) -> float:
        """Get elevation of a building storey"""
        try:
            if hasattr(storey, 'Elevation') and storey.Elevation:
                return float(storey.Elevation) * self.unit_scale
            
            # Try to get from placement
            if hasattr(storey, 'ObjectPlacement') and storey.ObjectPlacement:
                placement = storey.ObjectPlacement
                if hasattr(placement, 'RelativePlacement'):
                    rel_placement = placement.RelativePlacement
                    if hasattr(rel_placement, 'Location') and rel_placement.Location:
                        coords = rel_placement.Location.Coordinates
                        if len(coords) >= 3:
                            return float(coords[2]) * self.unit_scale
            
            return 0.0
        except:
            return 0.0
    
    def get_storey_elements(self, storey) -> List:
        """Get all elements contained in a building storey"""
        elements = []
        
        try:
            # Get elements through spatial containment
            if hasattr(storey, 'ContainsElements'):
                for rel in storey.ContainsElements:
                    if hasattr(rel, 'RelatedElements'):
                        elements.extend(rel.RelatedElements)
            
            # Also check for elements that reference this storey
            all_elements = (
                self.ifc_file.by_type('IfcWall') +
                self.ifc_file.by_type('IfcSlab') +
                self.ifc_file.by_type('IfcColumn') +
                self.ifc_file.by_type('IfcBeam') +
                self.ifc_file.by_type('IfcDoor') +
                self.ifc_file.by_type('IfcWindow')
            )
            
            for element in all_elements:
                if self._element_belongs_to_storey(element, storey):
                    if element not in elements:
                        elements.append(element)
                        
        except Exception as e:
            print(f"[WARNING] Error getting storey elements: {e}")
        
        return elements
    
    def _element_belongs_to_storey(self, element, storey) -> bool:
        """Check if an element belongs to a specific storey"""
        try:
            # Check through spatial containment
            if hasattr(element, 'ContainedInStructure'):
                for rel in element.ContainedInStructure:
                    if hasattr(rel, 'RelatingStructure'):
                        if rel.RelatingStructure == storey:
                            return True
            
            # Check through placement hierarchy
            current = element
            while hasattr(current, 'ObjectPlacement') and current.ObjectPlacement:
                placement = current.ObjectPlacement
                if hasattr(placement, 'PlacementRelTo') and placement.PlacementRelTo:
                    rel_to = placement.PlacementRelTo
                    if hasattr(rel_to, 'PlacesObject') and rel_to.PlacesObject:
                        for obj in rel_to.PlacesObject:
                            if obj == storey:
                                return True
                        current = rel_to.PlacesObject[0] if rel_to.PlacesObject else None
                    else:
                        break
                else:
                    break
                    
        except:
            pass
        
        return False
    
    def slice_element_geometry(self, element, cut_height: float) -> SliceResult:
        """Slice an element's geometry at the specified height"""
        lines = []
        element_type = element.is_a()
        element_name = getattr(element, 'Name', '') or f'{element_type}_{element.id()}'
        
        try:
            # Create geometry settings
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, self.config.use_world_coords)
            settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, not self.config.subtract_openings)
            settings.set(settings.SEW_SHELLS, self.config.sew_shells)
            
            # Get element shape
            shape = ifcopenshell.geom.create_shape(settings, element)
            if not shape:
                return SliceResult(lines, element_type, element_name)
            
            # Get vertices and faces
            verts = shape.geometry.verts
            faces = shape.geometry.faces
            
            if not verts or not faces:
                return SliceResult(lines, element_type, element_name)
            
            # Convert vertices to 3D points
            vertices = []
            for i in range(0, len(verts), 3):
                x = verts[i] * self.unit_scale
                y = verts[i + 1] * self.unit_scale
                z = verts[i + 2] * self.unit_scale
                vertices.append((x, y, z))
            
            # Process faces and find intersections with cutting plane
            for i in range(0, len(faces), 3):
                if i + 2 >= len(faces):
                    break
                    
                # Get triangle vertices
                v1_idx, v2_idx, v3_idx = faces[i], faces[i + 1], faces[i + 2]
                if v1_idx >= len(vertices) or v2_idx >= len(vertices) or v3_idx >= len(vertices):
                    continue
                    
                v1, v2, v3 = vertices[v1_idx], vertices[v2_idx], vertices[v3_idx]
                
                # Find intersections with horizontal plane at cut_height
                intersections = self._intersect_triangle_with_plane(v1, v2, v3, cut_height)
                
                if len(intersections) >= 2:
                    # Create line segment from intersections
                    p1, p2 = intersections[0], intersections[1]
                    line = ((p1[0], p1[1]), (p2[0], p2[1]))
                    lines.append(line)
            
        except Exception as e:
            print(f"[WARNING] Error slicing {element_name}: {e}")
        
        return SliceResult(lines, element_type, element_name)
    
    def _intersect_triangle_with_plane(self, v1: Tuple[float, float, float], 
                                     v2: Tuple[float, float, float], 
                                     v3: Tuple[float, float, float], 
                                     plane_z: float) -> List[Tuple[float, float, float]]:
        """Find intersection points between a triangle and a horizontal plane"""
        intersections = []
        edges = [(v1, v2), (v2, v3), (v3, v1)]
        
        for p1, p2 in edges:
            intersection = self._intersect_line_with_plane(p1, p2, plane_z)
            if intersection:
                # Check if intersection is already in list (within tolerance)
                is_duplicate = False
                for existing in intersections:
                    if (abs(existing[0] - intersection[0]) < self.config.slice_tol and
                        abs(existing[1] - intersection[1]) < self.config.slice_tol):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    intersections.append(intersection)
        
        return intersections
    
    def _intersect_line_with_plane(self, p1: Tuple[float, float, float], 
                                 p2: Tuple[float, float, float], 
                                 plane_z: float) -> Optional[Tuple[float, float, float]]:
        """Find intersection point between a line segment and a horizontal plane"""
        z1, z2 = p1[2], p2[2]
        
        # Check if line crosses the plane
        if (z1 <= plane_z <= z2) or (z2 <= plane_z <= z1):
            if abs(z2 - z1) < self.config.slice_tol:
                # Line is parallel to plane
                if abs(z1 - plane_z) < self.config.slice_tol:
                    return p1  # Line lies on plane
                return None
            
            # Calculate intersection point
            t = (plane_z - z1) / (z2 - z1)
            x = p1[0] + t * (p2[0] - p1[0])
            y = p1[1] + t * (p2[1] - p1[1])
            return (x, y, plane_z)
        
        return None
    
    def generate_floor_plan_svg(self, storey, output_path: str) -> bool:
        """Generate SVG floor plan for a specific storey"""
        try:
            storey_name = getattr(storey, 'Name', '') or f'Storey_{storey.id()}'
            elevation = self.get_storey_elevation(storey)
            cut_height = elevation + self.config.cut_offset_m
            
            print(f"\nGenerating floor plan for {storey_name}")
            print(f"  Elevation: {elevation:.2f}m, Cut height: {cut_height:.2f}m")
            
            # Get elements in this storey
            elements = self.get_storey_elements(storey)
            print(f"  Found {len(elements)} elements")
            
            if not elements:
                print(f"  [WARNING] No elements found for {storey_name}")
                return False
            
            # Slice all elements
            all_lines = []
            element_counts = {}
            
            for element in elements:
                slice_result = self.slice_element_geometry(element, cut_height)
                if slice_result.lines:
                    all_lines.extend(slice_result.lines)
                    element_type = slice_result.element_type
                    element_counts[element_type] = element_counts.get(element_type, 0) + 1
            
            print(f"  Element summary: {dict(element_counts)}")
            print(f"  Generated {len(all_lines)} line segments")
            
            if not all_lines:
                print(f"  [WARNING] No geometry lines generated for {storey_name}")
                return False
            
            # Create matplotlib figure for SVG export
            fig, ax = plt.subplots(1, 1, figsize=(16, 12))
            
            # Draw all lines
            for line in all_lines:
                (x1, y1), (x2, y2) = line
                
                if self.config.invert_y:
                    y1, y2 = -y1, -y2
                
                ax.plot([x1, x2], [y1, y2], 
                       color=self.config.color_hex, 
                       linewidth=self.config.linewidth_px)
            
            # Set up the plot
            ax.set_aspect('equal')
            ax.set_title(f'Floor Plan: {storey_name} (Elevation: {elevation:.2f}m)')
            ax.set_xlabel('X (meters)')
            ax.set_ylabel('Y (meters)')
            ax.grid(True, alpha=0.3)
            
            # Save as SVG
            plt.tight_layout()
            plt.savefig(output_path, format='svg', bbox_inches='tight', dpi=150)
            plt.close()
            
            print(f"  [OK] Floor plan saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"  [ERROR] Failed to generate floor plan: {e}")
            return False
    
    def generate_all_floor_plans(self, output_dir: str = "floor_plans") -> int:
        """Generate floor plans for all building storeys"""
        if not self.ifc_file:
            print("[ERROR] No IFC file loaded")
            return 0
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all building storeys
        storeys = self.get_building_storeys()
        print(f"[OK] Found {len(storeys)} building storeys")
        
        if not storeys:
            print("[WARNING] No building storeys found in IFC file")
            return 0
        
        # Generate floor plan for each storey
        success_count = 0
        for i, storey in enumerate(storeys):
            storey_name = getattr(storey, 'Name', '') or f'Storey_{storey.id()}'
            safe_name = "".join(c for c in storey_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_path = os.path.join(output_dir, f"{safe_name}_floor_plan.svg")
            
            if self.generate_floor_plan_svg(storey, output_path):
                success_count += 1
        
        print(f"\n[OK] Generated {success_count}/{len(storeys)} floor plans")
        return success_count

def main():
    """Main function to demonstrate floor plan generation"""
    print("IFC Floor Plan Generator")
    print("=" * 50)
    
    # Configuration
    config = FloorPlanConfig(
        cut_offset_m=1.10,
        use_world_coords=True,
        subtract_openings=True,
        linewidth_px=0.8,
        color_hex="#000000"
    )
    
    # Create generator
    generator = IFCFloorPlanGenerator(config)
    
    # Load IFC file
    ifc_file_path = "tesfiler/DEICH_Test.ifc"
    if not generator.load_ifc_file(ifc_file_path):
        return
    
    # Generate all floor plans
    success_count = generator.generate_all_floor_plans("floor_plans")
    
    if success_count > 0:
        print(f"\n[SUCCESS] Generated {success_count} floor plan(s)")
        print("Check the 'floor_plans' directory for SVG files")
    else:
        print("\n[ERROR] No floor plans were generated")

if __name__ == "__main__":
    main()