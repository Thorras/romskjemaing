"""
Section Configuration for IFC Room Schedule

Manages configuration for room schedule sections, export profiles,
and fallback strategies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import json
from pathlib import Path

from ..data.enhanced_room_schedule_model import ValidationLevel, FallbackStrategy, Phase


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"
    CSV = "csv"


@dataclass
class SectionSettings:
    """Settings for a specific room schedule section."""
    
    enabled: bool = True
    required: bool = False
    fallback_strategy: FallbackStrategy = FallbackStrategy.INFER
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert section settings to dictionary."""
        return {
            "enabled": self.enabled,
            "required": self.required,
            "fallback_strategy": self.fallback_strategy.value,
            "validation_level": self.validation_level.value,
            "custom_settings": self.custom_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SectionSettings':
        """Create section settings from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            required=data.get("required", False),
            fallback_strategy=FallbackStrategy(data.get("fallback_strategy", "infer")),
            validation_level=ValidationLevel(data.get("validation_level", "moderate")),
            custom_settings=data.get("custom_settings", {})
        )


@dataclass
class ExportProfile:
    """Export profile defining which sections to include."""
    
    name: str
    description: str
    phase: Phase
    section_settings: Dict[str, SectionSettings] = field(default_factory=dict)
    export_formats: List[ExportFormat] = field(default_factory=lambda: [ExportFormat.JSON])
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    fallback_strategy: FallbackStrategy = FallbackStrategy.INFER
    
    def __post_init__(self):
        """Initialize default section settings if not provided."""
        if not self.section_settings:
            self.section_settings = self._get_default_section_settings()
    
    def _get_default_section_settings(self) -> Dict[str, SectionSettings]:
        """Get default section settings based on phase."""
        default_settings = {
            "meta": SectionSettings(enabled=True, required=True),
            "identification": SectionSettings(enabled=True, required=True),
            "classification": SectionSettings(enabled=True, required=True),
            "structure": SectionSettings(enabled=True, required=False),
            "geometry_enhanced": SectionSettings(enabled=True, required=True),
            "ifc_metadata": SectionSettings(enabled=True, required=False),
            "performance_requirements": SectionSettings(enabled=False, required=False),
            "finishes": SectionSettings(enabled=False, required=False),
            "openings": SectionSettings(enabled=False, required=False),
            "fixtures": SectionSettings(enabled=False, required=False),
            "hse": SectionSettings(enabled=False, required=False)
        }
        
        # Adjust based on phase
        if self.phase == Phase.CORE:
            # Only core sections enabled
            for section in ["performance_requirements", "finishes", "openings", "fixtures", "hse"]:
                default_settings[section].enabled = False
        elif self.phase == Phase.ADVANCED:
            # Core + advanced sections enabled
            for section in ["performance_requirements", "finishes", "openings"]:
                default_settings[section].enabled = True
        elif self.phase == Phase.PRODUCTION:
            # All sections enabled
            for section in default_settings:
                default_settings[section].enabled = True
        
        return default_settings
    
    def get_enabled_sections(self) -> List[str]:
        """Get list of enabled section names."""
        return [name for name, settings in self.section_settings.items() if settings.enabled]
    
    def get_required_sections(self) -> List[str]:
        """Get list of required section names."""
        return [name for name, settings in self.section_settings.items() if settings.required]
    
    def is_section_enabled(self, section_name: str) -> bool:
        """Check if a section is enabled."""
        return self.section_settings.get(section_name, SectionSettings()).enabled
    
    def is_section_required(self, section_name: str) -> bool:
        """Check if a section is required."""
        return self.section_settings.get(section_name, SectionSettings()).required
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert export profile to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "phase": self.phase.value,
            "section_settings": {
                name: settings.to_dict() 
                for name, settings in self.section_settings.items()
            },
            "export_formats": [fmt.value for fmt in self.export_formats],
            "validation_level": self.validation_level.value,
            "fallback_strategy": self.fallback_strategy.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportProfile':
        """Create export profile from dictionary."""
        section_settings = {
            name: SectionSettings.from_dict(settings_data)
            for name, settings_data in data.get("section_settings", {}).items()
        }
        
        return cls(
            name=data["name"],
            description=data["description"],
            phase=Phase(data["phase"]),
            section_settings=section_settings,
            export_formats=[ExportFormat(fmt) for fmt in data.get("export_formats", ["json"])],
            validation_level=ValidationLevel(data.get("validation_level", "moderate")),
            fallback_strategy=FallbackStrategy(data.get("fallback_strategy", "infer"))
        )


@dataclass
class ExportConfiguration:
    """Complete export configuration."""
    
    profile: ExportProfile
    output_directory: str = "."
    file_naming_pattern: str = "room_schedule_{timestamp}"
    include_metadata: bool = True
    include_validation_report: bool = True
    compression_enabled: bool = False
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert export configuration to dictionary."""
        return {
            "profile": self.profile.to_dict(),
            "output_directory": self.output_directory,
            "file_naming_pattern": self.file_naming_pattern,
            "include_metadata": self.include_metadata,
            "include_validation_report": self.include_validation_report,
            "compression_enabled": self.compression_enabled,
            "custom_settings": self.custom_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportConfiguration':
        """Create export configuration from dictionary."""
        return cls(
            profile=ExportProfile.from_dict(data["profile"]),
            output_directory=data.get("output_directory", "."),
            file_naming_pattern=data.get("file_naming_pattern", "room_schedule_{timestamp}"),
            include_metadata=data.get("include_metadata", True),
            include_validation_report=data.get("include_validation_report", True),
            compression_enabled=data.get("compression_enabled", False),
            custom_settings=data.get("custom_settings", {})
        )


class SectionConfiguration:
    """Manages section configuration and export profiles."""
    
    # Predefined export profiles
    PREDEFINED_PROFILES = {
        "core": ExportProfile(
            name="Core",
            description="Basic room schedule with essential sections only",
            phase=Phase.CORE
        ),
        "advanced": ExportProfile(
            name="Advanced", 
            description="Extended room schedule with additional sections",
            phase=Phase.ADVANCED
        ),
        "production": ExportProfile(
            name="Production",
            description="Complete room schedule with all sections",
            phase=Phase.PRODUCTION
        ),
        "minimal": ExportProfile(
            name="Minimal",
            description="Minimal room schedule for basic export",
            phase=Phase.CORE,
            section_settings={
                "meta": SectionSettings(enabled=True, required=True),
                "identification": SectionSettings(enabled=True, required=True),
                "geometry_enhanced": SectionSettings(enabled=True, required=True),
                "ifc_metadata": SectionSettings(enabled=True, required=True)
            }
        ),
        "comprehensive": ExportProfile(
            name="Comprehensive",
            description="Comprehensive room schedule with all available data",
            phase=Phase.PRODUCTION,
            section_settings={
                name: SectionSettings(enabled=True, required=True)
                for name in [
                    "meta", "identification", "classification", "structure",
                    "geometry_enhanced", "ifc_metadata", "performance_requirements",
                    "finishes", "openings", "fixtures", "hse"
                ]
            }
        )
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize section configuration."""
        self.config_file = config_file
        self.profiles: Dict[str, ExportProfile] = {}
        self.current_profile: Optional[str] = None
        
        # Load predefined profiles
        self.profiles.update(self.PREDEFINED_PROFILES)
        
        # Load custom profiles from file if specified
        if config_file and Path(config_file).exists():
            self.load_from_file(config_file)
    
    def get_profile(self, profile_name: str) -> Optional[ExportProfile]:
        """Get export profile by name."""
        return self.profiles.get(profile_name)
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available profile names."""
        return list(self.profiles.keys())
    
    def create_profile(self, profile: ExportProfile) -> None:
        """Create a new export profile."""
        self.profiles[profile.name] = profile
    
    def update_profile(self, profile_name: str, profile: ExportProfile) -> None:
        """Update an existing export profile."""
        if profile_name in self.profiles:
            self.profiles[profile_name] = profile
    
    def delete_profile(self, profile_name: str) -> bool:
        """Delete an export profile."""
        if profile_name in self.PREDEFINED_PROFILES:
            return False  # Cannot delete predefined profiles
        
        if profile_name in self.profiles:
            del self.profiles[profile_name]
            return True
        return False
    
    def set_current_profile(self, profile_name: str) -> bool:
        """Set the current active profile."""
        if profile_name in self.profiles:
            self.current_profile = profile_name
            return True
        return False
    
    def get_current_profile(self) -> Optional[ExportProfile]:
        """Get the current active profile."""
        if self.current_profile:
            return self.profiles.get(self.current_profile)
        return None
    
    def create_export_configuration(self, 
                                  profile_name: str,
                                  output_directory: str = ".",
                                  **kwargs) -> Optional[ExportConfiguration]:
        """Create export configuration from profile."""
        profile = self.get_profile(profile_name)
        if not profile:
            return None
        
        return ExportConfiguration(
            profile=profile,
            output_directory=output_directory,
            **kwargs
        )
    
    def validate_configuration(self, config: ExportConfiguration) -> List[str]:
        """Validate export configuration and return list of issues."""
        issues = []
        
        # Check if output directory exists
        output_path = Path(config.output_directory)
        if not output_path.exists():
            issues.append(f"Output directory does not exist: {config.output_directory}")
        
        # Check if profile is valid
        if not config.profile:
            issues.append("No profile specified")
        
        # Check required sections
        required_sections = config.profile.get_required_sections()
        for section in required_sections:
            if not config.profile.is_section_enabled(section):
                issues.append(f"Required section '{section}' is not enabled")
        
        return issues
    
    def save_to_file(self, file_path: str) -> bool:
        """Save configuration to file."""
        try:
            config_data = {
                "profiles": {
                    name: profile.to_dict() 
                    for name, profile in self.profiles.items()
                    if name not in self.PREDEFINED_PROFILES  # Don't save predefined profiles
                },
                "current_profile": self.current_profile
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def load_from_file(self, file_path: str) -> bool:
        """Load configuration from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Load custom profiles
            for name, profile_data in config_data.get("profiles", {}).items():
                self.profiles[name] = ExportProfile.from_dict(profile_data)
            
            # Set current profile
            self.current_profile = config_data.get("current_profile")
            
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def get_section_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available sections."""
        return {
            "meta": {
                "name": "Meta",
                "description": "Project metadata and identification",
                "priority": "high",
                "phase": "core"
            },
            "identification": {
                "name": "Identification", 
                "description": "Space identification and naming",
                "priority": "high",
                "phase": "core"
            },
            "classification": {
                "name": "Classification",
                "description": "NS 3940 classification and categorization",
                "priority": "high",
                "phase": "core"
            },
            "structure": {
                "name": "Structure",
                "description": "Building hierarchy and structure",
                "priority": "medium",
                "phase": "core"
            },
            "geometry_enhanced": {
                "name": "Geometry Enhanced",
                "description": "Geometric properties and quantities",
                "priority": "high",
                "phase": "core"
            },
            "ifc_metadata": {
                "name": "IFC Metadata",
                "description": "IFC-specific metadata and references",
                "priority": "medium",
                "phase": "core"
            },
            "performance_requirements": {
                "name": "Performance Requirements",
                "description": "Technical performance requirements",
                "priority": "medium",
                "phase": "advanced"
            },
            "finishes": {
                "name": "Finishes",
                "description": "Surface finishes and materials",
                "priority": "low",
                "phase": "advanced"
            },
            "openings": {
                "name": "Openings",
                "description": "Doors, windows and other openings",
                "priority": "low",
                "phase": "advanced"
            },
            "fixtures": {
                "name": "Fixtures",
                "description": "Equipment and fixtures",
                "priority": "low",
                "phase": "production"
            },
            "hse": {
                "name": "HSE",
                "description": "Health, safety and environmental requirements",
                "priority": "medium",
                "phase": "production"
            }
        }


