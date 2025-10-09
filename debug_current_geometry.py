#!/usr/bin/env python3
"""
Debug script to visualize the current geometry extraction results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
import numpy as np

def debug_current_geometry():
    """Debug the current geometry extraction with visualization."""
    
    print("Debugging current geometry extraction...")
    print("=" * 60)
    
    # Load IFC file
    ifc_file_path = "tesfiler/DEICH_Test.ifc"
    reader = IfcFileReader()
    success, message = reader.load_file(ifc_file_path)
    
    if not success:
        print(f"[ERROR] Failed to load IFC file: {message}")
        return
    
    print("[OK] IFC file loaded")
    ifc_file = reader.get_ifc_file()
    
    # Extract spaces
    extractor = IfcSpaceExtractor()
    spaces = extractor.extract_spaces(ifc_file)
    print(f"[OK] Found {len(spaces)} spaces")
    
    # Extract geometry
    geom_extractor = GeometryExtractor()
    
    # Process first 10 spaces for detailed analysis
    sample_spaces = spaces[:10]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(sample_spaces)))
    
    print(f"\nAnalyzing first {len(sample_spaces)} spaces:")
    print("-" * 50)
    
    for i, space in enumerate(sample_spaces):
        space_name = getattr(space, 'Name', f'Space_{i}') or f'Space_{i}'
        space_guid = getattr(space, 'GlobalId', f'guid_{i}')
        
        print(f"\n{i+1}. {space_name} ({space_guid})")
        
        # Extract polygons
        polygons = geom_extractor.extract_space_boundaries(space)
        
        if polygons:
            polygon = polygons[0]  # Use first polygon
            points = polygon.points
            
            print(f"   - Points: {len(points)}")
            print(f"   - Area: {polygon.get_area():.1f} m2")
            
            # Get bounds
            x_coords = [p.x for p in points]
            y_coords = [p.y for p in points]
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            print(f"   - Bounds: ({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f})")
            print(f"   - Dimensions: {max_x-min_x:.1f} x {max_y-min_y:.1f} m")
            print(f"   - Center: ({(min_x+max_x)/2:.1f}, {(min_y+max_y)/2:.1f})")
            
            # Plot on both axes
            for ax in [ax1, ax2]:
                # Create polygon patch
                xy_points = [(p.x, p.y) for p in points]
                poly_patch = patches.Polygon(xy_points, 
                                           facecolor=colors[i], 
                                           edgecolor='black', 
                                           alpha=0.7,
                                           linewidth=1)
                ax.add_patch(poly_patch)
                
                # Add label at center
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
                ax.text(center_x, center_y, space_name, 
                       ha='center', va='center', fontsize=8, 
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        else:
            print(f"   - No geometry extracted")
    
    # Set up axes
    ax1.set_title("Room Layout - Overview")
    ax1.set_xlabel("X (meters)")
    ax1.set_ylabel("Y (meters)")
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')
    
    ax2.set_title("Room Layout - Zoomed")
    ax2.set_xlabel("X (meters)")
    ax2.set_ylabel("Y (meters)")
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')
    
    # Auto-scale axes
    ax1.autoscale()
    ax2.autoscale()
    
    # Zoom ax2 to show potential overlaps better
    if sample_spaces:
        # Find the area with most rooms for zooming
        all_centers = []
        for space in sample_spaces:
            polygons = geom_extractor.extract_space_boundaries(space)
            if polygons:
                polygon = polygons[0]
                points = polygon.points
                x_coords = [p.x for p in points]
                y_coords = [p.y for p in points]
                center_x = (min(x_coords) + max(x_coords)) / 2
                center_y = (min(y_coords) + max(y_coords)) / 2
                all_centers.append((center_x, center_y))
        
        if all_centers:
            # Find center of all centers
            avg_x = sum(c[0] for c in all_centers) / len(all_centers)
            avg_y = sum(c[1] for c in all_centers) / len(all_centers)
            
            # Set zoom window around this center
            zoom_size = 50  # 50 meter window
            ax2.set_xlim(avg_x - zoom_size, avg_x + zoom_size)
            ax2.set_ylim(avg_y - zoom_size, avg_y + zoom_size)
    
    plt.tight_layout()
    plt.savefig('debug_current_geometry.png', dpi=150, bbox_inches='tight')
    print(f"\n[OK] Visualization saved as 'debug_current_geometry.png'")
    
    # Check for overlaps
    print(f"\nChecking for overlaps among sample spaces...")
    overlaps = []
    
    for i, space1 in enumerate(sample_spaces):
        polygons1 = geom_extractor.extract_space_boundaries(space1)
        if not polygons1:
            continue
            
        name1 = getattr(space1, 'Name', f'Space_{i}') or f'Space_{i}'
        poly1 = polygons1[0]
        center1 = poly1.get_center()
        
        for j, space2 in enumerate(sample_spaces[i+1:], i+1):
            polygons2 = geom_extractor.extract_space_boundaries(space2)
            if not polygons2:
                continue
                
            name2 = getattr(space2, 'Name', f'Space_{j}') or f'Space_{j}'
            poly2 = polygons2[0]
            center2 = poly2.get_center()
            
            # Calculate distance between centers
            distance = ((center1.x - center2.x)**2 + (center1.y - center2.y)**2)**0.5
            
            # If centers are very close, likely overlapping
            if distance < 5.0:  # Less than 5 meters apart
                overlaps.append((name1, name2, distance))
    
    if overlaps:
        print(f"[WARNING] Found {len(overlaps)} potential overlaps:")
        for name1, name2, dist in overlaps:
            print(f"   - {name1} <-> {name2}: {dist:.1f}m apart")
    else:
        print("[OK] No obvious overlaps detected in sample")
    
    plt.show()

if __name__ == "__main__":
    debug_current_geometry()