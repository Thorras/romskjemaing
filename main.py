#!/usr/bin/env python3
"""
IFC Room Schedule Application Entry Point

Main application launcher for the IFC Room Schedule desktop application.
Enhanced with performance optimizations and NS Standards integration.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from ifc_room_schedule.ui.main_window import MainWindow
from ifc_room_schedule.utils.enhanced_logging import enhanced_logger


def main():
    """Main application entry point with performance optimizations."""
    # Initialize enhanced logging
    enhanced_logger.initialize()
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("IFC Room Schedule")
    app.setApplicationVersion("1.1.0")  # Updated version with NS Standards
    app.setOrganizationName("Building Professional")
    
    # Set application properties for performance
    app.setAttribute(app.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setAttribute(app.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # Log application startup
    enhanced_logger.logger.info("Starting IFC Room Schedule Application v1.1.0")
    enhanced_logger.logger.info("Features: NS Standards Integration, Performance Optimizations")
    
    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Log successful startup
        enhanced_logger.logger.info("Application started successfully")
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        enhanced_logger.logger.error(f"Application startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()