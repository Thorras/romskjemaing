"""
Test project structure and basic imports.
"""

import pytest


def test_main_package_import():
    """Test that main package can be imported."""
    import ifc_room_schedule
    assert ifc_room_schedule.__version__ == "0.1.0"


def test_parser_module_import():
    """Test that parser module can be imported."""
    from ifc_room_schedule import parser
    assert hasattr(parser, '__all__')


def test_ui_module_import():
    """Test that UI module can be imported."""
    from ifc_room_schedule import ui
    assert hasattr(ui, '__all__')


def test_data_module_import():
    """Test that data module can be imported."""
    from ifc_room_schedule import data
    assert hasattr(data, '__all__')


def test_export_module_import():
    """Test that export module can be imported."""
    from ifc_room_schedule import export
    assert hasattr(export, '__all__')


def test_ifcopenshell_available():
    """Test that IfcOpenShell is available."""
    import ifcopenshell
    assert ifcopenshell.version


def test_pyqt6_available():
    """Test that PyQt6 is available."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    assert QApplication
    assert Qt