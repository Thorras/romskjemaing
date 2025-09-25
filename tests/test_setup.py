"""
Test basic project setup and imports.
"""

import pytest


def test_ifcopenshell_import():
    """Test that IfcOpenShell can be imported."""
    try:
        import ifcopenshell
        assert ifcopenshell is not None
    except ImportError:
        pytest.fail("IfcOpenShell could not be imported")


def test_pyqt6_import():
    """Test that PyQt6 can be imported."""
    try:
        from PyQt6.QtWidgets import QApplication
        assert QApplication is not None
    except ImportError:
        pytest.fail("PyQt6 could not be imported")


def test_main_window_import():
    """Test that MainWindow can be imported."""
    try:
        from ifc_room_schedule.ui import MainWindow
        assert MainWindow is not None
    except ImportError:
        pytest.fail("MainWindow could not be imported")