"""
IFC Space Extractor

Extracts spatial information from IFC files using IfcOpenShell.
"""

from typing import List, Dict, Optional, Any, Tuple
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit
from ..data.space_model import SpaceData
from ..utils.enhanced_logging import enhanced_logger


class IfcSpaceExtractor:
    """Extracts IfcSpace entities and their properties from IFC files."""

    def __init__(self, ifc_file=None):
        """
        Initialize the space extractor.
        
        Args:
            ifc_file: IfcOpenShell file object (optional)
        """
        self.ifc_file = ifc_file
        self.logger = enhanced_logger.logger
        self._spaces_cache = None

    def set_ifc_file(self, ifc_file) -> None:
        """
        Set the IFC file to extract spaces from.
        
        Args:
            ifc_file: IfcOpenShell file object
        """
        self.ifc_file = ifc_file
        self._spaces_cache = None  # Clear cache when file changes

    def extract_spaces(self) -> List[SpaceData]:
        """
        Extract all IfcSpace entities from the IFC file.
        
        Returns:
            List of SpaceData objects
            
        Raises:
            ValueError: If no IFC file is loaded
            RuntimeError: If extraction fails
            MemoryError: If insufficient memory for extraction
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        try:
            # Get all IfcSpace entities
            try:
                ifc_spaces = self.ifc_file.by_type("IfcSpace")
            except MemoryError as e:
                raise MemoryError(f"Insufficient memory to load IfcSpace entities: {e}")
            except Exception as e:
                raise RuntimeError(f"Failed to access IfcSpace entities: {e}")
            
            if not ifc_spaces:
                self.logger.warning("No IfcSpace entities found in the file")
                return []

            spaces = []
            failed_extractions = []
            
            for i, ifc_space in enumerate(ifc_spaces):
                try:
                    space_data = self._extract_space_properties(ifc_space)
                    if space_data:
                        spaces.append(space_data)
                    else:
                        failed_extractions.append((getattr(ifc_space, 'GlobalId', f'Space_{i}'), "Failed to extract properties"))
                except MemoryError as e:
                    # For memory errors, we should stop processing
                    self.logger.error(f"Memory error extracting space {getattr(ifc_space, 'GlobalId', f'Space_{i}')}: {e}")
                    raise MemoryError(f"Insufficient memory to extract spaces. Processed {len(spaces)} of {len(ifc_spaces)} spaces.")
                except Exception as e:
                    space_id = getattr(ifc_space, 'GlobalId', f'Space_{i}')
                    self.logger.error(f"Error extracting space {space_id}: {e}")
                    failed_extractions.append((space_id, str(e)))
                    # Continue processing other spaces
                    continue

            # Log summary
            if failed_extractions:
                self.logger.warning(f"Failed to extract {len(failed_extractions)} spaces out of {len(ifc_spaces)}")
                for space_id, error in failed_extractions[:5]:  # Log first 5 failures
                    self.logger.debug(f"  - {space_id}: {error}")
            
            self.logger.info(f"Successfully extracted {len(spaces)} spaces from {len(ifc_spaces)} IfcSpace entities")
            self._spaces_cache = spaces
            return spaces

        except (ValueError, MemoryError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            error_msg = f"Failed to extract spaces from IFC file: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _extract_spaces_batch(self, ifc_spaces_batch: List, batch_offset: int = 0) -> Tuple[List[SpaceData], List[Tuple[str, str]]]:
        """
        Extract a batch of spaces with optimized processing.
        
        Args:
            ifc_spaces_batch: List of IFC space entities to process
            batch_offset: Offset for space numbering in logs
            
        Returns:
            Tuple of (successful_spaces, failed_extractions)
        """
        spaces = []
        failed_extractions = []
        
        for i, ifc_space in enumerate(ifc_spaces_batch):
            try:
                # Pre-check for essential properties to avoid expensive extraction
                if not hasattr(ifc_space, 'GlobalId') or not ifc_space.GlobalId:
                    space_id = f'Space_{batch_offset + i}'
                    failed_extractions.append((space_id, "Missing GlobalId"))
                    continue
                
                space_data = self._extract_space_properties(ifc_space)
                if space_data:
                    spaces.append(space_data)
                else:
                    failed_extractions.append((ifc_space.GlobalId, "Failed to extract properties"))
                    
            except MemoryError as e:
                # For memory errors, we should stop processing
                space_id = getattr(ifc_space, 'GlobalId', f'Space_{batch_offset + i}')
                self.logger.error(f"Memory error extracting space {space_id}: {e}")
                raise MemoryError(f"Insufficient memory to extract spaces. Processed {len(spaces)} of {len(ifc_spaces_batch)} spaces in current batch.")
            except Exception as e:
                space_id = getattr(ifc_space, 'GlobalId', f'Space_{batch_offset + i}')
                self.logger.error(f"Error extracting space {space_id}: {e}")
                failed_extractions.append((space_id, str(e)))
                continue
        
        return spaces, failed_extractions

    def get_space_by_guid(self, guid: str) -> Optional[SpaceData]:
        """
        Get a specific space by its GUID.
        
        Args:
            guid: The GlobalId of the space
            
        Returns:
            SpaceData object or None if not found
        """
        if not self._spaces_cache:
            self.extract_spaces()
            
        for space in self._spaces_cache or []:
            if space.guid == guid:
                return space
        return None

    def _extract_space_properties(self, ifc_space) -> Optional[SpaceData]:
        """
        Extract properties from a single IfcSpace entity.
        
        Args:
            ifc_space: IfcSpace entity from IfcOpenShell
            
        Returns:
            SpaceData object or None if extraction fails
        """
        try:
            # Extract basic properties
            guid = getattr(ifc_space, 'GlobalId', '')
            name = getattr(ifc_space, 'Name', '') or ''
            long_name = getattr(ifc_space, 'LongName', '') or ''
            description = getattr(ifc_space, 'Description', '') or ''
            object_type = getattr(ifc_space, 'ObjectType', '') or ''

            # Validate required fields
            if not guid:
                self.logger.warning("Space missing GlobalId, skipping")
                return None

            # Extract elevation
            elevation = 0.0
            if hasattr(ifc_space, 'ElevationWithFlooring') and ifc_space.ElevationWithFlooring:
                elevation = float(ifc_space.ElevationWithFlooring)

            # Extract quantities
            quantities = self._extract_quantities(ifc_space)

            # Determine zone category and number from name or object type
            zone_category = self._determine_zone_category(ifc_space)
            number = self._extract_space_number(ifc_space)

            # Create SpaceData object
            space_data = SpaceData(
                guid=guid,
                name=name,
                long_name=long_name,
                description=description,
                object_type=object_type,
                zone_category=zone_category,
                number=number,
                elevation=elevation,
                quantities=quantities
            )

            self.logger.debug(f"Extracted space: {guid} - {name}")
            return space_data

        except Exception as e:
            self.logger.error(f"Error extracting properties from space: {e}")
            return None

    def _extract_quantities(self, ifc_space) -> Dict[str, float]:
        """
        Extract quantity information from IfcSpace.
        
        Args:
            ifc_space: IfcSpace entity
            
        Returns:
            Dictionary of quantity names and values
        """
        quantities = {}
        
        try:
            # Get quantity sets
            for relationship in getattr(ifc_space, 'IsDefinedBy', []):
                if relationship.is_a('IfcRelDefinesByProperties'):
                    property_definition = relationship.RelatingPropertyDefinition
                    
                    if property_definition.is_a('IfcElementQuantity'):
                        for quantity in property_definition.Quantities:
                            quantity_name = getattr(quantity, 'Name', '')
                            
                            # Extract different types of quantities
                            if quantity.is_a('IfcQuantityLength'):
                                quantities[quantity_name] = float(quantity.LengthValue or 0)
                            elif quantity.is_a('IfcQuantityArea'):
                                quantities[quantity_name] = float(quantity.AreaValue or 0)
                            elif quantity.is_a('IfcQuantityVolume'):
                                quantities[quantity_name] = float(quantity.VolumeValue or 0)
                            elif quantity.is_a('IfcQuantityCount'):
                                quantities[quantity_name] = float(quantity.CountValue or 0)
                            elif quantity.is_a('IfcQuantityWeight'):
                                quantities[quantity_name] = float(quantity.WeightValue or 0)
                            elif quantity.is_a('IfcQuantityTime'):
                                quantities[quantity_name] = float(quantity.TimeValue or 0)

        except Exception as e:
            self.logger.warning(f"Error extracting quantities: {e}")

        return quantities

    def _determine_zone_category(self, ifc_space) -> str:
        """
        Determine the zone category from space properties.
        
        Args:
            ifc_space: IfcSpace entity
            
        Returns:
            Zone category string
        """
        # Check ObjectType first
        object_type = getattr(ifc_space, 'ObjectType', '') or ''
        if object_type:
            return object_type

        # Check LongName for category hints
        long_name = getattr(ifc_space, 'LongName', '') or ''
        if long_name:
            # Common space type keywords
            long_name_lower = long_name.lower()
            if any(keyword in long_name_lower for keyword in ['office', 'kontor']):
                return 'Office'
            elif any(keyword in long_name_lower for keyword in ['meeting', 'møte', 'conference']):
                return 'Meeting Room'
            elif any(keyword in long_name_lower for keyword in ['corridor', 'gang', 'hallway']):
                return 'Corridor'
            elif any(keyword in long_name_lower for keyword in ['storage', 'lager', 'arkiv']):
                return 'Storage'
            elif any(keyword in long_name_lower for keyword in ['toilet', 'wc', 'restroom']):
                return 'Restroom'

        # Check Name as fallback
        name = getattr(ifc_space, 'Name', '') or ''
        if name:
            name_lower = name.lower()
            if any(keyword in name_lower for keyword in ['office', 'kontor']):
                return 'Office'

        return 'Unspecified'

    def _extract_space_number(self, ifc_space) -> str:
        """
        Extract space number from space properties.
        
        Args:
            ifc_space: IfcSpace entity
            
        Returns:
            Space number string
        """
        # Try Name first (often contains room number)
        name = getattr(ifc_space, 'Name', '') or ''
        if name and name.strip():
            return name.strip()

        # Try to extract number from LongName
        long_name = getattr(ifc_space, 'LongName', '') or ''
        if long_name:
            # Look for patterns like "Room 101", "Office 205", etc.
            import re
            number_match = re.search(r'\b(\d+)\b', long_name)
            if number_match:
                return number_match.group(1)

        # Use GUID as fallback (last 8 characters)
        guid = getattr(ifc_space, 'GlobalId', '')
        if guid and len(guid) >= 8:
            return guid[-8:]

        return 'Unknown'

    def get_space_count(self) -> int:
        """
        Get the total number of spaces in the IFC file.
        
        Returns:
            Number of IfcSpace entities
        """
        if not self.ifc_file:
            return 0
            
        try:
            return len(self.ifc_file.by_type("IfcSpace"))
        except Exception:
            return 0

    def validate_spaces(self, spaces: List[SpaceData]) -> Tuple[bool, List[str]]:
        """
        Validate extracted space data.
        
        Args:
            spaces: List of SpaceData objects to validate
            
        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        errors = []
        
        if not spaces:
            errors.append("No spaces found to validate")
            return False, errors

        # Check for duplicate GUIDs
        guids = [space.guid for space in spaces]
        duplicate_guids = set([guid for guid in guids if guids.count(guid) > 1])
        if duplicate_guids:
            errors.append(f"Duplicate GUIDs found: {', '.join(duplicate_guids)}")

        # Check for missing required properties
        for i, space in enumerate(spaces):
            if not space.guid:
                errors.append(f"Space {i+1}: Missing GUID")
            if not space.name and not space.long_name:
                errors.append(f"Space {space.guid}: Missing both Name and LongName")

        return len(errors) == 0, errors