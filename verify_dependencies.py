#!/usr/bin/env python3
"""
Dependency Verification Script for IFC Room Schedule Application

This script verifies that all required dependencies are installed and working
correctly for the 2D floor plan visualization system.
"""

import sys
import importlib
from typing import List, Tuple, Dict, Any


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major == 3 and version.minor == 11:
        return True, f"✓ Python {version.major}.{version.minor}.{version.micro} (Compatible)"
    else:
        return False, f"✗ Python {version.major}.{version.minor}.{version.micro} (Requires Python 3.11)"


def check_dependency(module_name: str, package_name: str = None, version_attr: str = None) -> Tuple[bool, str]:
    """
    Check if a dependency is available and optionally get version info.
    
    Args:
        module_name: Name of the module to import
        package_name: Display name for the package (defaults to module_name)
        version_attr: Attribute name to get version (e.g., '__version__', 'version')
    
    Returns:
        Tuple of (success, message)
    """
    if package_name is None:
        package_name = module_name
    
    try:
        module = importlib.import_module(module_name)
        
        version_info = ""
        if version_attr:
            try:
                version = getattr(module, version_attr)
                version_info = f" (v{version})"
            except AttributeError:
                version_info = " (version unknown)"
        
        return True, f"✓ {package_name}{version_info}"
    
    except ImportError as e:
        return False, f"✗ {package_name} - {str(e)}"
    except Exception as e:
        return False, f"✗ {package_name} - Unexpected error: {str(e)}"


def check_ifc_room_schedule_components() -> List[Tuple[bool, str]]:
    """Check IFC Room Schedule application components."""
    components = [
        ("ifc_room_schedule.visualization.geometry_extractor", "GeometryExtractor"),
        ("ifc_room_schedule.visualization.floor_plan_canvas", "FloorPlanCanvas"),
        ("ifc_room_schedule.visualization.geometry_models", "Geometry Models"),
        ("ifc_room_schedule.ui.floor_plan_widget", "FloorPlanWidget"),
        ("ifc_room_schedule.ui.main_window", "MainWindow"),
        ("ifc_room_schedule.parser.ifc_file_reader", "IFC File Reader"),
        ("ifc_room_schedule.parser.ifc_space_extractor", "IFC Space Extractor"),
    ]
    
    results = []
    for module_name, display_name in components:
        success, message = check_dependency(module_name, display_name)
        results.append((success, message))
    
    return results


def test_geometry_extractor_initialization() -> Tuple[bool, str]:
    """Test GeometryExtractor initialization."""
    try:
        from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
        extractor = GeometryExtractor()
        return True, "✓ GeometryExtractor initialization successful"
    except Exception as e:
        return False, f"✗ GeometryExtractor initialization failed: {str(e)}"


def test_pyqt6_gui_components() -> Tuple[bool, str]:
    """Test PyQt6 GUI components."""
    try:
        from PyQt6.QtWidgets import QApplication, QWidget
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPainter
        
        # Test basic QApplication creation (without showing GUI)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test widget creation
        widget = QWidget()
        
        return True, "✓ PyQt6 GUI components working"
    except Exception as e:
        return False, f"✗ PyQt6 GUI components failed: {str(e)}"


def main():
    """Main verification function."""
    print("IFC Room Schedule - Dependency Verification")
    print("=" * 50)
    
    # Check Python version
    success, message = check_python_version()
    print(message)
    if not success:
        print("\nERROR: Incompatible Python version. Please use Python 3.11")
        return False
    
    print("\nCore Dependencies:")
    print("-" * 20)
    
    # Core dependencies
    core_deps = [
        ("ifcopenshell", "ifcopenshell", "version"),
        ("PyQt6", "PyQt6"),
        ("PyQt6.QtWidgets", "PyQt6.QtWidgets"),
        ("psutil", "psutil", "__version__"),
        ("memory_profiler", "memory_profiler", "__version__"),
        ("numpy", "numpy", "__version__"),
        ("pandas", "pandas", "__version__"),
        ("openpyxl", "openpyxl", "__version__"),
        ("reportlab", "reportlab", "Version"),
        ("marshmallow", "marshmallow", "__version__"),
    ]
    
    all_success = True
    for dep in core_deps:
        success, message = check_dependency(*dep)
        print(message)
        if not success:
            all_success = False
    
    print("\nApplication Components:")
    print("-" * 25)
    
    # Application components
    component_results = check_ifc_room_schedule_components()
    for success, message in component_results:
        print(message)
        if not success:
            all_success = False
    
    print("\nFunctionality Tests:")
    print("-" * 20)
    
    # Test GeometryExtractor
    success, message = test_geometry_extractor_initialization()
    print(message)
    if not success:
        all_success = False
    
    # Test PyQt6 GUI
    success, message = test_pyqt6_gui_components()
    print(message)
    if not success:
        all_success = False
    
    print("\n" + "=" * 50)
    if all_success:
        print("✅ ALL DEPENDENCIES VERIFIED SUCCESSFULLY!")
        print("The 2D floor plan visualization system is ready to use.")
        return True
    else:
        print("❌ SOME DEPENDENCIES FAILED VERIFICATION")
        print("Please install missing dependencies before using the system.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)