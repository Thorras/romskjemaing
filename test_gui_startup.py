#!/usr/bin/env python3
"""
Test GUI startup without blocking
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

def test_gui_startup():
    """Test that the GUI can start and close automatically."""
    print("🖥️  Testing GUI startup...")
    
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("IFC Room Schedule Test")
        
        # Import and create main window
        from ifc_room_schedule.ui.main_window import MainWindow
        window = MainWindow()
        
        print("✅ MainWindow created successfully")
        
        # Show window briefly
        window.show()
        print("✅ Window displayed")
        
        # Set up timer to close after 2 seconds
        timer = QTimer()
        timer.timeout.connect(lambda: (
            print("✅ GUI test completed successfully"),
            window.close(),
            app.quit()
        ))
        timer.start(2000)  # 2 seconds
        
        # Run event loop briefly
        app.exec()
        
        print("✅ Application closed cleanly")
        return True
        
    except Exception as e:
        print(f"❌ GUI startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 GUI Startup Test")
    print("=" * 30)
    
    if test_gui_startup():
        print("\n🎉 GUI startup test passed!")
        print("The application is ready to run normally.")
    else:
        print("\n❌ GUI startup test failed!")
        print("Check error messages above.")
    
    print("\nTo run the full application:")
    print("  python main.py")