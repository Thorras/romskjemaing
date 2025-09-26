#!/usr/bin/env python3
"""
Test script to verify space boundary display in UI
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from PyQt6.QtWidgets import QApplication
from ifc_room_schedule.ui.main_window import MainWindow

def test_ui_boundaries():
    """Test the UI with space boundaries."""
    
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Load test file automatically
    test_file = "tesfiler/AkkordSvingen 23_ARK.ifc"
    if os.path.exists(test_file):
        print(f"Loading test file: {test_file}")
        window.process_ifc_file(test_file)
    else:
        print(f"Test file not found: {test_file}")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    test_ui_boundaries()