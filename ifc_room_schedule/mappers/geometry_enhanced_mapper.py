"""
Geometry Enhanced Mapper

Maps IFC Space geometry to enhanced room schedule geometry section with intelligent estimation.
"""

import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from ..data.space_model import SpaceData


@dataclass
class GeometryData:
    """Enhanced geometry data for room schedule."""
    
    # Basic dimensions
    length_m: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None
    
    # Calculated areas
    net_floor_area_m2: Optional[float] = None
    gross_floor_area_m2: Optional[float] = None
    wall_area_m2: Optional[float] = None
    ceiling_area_m2: Optional[float] = None
    
    # Calculated volumes
    net_volume_m3: Optional[float] = None
    gross_volume_m3: Optional[float] = None
    
    # Room properties
    room_origin: Optional[Dict[str, float]] = None
    room_orientation_deg: Optional[float] = None
    room_shape_type: Optional[str] = None
    room_aspect_ratio: Optional[float] = None
    
    # Accessibility
    clear_width_m: Optional[float] = None
    clear_height_m: Optional[float] = None
    turning_radius_m: Optional[float] = None
    
    # Estimation flags
    estimated_dimensions: bool = False
    estimation_confidence: float = 0.0
    estimation_method: Optional[str] = None


@dataclass
class RoomShapeAnalysis:
    """Analysis of room shape and proportions."""
    
    shape_type: str  # "rectangular", "irregular", "circular", "L-shaped", etc.
    aspect_ratio: float
    perimeter_m: float
    compactness: float  # Area/perimeter ratio
    is_regular: bool
    estimated_dimensions: Dict[str, float]


