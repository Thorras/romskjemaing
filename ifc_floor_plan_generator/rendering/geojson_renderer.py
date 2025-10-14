"""
GeoJSON renderer for IFC Floor Plan Generator.

Renders polylines to GeoJSON format with semantic metadata and Norwegian category mapping.
"""

import json
import logging
from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING
from ..models import Polyline2D
from ..errors.handler import ErrorHandler
from ..errors.exceptions import ProcessingError

if TYPE_CHECKING:
    from ..models import Config


class GeoJSONRenderer:
    """Renders polylines to GeoJSON format with semantic metadata."""
    
    # Norwegian category mapping for IFC classes
    IFC_CATEGORY_MAPPING = {
        # Structural elements
        "IfcWall": "Vegg",
        "IfcWallStandardCase": "Vegg",
        "IfcColumn": "Søyle",
        "IfcBeam": "Bjelke",
        "IfcSlab": "Dekke",
        "IfcRoof": "Tak",
        "IfcStair": "Trapp",
        "IfcRamp": "Rampe",
        "IfcFooting": "Fundament",
        "IfcPile": "Pæl",
        
        # Openings and fillings
        "IfcDoor": "Dør",
        "IfcWindow": "Vindu",
        "IfcOpeningElement": "Åpning",
        
        # Building service elements
        "IfcPipeSegment": "Rør",
        "IfcDuctSegment": "Kanal",
        "IfcCableSegment": "Kabel",
        "IfcFlowTerminal": "Terminal",
        "IfcFlowFitting": "Rørkobbling",
        
        # Furnishing elements
        "IfcFurnishingElement": "Møbel",
        "IfcSystemFurnitureElement": "Systemmøbel",
        
        # Distribution elements
        "IfcDistributionElement": "Distribusjonselement",
        "IfcDistributionFlowElement": "Strømningselement",
        
        # Building elements
        "IfcBuildingElement": "Bygningselement",
        "IfcBuildingElementProxy": "Bygningselement (proxy)",
        
        # Spaces and zones
        "IfcSpace": "Rom",
        "IfcZone": "Sone",
        
        # Generic elements
        "IfcElement": "Element",
        "IfcElementAssembly": "Elementsamling",
        "IfcElementComponent": "Elementkomponent",
        
        # Transportation elements
        "IfcTransportElement": "Transportelement",
        
        # Virtual elements
        "IfcVirtualElement": "Virtuelt element",
        
        # Covering elements
        "IfcCovering": "Dekke/belegg",
        
        # Curtain walls
        "IfcCurtainWall": "Fasadevegg",
        "IfcPlate": "Plate",
        "IfcMember": "Profil",
        
        # Reinforcement
        "IfcReinforcingElement": "Armering",
        "IfcReinforcingBar": "Armeringsjern",
        "IfcReinforcingMesh": "Armeringsnett",
        
        # Fasteners
        "IfcFastener": "Festeelement",
        "IfcMechanicalFastener": "Mekanisk festeelement",
        
        # Chimneys and shafts
        "IfcChimney": "Skorstein",
        "IfcShadingDevice": "Solskjerming"
    }
    
    def __init__(self, config: Optional['Config'] = None):
        """Initialize GeoJSON renderer with optional configuration.
        
        Args:
            config: Main configuration object containing output settings
        """
        self.config = config
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
    
    def render_polylines(self, polylines: List[Polyline2D], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Render polylines to GeoJSON dictionary.
        
        Args:
            polylines: List of polylines to render
            metadata: Additional metadata for the GeoJSON (storey info, etc.)
            
        Returns:
            Dict[str, Any]: Complete GeoJSON FeatureCollection
            
        Raises:
            ProcessingError: If GeoJSON generation fails
        """
        try:
            if not polylines:
                self._logger.warning("No polylines to render to GeoJSON")
                return self._create_empty_geojson(metadata)
            
            # Create GeoJSON FeatureCollection
            geojson = {
                "type": "FeatureCollection",
                "features": [],
                "properties": self._create_collection_properties(metadata)
            }
            
            # Convert each polyline to a GeoJSON feature
            for i, polyline in enumerate(polylines):
                try:
                    feature = self._polyline_to_feature(polyline, metadata, i)
                    if feature:
                        geojson["features"].append(feature)
                except Exception as e:
                    self._logger.warning(f"Failed to convert polyline {i} to GeoJSON feature: {e}")
                    continue
            
            self._logger.debug(f"Successfully rendered {len(polylines)} polylines to GeoJSON with {len(geojson['features'])} features")
            return geojson
            
        except Exception as e:
            self._logger.error(f"GeoJSON rendering failed: {e}")
            raise ProcessingError(
                error_code="GEOJSON_RENDER_FAILED",
                message=f"GeoJSON-rendering feilet: {str(e)}",
                context={"error": str(e), "polyline_count": len(polylines)}
            )
    
    def create_feature_properties(self, ifc_class: str, storey_name: str) -> Dict[str, Any]:
        """Create GeoJSON feature properties with semantic metadata.
        
        Args:
            ifc_class: IFC class of the element
            storey_name: Name of the building storey
            
        Returns:
            Dict[str, Any]: Properties dictionary with semantic metadata
        """
        properties = {
            "ifc_class": ifc_class,
            "storey_name": storey_name,
            "category": self._get_norwegian_category(ifc_class),
            "element_type": self._get_element_type(ifc_class)
        }
        
        # Add semantic metadata
        properties = self.add_semantic_metadata(properties)
        
        return properties
    
    def add_semantic_metadata(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Add Norwegian category mapping and semantic metadata.
        
        Args:
            properties: Existing properties dictionary
            
        Returns:
            Dict[str, Any]: Properties with added semantic metadata
        """
        ifc_class = properties.get("ifc_class", "")
        
        # Add structural classification
        properties["is_structural"] = self._is_structural_element(ifc_class)
        properties["is_opening"] = self._is_opening_element(ifc_class)
        properties["is_building_service"] = self._is_building_service_element(ifc_class)
        properties["is_furnishing"] = self._is_furnishing_element(ifc_class)
        
        # Add geometric classification
        properties["geometry_type"] = "LineString"  # All our polylines become LineStrings
        
        # Add Norwegian descriptions
        properties["beskrivelse"] = self._get_norwegian_description(ifc_class)
        properties["kategori_gruppe"] = self._get_category_group(ifc_class)
        
        return properties
    
    def _polyline_to_feature(self, polyline: Polyline2D, metadata: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Convert a polyline to a GeoJSON feature.
        
        Args:
            polyline: Polyline to convert
            metadata: Metadata for the feature
            index: Index of the polyline
            
        Returns:
            Optional[Dict[str, Any]]: GeoJSON feature or None if conversion fails
        """
        if len(polyline.points) < 2:
            self._logger.debug(f"Skipping polyline {index} with insufficient points ({len(polyline.points)})")
            return None
        
        try:
            # Convert points to GeoJSON coordinates
            coordinates = self._points_to_geojson_coordinates(polyline.points, polyline.is_closed)
            
            # Create geometry
            if polyline.is_closed and len(polyline.points) > 2:
                # Closed polylines become Polygons
                geometry = {
                    "type": "Polygon",
                    "coordinates": [coordinates]
                }
            else:
                # Open polylines become LineStrings
                geometry = {
                    "type": "LineString", 
                    "coordinates": coordinates
                }
            
            # Create enhanced properties with all required semantic metadata
            storey_name = metadata.get("storey_name", "Unknown")
            additional_metadata = {
                "is_closed": polyline.is_closed,
                "point_count": len(polyline.points),
                "feature_index": index
            }
            
            # Enhance metadata with configuration information
            enhanced_metadata = self.enhance_metadata_with_config(metadata)
            additional_metadata.update(enhanced_metadata.get("config_info", {}))
            
            properties = self.create_enhanced_feature_properties(
                polyline.ifc_class, 
                storey_name, 
                polyline.element_guid,
                additional_metadata
            )
            
            # Create feature
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
                "id": f"{polyline.element_guid}_{index}"
            }
            
            return feature
            
        except Exception as e:
            self._logger.warning(f"Failed to create GeoJSON feature for polyline {index}: {e}")
            return None
    
    def _points_to_geojson_coordinates(self, points: List[Tuple[float, float]], is_closed: bool) -> List[List[float]]:
        """Convert polyline points to GeoJSON coordinates.
        
        Args:
            points: List of 2D points
            is_closed: Whether the polyline is closed
            
        Returns:
            List[List[float]]: GeoJSON coordinates array
        """
        # Convert to GeoJSON coordinate format [longitude, latitude] or [x, y]
        coordinates = [[float(x), float(y)] for x, y in points]
        
        # For closed polygons, ensure the first and last points are the same
        if is_closed and len(coordinates) > 2:
            if coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])
        
        return coordinates
    
    def _get_norwegian_category(self, ifc_class: str) -> str:
        """Get Norwegian category name for IFC class.
        
        Args:
            ifc_class: IFC class name
            
        Returns:
            str: Norwegian category name
        """
        return self.IFC_CATEGORY_MAPPING.get(ifc_class, ifc_class)
    
    def _get_element_type(self, ifc_class: str) -> str:
        """Get general element type classification.
        
        Args:
            ifc_class: IFC class name
            
        Returns:
            str: Element type classification
        """
        if self._is_structural_element(ifc_class):
            return "Structural"
        elif self._is_opening_element(ifc_class):
            return "Opening"
        elif self._is_building_service_element(ifc_class):
            return "Building Service"
        elif self._is_furnishing_element(ifc_class):
            return "Furnishing"
        else:
            return "Other"
    
    def _is_structural_element(self, ifc_class: str) -> bool:
        """Check if IFC class represents a structural element."""
        structural_classes = {
            "IfcWall", "IfcWallStandardCase", "IfcColumn", "IfcBeam", 
            "IfcSlab", "IfcFooting", "IfcPile", "IfcRoof"
        }
        return ifc_class in structural_classes
    
    def _is_opening_element(self, ifc_class: str) -> bool:
        """Check if IFC class represents an opening element."""
        opening_classes = {
            "IfcDoor", "IfcWindow", "IfcOpeningElement"
        }
        return ifc_class in opening_classes
    
    def _is_building_service_element(self, ifc_class: str) -> bool:
        """Check if IFC class represents a building service element."""
        service_classes = {
            "IfcPipeSegment", "IfcDuctSegment", "IfcCableSegment",
            "IfcFlowTerminal", "IfcFlowFitting", "IfcDistributionElement",
            "IfcDistributionFlowElement"
        }
        return ifc_class in service_classes
    
    def _is_furnishing_element(self, ifc_class: str) -> bool:
        """Check if IFC class represents a furnishing element."""
        furnishing_classes = {
            "IfcFurnishingElement", "IfcSystemFurnitureElement"
        }
        return ifc_class in furnishing_classes
    
    def _get_norwegian_description(self, ifc_class: str) -> str:
        """Get detailed Norwegian description for IFC class.
        
        Args:
            ifc_class: IFC class name
            
        Returns:
            str: Norwegian description
        """
        descriptions = {
            "IfcWall": "Bærende eller ikke-bærende vegg",
            "IfcWallStandardCase": "Standard vegg med rett geometri",
            "IfcColumn": "Vertikal bærende konstruksjon",
            "IfcBeam": "Horisontal bærende konstruksjon",
            "IfcSlab": "Horisontal plate eller dekke",
            "IfcDoor": "Døråpning med dørblad",
            "IfcWindow": "Vindusåpning med vindusramme",
            "IfcStair": "Trappekonstruksjon",
            "IfcRamp": "Rampekonstruksjon",
            "IfcSpace": "Definert romområde",
            "IfcRoof": "Takkonstruksjon"
        }
        return descriptions.get(ifc_class, f"IFC element av type {ifc_class}")
    
    def _get_category_group(self, ifc_class: str) -> str:
        """Get category group for IFC class.
        
        Args:
            ifc_class: IFC class name
            
        Returns:
            str: Category group name in Norwegian
        """
        if self._is_structural_element(ifc_class):
            return "Bærekonstruksjon"
        elif self._is_opening_element(ifc_class):
            return "Åpninger"
        elif self._is_building_service_element(ifc_class):
            return "Tekniske installasjoner"
        elif self._is_furnishing_element(ifc_class):
            return "Innredning"
        else:
            return "Øvrige elementer"
    
    def _create_collection_properties(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create properties for the GeoJSON FeatureCollection.
        
        Args:
            metadata: Metadata for the collection
            
        Returns:
            Dict[str, Any]: Collection properties
        """
        return {
            "generator": "IFC Floor Plan Generator",
            "storey_name": metadata.get("storey_name", "Unknown"),
            "cut_height": metadata.get("cut_height", 0.0),
            "created_at": metadata.get("created_at", ""),
            "coordinate_system": "Local building coordinates",
            "units": "meters"
        }
    
    def _create_empty_geojson(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create empty GeoJSON FeatureCollection.
        
        Args:
            metadata: Metadata for the collection
            
        Returns:
            Dict[str, Any]: Empty GeoJSON FeatureCollection
        """
        return {
            "type": "FeatureCollection",
            "features": [],
            "properties": self._create_collection_properties(metadata)
        }
    
    def render_to_string(self, polylines: List[Polyline2D], metadata: Dict[str, Any], 
                        indent: Optional[int] = 2) -> str:
        """Render polylines to GeoJSON string.
        
        Args:
            polylines: List of polylines to render
            metadata: Metadata for the GeoJSON
            indent: JSON indentation (None for compact output)
            
        Returns:
            str: GeoJSON as formatted string
            
        Raises:
            ProcessingError: If GeoJSON generation fails
        """
        geojson_dict = self.render_polylines(polylines, metadata)
        
        try:
            return json.dumps(geojson_dict, indent=indent, ensure_ascii=False)
        except Exception as e:
            raise ProcessingError(
                error_code="GEOJSON_SERIALIZE_FAILED",
                message=f"GeoJSON serialisering feilet: {str(e)}",
                context={"error": str(e)}
            )
    
    def render_and_save(self, polylines: List[Polyline2D], output_manager, 
                       storey_name: str, index: int, metadata: Dict[str, Any]) -> str:
        """Render polylines to GeoJSON and save to file.
        
        This is a convenience method that combines rendering and file writing.
        
        Args:
            polylines: List of polylines to render
            output_manager: OutputManager instance for file operations
            storey_name: Name of the storey for filename generation
            index: Index for filename generation
            metadata: Metadata for the GeoJSON
            
        Returns:
            str: Full path to the saved GeoJSON file
            
        Raises:
            WriteFailedError: If file writing fails
            ProcessingError: If GeoJSON generation fails
        """
        # Generate GeoJSON content
        geojson_content = self.render_to_string(polylines, metadata)
        
        # Generate filename
        filename = output_manager.generate_geojson_filename(storey_name, index)
        
        # Write to file
        file_path = output_manager.write_geojson_file(geojson_content, filename)
        
        self._logger.info(f"Rendered and saved GeoJSON: {file_path}")
        return file_path
    
    def should_generate_geojson(self) -> bool:
        """Check if GeoJSON generation is enabled in configuration.
        
        Returns:
            bool: True if GeoJSON should be generated, False otherwise
        """
        if self.config is None:
            # Default to True if no configuration is provided
            return True
        
        return self.config.output.write_geojson
    
    def render_and_save_conditional(self, polylines: List[Polyline2D], output_manager, 
                                   storey_name: str, index: int, metadata: Dict[str, Any]) -> Optional[str]:
        """Conditionally render and save GeoJSON based on configuration.
        
        This method checks the write_geojson setting before generating output.
        
        Args:
            polylines: List of polylines to render
            output_manager: OutputManager instance for file operations
            storey_name: Name of the storey for filename generation
            index: Index for filename generation
            metadata: Metadata for the GeoJSON
            
        Returns:
            Optional[str]: Full path to the saved GeoJSON file, or None if generation is disabled
            
        Raises:
            WriteFailedError: If file writing fails
            ProcessingError: If GeoJSON generation fails
        """
        if not self.should_generate_geojson():
            self._logger.debug("GeoJSON generation disabled in configuration")
            return None
        
        return self.render_and_save(polylines, output_manager, storey_name, index, metadata)
    
    def get_filename_pattern(self) -> str:
        """Get GeoJSON filename pattern from configuration.
        
        Returns:
            str: Filename pattern for GeoJSON files
        """
        if self.config is None:
            return "{index:02d}_{storey_name}.geo.json"  # Default pattern
        
        return self.config.output.geojson_filename_pattern
    
    def enhance_metadata_with_config(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata with configuration-specific information.
        
        Args:
            metadata: Base metadata dictionary
            
        Returns:
            Dict[str, Any]: Enhanced metadata with configuration information
        """
        enhanced = metadata.copy()
        
        if self.config is not None:
            # Add configuration-specific metadata
            enhanced["config_info"] = {
                "write_geojson_enabled": self.config.output.write_geojson,
                "filename_pattern": self.config.output.geojson_filename_pattern,
                "units_config": {
                    "auto_detect": self.config.units.auto_detect_units,
                    "manual_scale": self.config.units.unit_scale_to_m
                },
                "geometry_config": {
                    "use_world_coords": self.config.geometry.use_world_coords,
                    "subtract_openings": self.config.geometry.subtract_openings,
                    "sew_shells": self.config.geometry.sew_shells
                }
            }
            
            # Add class filter information
            if self.config.class_filters:
                enhanced["class_filters"] = {
                    "include_classes": self.config.class_filters.include_ifc_classes,
                    "exclude_classes": self.config.class_filters.exclude_ifc_classes
                }
        
        return enhanced
    
    def validate_semantic_metadata(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and ensure all required semantic metadata properties are present.
        
        Args:
            properties: Properties dictionary to validate
            
        Returns:
            Dict[str, Any]: Validated properties with all required fields
        """
        required_fields = {
            "ifc_class": "Unknown",
            "category": "Ukjent",
            "storey_name": "Unknown",
            "element_type": "Other",
            "is_structural": False,
            "is_opening": False,
            "is_building_service": False,
            "is_furnishing": False,
            "geometry_type": "LineString",
            "beskrivelse": "Ingen beskrivelse tilgjengelig",
            "kategori_gruppe": "Øvrige elementer"
        }
        
        # Ensure all required fields are present
        for field, default_value in required_fields.items():
            if field not in properties:
                properties[field] = default_value
                self._logger.debug(f"Added missing semantic metadata field: {field} = {default_value}")
        
        return properties
    
    def create_enhanced_feature_properties(self, ifc_class: str, storey_name: str, 
                                         element_guid: str, additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create enhanced feature properties with all required semantic metadata.
        
        This method ensures all required properties are included and validates the result.
        
        Args:
            ifc_class: IFC class of the element
            storey_name: Name of the building storey
            element_guid: GUID of the element
            additional_metadata: Optional additional metadata to include
            
        Returns:
            Dict[str, Any]: Complete and validated properties dictionary
        """
        # Create base properties
        properties = self.create_feature_properties(ifc_class, storey_name)
        
        # Add element-specific information
        properties["element_guid"] = element_guid
        
        # Add additional metadata if provided
        if additional_metadata:
            properties.update(additional_metadata)
        
        # Add configuration-specific metadata if available
        if self.config is not None:
            properties["processing_config"] = {
                "cut_height": self.config.get_storey_cut_height(storey_name),
                "tolerances": {
                    "slice_tol": self.config.tolerances.slice_tol,
                    "chain_tol": self.config.tolerances.chain_tol
                }
            }
        
        # Validate and ensure all required fields are present
        properties = self.validate_semantic_metadata(properties)
        
        return properties
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration settings relevant to GeoJSON generation.
        
        Returns:
            Dict[str, Any]: Configuration summary
        """
        if self.config is None:
            return {
                "config_loaded": False,
                "write_geojson": True,  # Default
                "filename_pattern": "{index:02d}_{storey_name}.geo.json"
            }
        
        return {
            "config_loaded": True,
            "write_geojson": self.config.output.write_geojson,
            "filename_pattern": self.config.output.geojson_filename_pattern,
            "manifest_filename": self.config.output.manifest_filename,
            "output_directory": self.config.output_dir,
            "units_auto_detect": self.config.units.auto_detect_units,
            "geometry_use_world_coords": self.config.geometry.use_world_coords,
            "class_filters_active": bool(
                self.config.class_filters.include_ifc_classes or 
                self.config.class_filters.exclude_ifc_classes
            )
        }