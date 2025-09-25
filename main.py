#!/usr/bin/env python3
"""
IFC Room Schedule Application Entry Point

Main application launcher for the IFC Room Schedule desktop application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from ifc_room_schedule.ui.main_window import MainWindow


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("IFC Room Schedule")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Building Professional")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()