class GeometryEnhancedMapper:
    """Maps IFC Space geometry to enhanced room schedule geometry section."""
    
    def __init__(self):
        """Initialize GeometryEnhancedMapper."""
        self.default_ceiling_height = 3.0  # meters
        self.min_room_dimension = 1.5  # meters
        self.max_room_dimension = 20.0  # meters
        self.typical_aspect_ratios = {
            "rectangular": 1.2,  # 1.2:1 ratio
            "square": 1.0,
            "long_narrow": 2.5,
            "wide_shallow": 0.4
        }
    
    def calculate_enhanced_geometry(self, space: SpaceData) -> GeometryData:
        """
        Calculate enhanced geometry from IFC Space data.
        
        Args:
            space: SpaceData to calculate geometry for
            
        Returns:
            GeometryData with enhanced calculations
        """
        # Extract basic area information
        net_area = space.quantities.get("NetFloorArea") if space.quantities else None
        gross_area = space.quantities.get("GrossFloorArea") if space.quantities else None
        
        # Calculate dimensions
        dimensions = self._calculate_room_dimensions(net_area or gross_area)
        
        # Calculate areas
        areas = self._calculate_room_areas(net_area, gross_area, dimensions)
        
        # Calculate volumes
        volumes = self._calculate_room_volumes(areas, dimensions)
        
        # Analyze room shape
        shape_analysis = self._analyze_room_shape(areas["net_floor_area"], dimensions)
        
        # Calculate room properties
        room_origin = self._calculate_room_origin(space)
        room_orientation = self._calculate_room_orientation(space)
        
        # Calculate accessibility metrics
        accessibility = self._calculate_accessibility_metrics(dimensions, shape_analysis)
        
        # Determine estimation status
        estimated_dimensions = dimensions["estimated"]
        estimation_confidence = self._calculate_estimation_confidence(space, dimensions)
        estimation_method = self._determine_estimation_method(space, dimensions)
        
        return GeometryData(
            length_m=dimensions["length"],
            width_m=dimensions["width"],
            height_m=dimensions["height"],
            net_floor_area_m2=areas["net_floor_area"],
            gross_floor_area_m2=areas["gross_floor_area"],
            wall_area_m2=areas["wall_area"],
            ceiling_area_m2=areas["ceiling_area"],
            net_volume_m3=volumes["net_volume"],
            gross_volume_m3=volumes["gross_volume"],
            room_origin=room_origin,
            room_orientation_deg=room_orientation,
            room_shape_type=shape_analysis.shape_type,
            room_aspect_ratio=shape_analysis.aspect_ratio,
            clear_width_m=accessibility["clear_width"],
            clear_height_m=accessibility["clear_height"],
            turning_radius_m=accessibility["turning_radius"],
            estimated_dimensions=estimated_dimensions,
            estimation_confidence=estimation_confidence,
            estimation_method=estimation_method
        )
    
    def estimate_missing_dimensions(self, space: SpaceData) -> Dict[str, Any]:
        """
        Estimate missing dimensions based on area and room type.
        
        Args:
            space: SpaceData to estimate dimensions for
            
        Returns:
            Dictionary with estimated dimensions and confidence
        """
        net_area = space.quantities.get("NetFloorArea") if space.quantities else None
        gross_area = space.quantities.get("GrossFloorArea") if space.quantities else None
        area = net_area or gross_area
        
        if not area:
            return {
                "estimated": False,
                "confidence": 0.0,
                "method": "no_area_data",
                "dimensions": None
            }
        
        # Determine room type for estimation
        room_type = self._infer_room_type_from_name(space.name)
        
        # Estimate dimensions based on room type and area
        if room_type in ["bathroom", "wc", "utility"]:
            # Small rooms - typically square or rectangular
            estimated_dims = self._estimate_small_room_dimensions(area)
        elif room_type in ["bedroom", "office"]:
            # Medium rooms - rectangular with good proportions
            estimated_dims = self._estimate_medium_room_dimensions(area)
        elif room_type in ["living", "kitchen", "dining"]:
            # Large rooms - can be more varied
            estimated_dims = self._estimate_large_room_dimensions(area)
        else:
            # Generic estimation
            estimated_dims = self._estimate_generic_room_dimensions(area)
        
        # Calculate confidence based on area and room type
        confidence = self._calculate_estimation_confidence(space, estimated_dims)
        
        return {
            "estimated": True,
            "confidence": confidence,
            "method": f"area_based_{room_type}",
            "dimensions": estimated_dims
        }
    
    def extract_room_local_origin(self, space: SpaceData) -> Dict[str, float]:
        """
        Extract room local origin from IFC placement.
        
        Args:
            space: SpaceData to extract origin from
            
        Returns:
            Dictionary with local origin coordinates
        """
        # In a real implementation, this would parse IFC placement matrix
        # For now, return default origin
        return {
            "x": 0.0,
            "y": 0.0,
            "z": space.elevation or 0.0
        }
    
    def _calculate_room_dimensions(self, area: Optional[float]) -> Dict[str, Any]:
        """Calculate room dimensions from area."""
        if not area:
            return {
                "length": None,
                "width": None,
                "height": self.default_ceiling_height,
                "estimated": True
            }
        
        # Estimate dimensions from area
        # Assume rectangular room with reasonable aspect ratio
        aspect_ratio = self.typical_aspect_ratios["rectangular"]
        
        # Calculate width and length
        width = math.sqrt(area / aspect_ratio)
        length = area / width
        
        # Ensure reasonable dimensions
        width = max(self.min_room_dimension, min(width, self.max_room_dimension))
        length = max(self.min_room_dimension, min(length, self.max_room_dimension))
        
        return {
            "length": length,
            "width": width,
            "height": self.default_ceiling_height,
            "estimated": True
        }
    
    def _calculate_room_areas(self, net_area: Optional[float], gross_area: Optional[float], 
                             dimensions: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all room areas."""
        areas = {}
        
        # Floor areas
        areas["net_floor_area"] = net_area or 0.0
        areas["gross_floor_area"] = gross_area or net_area or 0.0
        
        # Wall area (perimeter * height)
        if dimensions["length"] and dimensions["width"] and dimensions["height"]:
            perimeter = 2 * (dimensions["length"] + dimensions["width"])
            areas["wall_area"] = perimeter * dimensions["height"]
        else:
            areas["wall_area"] = 0.0
        
        # Ceiling area (same as floor area)
        areas["ceiling_area"] = areas["net_floor_area"]
        
        return areas
    
    def _calculate_room_volumes(self, areas: Dict[str, float], dimensions: Dict[str, Any]) -> Dict[str, float]:
        """Calculate room volumes."""
        volumes = {}
        
        # Net volume
        if areas["net_floor_area"] and dimensions["height"]:
            volumes["net_volume"] = areas["net_floor_area"] * dimensions["height"]
        else:
            volumes["net_volume"] = 0.0
        
        # Gross volume
        if areas["gross_floor_area"] and dimensions["height"]:
            volumes["gross_volume"] = areas["gross_floor_area"] * dimensions["height"]
        else:
            volumes["gross_volume"] = volumes["net_volume"]
        
        return volumes
    
    def _analyze_room_shape(self, area: float, dimensions: Dict[str, Any]) -> RoomShapeAnalysis:
        """Analyze room shape and proportions."""
        if not dimensions["length"] or not dimensions["width"]:
            return RoomShapeAnalysis(
                shape_type="unknown",
                aspect_ratio=1.0,
                perimeter_m=0.0,
                compactness=0.0,
                is_regular=False,
                estimated_dimensions={}
            )
        
        length = dimensions["length"]
        width = dimensions["width"]
        aspect_ratio = length / width if width > 0 else 1.0
        
        # Determine shape type
        if 0.9 <= aspect_ratio <= 1.1:
            shape_type = "square"
        elif 1.1 < aspect_ratio <= 1.5:
            shape_type = "rectangular"
        elif aspect_ratio > 2.0:
            shape_type = "long_narrow"
        elif aspect_ratio < 0.5:
            shape_type = "wide_shallow"
        else:
            shape_type = "rectangular"
        
        # Calculate perimeter and compactness
        perimeter = 2 * (length + width)
        compactness = area / perimeter if perimeter > 0 else 0.0
        
        # Determine if regular
        is_regular = shape_type in ["square", "rectangular"]
        
        return RoomShapeAnalysis(
            shape_type=shape_type,
            aspect_ratio=aspect_ratio,
            perimeter_m=perimeter,
            compactness=compactness,
            is_regular=is_regular,
            estimated_dimensions=dimensions
        )
    
    def _calculate_room_origin(self, space: SpaceData) -> Dict[str, float]:
        """Calculate room origin coordinates."""
        return self.extract_room_local_origin(space)
    
    def _calculate_room_orientation(self, space: SpaceData) -> Optional[float]:
        """Calculate room orientation in degrees."""
        # In a real implementation, this would parse IFC placement matrix
        # For now, return default orientation
        return 0.0
    
    def _calculate_accessibility_metrics(self, dimensions: Dict[str, Any], 
                                       shape_analysis: RoomShapeAnalysis) -> Dict[str, float]:
        """Calculate accessibility metrics."""
        accessibility = {}
        
        # Clear width (minimum of length and width)
        if dimensions["length"] and dimensions["width"]:
            accessibility["clear_width"] = min(dimensions["length"], dimensions["width"])
        else:
            accessibility["clear_width"] = 0.0
        
        # Clear height (ceiling height minus any obstructions)
        accessibility["clear_height"] = dimensions["height"] or self.default_ceiling_height
        
        # Turning radius (minimum for wheelchair access)
        accessibility["turning_radius"] = 1.5  # meters (TEK17 requirement)
        
        return accessibility
    
    def _calculate_estimation_confidence(self, space: SpaceData, dimensions: Dict[str, Any]) -> float:
        """Calculate confidence in dimension estimation."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have area data
        if space.quantities and space.quantities.get("NetFloorArea"):
            confidence += 0.3
        
        # Increase confidence if room name suggests specific type
        room_type = self._infer_room_type_from_name(space.name)
        if room_type != "unknown":
            confidence += 0.2
        
        # Decrease confidence if dimensions seem unreasonable
        if dimensions["length"] and dimensions["width"]:
            aspect_ratio = dimensions["length"] / dimensions["width"]
            if aspect_ratio > 5.0 or aspect_ratio < 0.2:
                confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _determine_estimation_method(self, space: SpaceData, dimensions: Dict[str, Any]) -> str:
        """Determine the method used for dimension estimation."""
        if space.quantities and space.quantities.get("NetFloorArea"):
            return "area_based_estimation"
        elif space.name:
            return "name_based_inference"
        else:
            return "default_assumptions"
    
    def _infer_room_type_from_name(self, name: str) -> str:
        """Infer room type from name for estimation purposes."""
        if not name:
            return "unknown"
        
        name_lower = name.lower()
        
        if any(word in name_lower for word in ["bad", "våtrom", "bath", "wc", "toalett"]):
            return "bathroom"
        elif any(word in name_lower for word in ["soverom", "bedroom", "rom"]):
            return "bedroom"
        elif any(word in name_lower for word in ["stue", "living", "opphold"]):
            return "living"
        elif any(word in name_lower for word in ["kjøkken", "kitchen"]):
            return "kitchen"
        elif any(word in name_lower for word in ["kontor", "office"]):
            return "office"
        else:
            return "unknown"
    
    def _estimate_small_room_dimensions(self, area: float) -> Dict[str, Any]:
        """Estimate dimensions for small rooms (bathrooms, etc.)."""
        # Small rooms are typically square or slightly rectangular
        side_length = math.sqrt(area)
        return {
            "length": side_length,
            "width": side_length,
            "height": self.default_ceiling_height,
            "estimated": True
        }
    
    def _estimate_medium_room_dimensions(self, area: float) -> Dict[str, Any]:
        """Estimate dimensions for medium rooms (bedrooms, offices)."""
        # Medium rooms with good proportions
        aspect_ratio = self.typical_aspect_ratios["rectangular"]
        width = math.sqrt(area / aspect_ratio)
        length = area / width
        return {
            "length": length,
            "width": width,
            "height": self.default_ceiling_height,
            "estimated": True
        }
    
    def _estimate_large_room_dimensions(self, area: float) -> Dict[str, Any]:
        """Estimate dimensions for large rooms (living rooms, etc.)."""
        # Large rooms can be more varied
        aspect_ratio = self.typical_aspect_ratios["rectangular"]
        width = math.sqrt(area / aspect_ratio)
        length = area / width
        return {
            "length": length,
            "width": width,
            "height": self.default_ceiling_height,
            "estimated": True
        }
    
    def _estimate_generic_room_dimensions(self, area: float) -> Dict[str, Any]:
        """Estimate dimensions for generic rooms."""
        return self._estimate_medium_room_dimensions(area)


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
        ),
        SpaceData(
            guid="GUID-UNKNOWN-001",
            name="Unknown Room",
            description="Room without area data",
            object_type="IfcSpace",
            zone_category="Residential",
            number="001",
            elevation=6.0,
            quantities={}
        )
    ]
    
    mapper = GeometryEnhancedMapper()
    
    print("Geometry Enhanced Mapper Test Results:")
    print("=" * 60)
    
    for i, space in enumerate(test_spaces, 1):
        print(f"\n--- Test Space {i}: {space.name} ---")
        
        # Calculate enhanced geometry
        geometry = mapper.calculate_enhanced_geometry(space)
        
        print(f"Length: {geometry.length_m:.2f}m")
        print(f"Width: {geometry.width_m:.2f}m")
        print(f"Height: {geometry.height_m:.2f}m")
        print(f"Net Area: {geometry.net_floor_area_m2:.2f}m²")
        print(f"Gross Area: {geometry.gross_floor_area_m2:.2f}m²")
        print(f"Wall Area: {geometry.wall_area_m2:.2f}m²")
        print(f"Net Volume: {geometry.net_volume_m3:.2f}m³")
        print(f"Shape Type: {geometry.room_shape_type}")
        print(f"Aspect Ratio: {geometry.room_aspect_ratio:.2f}")
        print(f"Clear Width: {geometry.clear_width_m:.2f}m")
        print(f"Estimated: {geometry.estimated_dimensions}")
        print(f"Confidence: {geometry.estimation_confidence:.2f}")
        print(f"Method: {geometry.estimation_method}")
        
        # Test missing dimension estimation
        estimation = mapper.estimate_missing_dimensions(space)
        print(f"Estimation Confidence: {estimation['confidence']:.2f}")
        print(f"Estimation Method: {estimation['method']}")
