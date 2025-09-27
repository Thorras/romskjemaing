#!/usr/bin/env python3
"""
Quick test to verify the application can start without errors
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import PyQt6
        print("✅ PyQt6 imported successfully")
    except ImportError as e:
        print(f"❌ PyQt6 import failed: {e}")
        return False
    
    try:
        import ifcopenshell
        print("✅ IfcOpenShell imported successfully")
    except ImportError as e:
        print(f"❌ IfcOpenShell import failed: {e}")
        return False
    
    try:
        import pandas
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    return True

def test_app_modules():
    """Test that application modules can be imported."""
    print("\nTesting application modules...")
    
    try:
        from ifc_room_schedule.ui.main_window import MainWindow
        print("✅ MainWindow imported successfully")
    except ImportError as e:
        print(f"❌ MainWindow import failed: {e}")
        return False
    
    try:
        from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
        print("✅ IfcFileReader imported successfully")
    except ImportError as e:
        print(f"❌ IfcFileReader import failed: {e}")
        return False
    
    try:
        from ifc_room_schedule.export.json_builder import JsonBuilder
        print("✅ JsonBuilder imported successfully")
    except ImportError as e:
        print(f"❌ JsonBuilder import failed: {e}")
        return False
    
    return True

def test_app_creation():
    """Test that the application can be created."""
    print("\nTesting application creation...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from ifc_room_schedule.ui.main_window import MainWindow
        
        # Create QApplication (required for Qt widgets)
        app = QApplication([])
        
        # Create main window
        window = MainWindow()
        print("✅ MainWindow created successfully")
        
        # Test basic properties
        assert hasattr(window, 'ifc_reader'), "MainWindow should have ifc_reader"
        assert hasattr(window, 'spaces'), "MainWindow should have spaces list"
        print("✅ MainWindow has required attributes")
        
        # Cleanup
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"❌ Application creation failed: {e}")
        return False

def main():
    """Run all startup tests."""
    print("🧪 IFC Room Schedule Application - Startup Test")
    print("=" * 50)
    
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Run tests
    tests = [
        ("Import Test", test_imports),
        ("Module Test", test_app_modules),
        ("Creation Test", test_app_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED\n")
        else:
            print(f"❌ {test_name} FAILED\n")
    
    # Summary
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Application is ready to run.")
        print("\nTo start the application, run:")
        print("  python main.py")
        print("  or")
        print("  run_app.bat (Windows)")
        print("  ./run_app.sh (macOS/Linux)")
        return True
    else:
        print("❌ Some tests failed. Please check dependencies.")
        print("\nTo install dependencies, run:")
        print("  pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)