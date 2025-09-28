"""
NS 8360 Name Parser

Parser for NS 8360 compliant IFC Space names following Norwegian naming standards.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class NS8360ParsedName:
    """Parsed components of an NS 8360 compliant space name."""
    
    prefix: str  # "SPC"
    storey: str  # "02", "01", "U1"
    zone: Optional[str]  # "A101", None
    function_code: str  # "111", "130"
    sequence: str  # "003", "001"
    is_valid: bool
    raw_name: str
    confidence: float = 0.0  # Confidence score for parsing


class NS8360NameParser:
    """Parser for NS 8360 compliant IFC Space names."""
    
    # Regex patterns from NS 8360 standard
    PATTERN_WITH_ZONE = re.compile(r'^SPC-([A-Z0-9]{1,3})-([A-Z0-9]{1,6})-(\d{3})-(\d{3})$')
    PATTERN_NO_ZONE = re.compile(r'^SPC-([A-Z0-9]{1,3})-(\d{3})-(\d{3})$')
    
    # Norwegian room name patterns for fallback inference
    NORWEGIAN_ROOM_PATTERNS = {
        'stue': {'function_code': '111', 'confidence': 0.8},
        'opphold': {'function_code': '111', 'confidence': 0.9},
        'living': {'function_code': '111', 'confidence': 0.7},
        'bad': {'function_code': '130', 'confidence': 0.9},
        'våtrom': {'function_code': '130', 'confidence': 0.95},
        'wc': {'function_code': '131', 'confidence': 0.9},
        'toalett': {'function_code': '131', 'confidence': 0.8},
        'baderom': {'function_code': '132', 'confidence': 0.9},
        'bath': {'function_code': '132', 'confidence': 0.7},
        'kjøkken': {'function_code': '140', 'confidence': 0.9},
        'kitchen': {'function_code': '140', 'confidence': 0.7},
        'soverom': {'function_code': '121', 'confidence': 0.9},
        'bedroom': {'function_code': '121', 'confidence': 0.7},
    }
    
    def parse(self, space_name: str) -> NS8360ParsedName:
        """
        Parse NS 8360 compliant space name.
        
        Args:
            space_name: Space name to parse
            
        Returns:
            NS8360ParsedName with parsed components
        """
        if not space_name:
            return self._create_invalid_result(space_name, "Empty space name")
        
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
                raw_name=space_name,
                confidence=1.0
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
                raw_name=space_name,
                confidence=1.0
            )
        
        # Try intelligent inference from Norwegian room names
        inferred = self._infer_from_norwegian_name(space_name)
        if inferred:
            return inferred
        
        # Invalid pattern - create fallback
        return self._create_invalid_result(space_name, "No matching pattern")
    
    def validate(self, space_name: str) -> bool:
        """
        Validate if space name follows NS 8360 standard.
        
        Args:
            space_name: Space name to validate
            
        Returns:
            True if valid NS 8360 format
        """
        return self.parse(space_name).is_valid
    
    def _infer_from_norwegian_name(self, space_name: str) -> Optional[NS8360ParsedName]:
        """
        Attempt to infer NS 8360 components from Norwegian room names.
        
        Args:
            space_name: Space name to analyze
            
        Returns:
            NS8360ParsedName if inference successful, None otherwise
        """
        name_lower = space_name.lower()
        
        # Look for Norwegian room type patterns
        best_match = None
        best_confidence = 0.0
        
        for pattern, info in self.NORWEGIAN_ROOM_PATTERNS.items():
            if pattern in name_lower:
                if info['confidence'] > best_confidence:
                    best_match = info
                    best_confidence = info['confidence']
        
        if best_match:
            # Try to extract storey information
            storey = self._extract_storey_from_name(space_name)
            sequence = self._extract_sequence_from_name(space_name)
            
            return NS8360ParsedName(
                prefix="",  # Not SPC format
                storey=storey,
                zone=None,
                function_code=best_match['function_code'],
                sequence=sequence,
                is_valid=False,  # Not compliant but parseable
                raw_name=space_name,
                confidence=best_confidence * 0.7  # Reduce confidence for inference
            )
        
        return None
    
    def _extract_storey_from_name(self, space_name: str) -> str:
        """Extract storey information from space name."""
        # Look for patterns like "2. etasje", "etasje 2", "2nd floor"
        storey_patterns = [
            r'(\d+)\.?\s*etasje',
            r'etasje\s*(\d+)',
            r'(\d+)(?:nd|rd|th|st)?\s*floor',
            r'floor\s*(\d+)',
            r'\b(\d+)\b'  # Any number as fallback
        ]
        
        for pattern in storey_patterns:
            match = re.search(pattern, space_name.lower())
            if match:
                storey_num = match.group(1)
                return f"{int(storey_num):02d}"  # Format as 01, 02, etc.
        
        return "01"  # Default to ground floor
    
    def _extract_sequence_from_name(self, space_name: str) -> str:
        """Extract sequence number from space name."""
        # Look for trailing numbers or explicit numbering
        sequence_patterns = [
            r'\b(\d+)$',  # Number at end
            r'nr\.?\s*(\d+)',  # "nr. 3"
            r'room\s*(\d+)',  # "room 3"
            r'\b(\d+)\b'  # Any number as fallback
        ]
        
        for pattern in sequence_patterns:
            match = re.search(pattern, space_name.lower())
            if match:
                seq_num = match.group(1)
                return f"{int(seq_num):03d}"  # Format as 001, 002, etc.
        
        return "001"  # Default sequence
    
    def _create_invalid_result(self, space_name: str, reason: str) -> NS8360ParsedName:
        """Create an invalid parsing result."""
        return NS8360ParsedName(
            prefix="",
            storey="",
            zone=None,
            function_code="",
            sequence="",
            is_valid=False,
            raw_name=space_name,
            confidence=0.0
        )


# Example usage and testing
if __name__ == "__main__":
    parser = NS8360NameParser()
    
    # Test cases from NS 8360 standard
    test_cases = [
        "SPC-02-A101-111-003",  # Valid with zone
        "SPC-01-A101-130-001",  # Valid with zone (wet room)
        "SPC-02-111-003",       # Valid without zone
        "Bad 2. etasje",        # Norwegian inference
        "Stue leilighet A101",  # Norwegian inference
        "Living room 3",        # English inference
        "InvalidName123",       # Invalid
    ]
    
    print("NS 8360 Name Parser Test Results:")
    print("=" * 50)
    
    for test_case in test_cases:
        result = parser.parse(test_case)
        print(f"\nInput: '{test_case}'")
        print(f"Valid: {result.is_valid}")
        print(f"Confidence: {result.confidence:.2f}")
        if result.function_code:
            print(f"Function Code: {result.function_code}")
        if result.storey:
            print(f"Storey: {result.storey}")
        if result.zone:
            print(f"Zone: {result.zone}")
        if result.sequence:
            print(f"Sequence: {result.sequence}")
