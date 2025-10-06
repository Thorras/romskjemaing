#!/usr/bin/env python3
"""
Test to verify the SpaceDetailWidget interface is working correctly.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_interface():
    """Test the SpaceDetailWidget interface."""
    
    try:
        from ifc_room_schedule.ui.space_detail_widget import SpaceDetailWidget
        from ifc_room_schedule.data.space_model import SpaceData
        from PyQt6.QtWidgets import QApplication
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        print("Testing SpaceDetailWidget interface...")
        
        # Create widget
        widget = SpaceDetailWidget()
        print("✓ SpaceDetailWidget created successfully")
        
        # Check that display_space method exists
        if hasattr(widget, 'display_space') and callable(getattr(widget, 'display_space')):
            print("✓ display_space method exists and is callable")
        else:
            print("✗ display_space method missing or not callable")
            return False
        
        # Check that deprecated load_space method raises proper error
        try:
            widget.load_space(None)
            print("✗ load_space should have raised an AttributeError")
            return False
        except AttributeError as e:
            if "Use 'display_space' instead" in str(e):
                print("✓ load_space correctly raises helpful error message")
            else:
                print(f"✗ load_space raises wrong error: {e}")
                return False
        
        # Test with actual space data
        test_space = SpaceData(
            guid="test-guid-123",
            number="101",
            name="Test Room",
            long_name="Test Room Long Name",
            description="Test room description",
            object_type="Room",
            zone_category="Office",
            elevation=0.0
        )
        
        # Test display_space works
        try:
            widget.display_space(test_space)
            print("✓ display_space works with real SpaceData")
        except Exception as e:
            print(f"✗ display_space failed: {e}")
            return False
        
        print("\n✅ All interface tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("SpaceDetailWidget Interface Verification")
    print("=" * 40)
    
    if test_interface():
        print("\n🎉 Interface verification successful!")
        sys.exit(0)
    else:
        print("\n❌ Interface verification failed!")
        sys.exit(1)