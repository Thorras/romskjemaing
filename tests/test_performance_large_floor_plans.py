"""
Performance Tests for Large Floor Plans

Tests rendering performance, memory usage, and responsiveness with large floor plans
containing 100+ spaces per floor as part of the interactive floor plan enhancement.
"""

import pytest
import sys
import os
import time
import gc
import psutil
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ifc_room_schedule.ui.floor_plan_widget import FloorPlanWidget
from ifc_room_schedule.ui.space_list_widget import SpaceListWidget
from ifc_room_schedule.ui.main_window import MainWindow
from ifc_room_schedule.visualization.floor_plan_canvas import FloorPlanCanvas
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.visualization.geometry_models import FloorLevel, FloorGeometry, Polygon2D, Point2D


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app
    app.quit()


def create_large_floor_dataset(num_floors=5, spaces_per_floor=150):
    """Create a large dataset for performance testing."""
    spaces = []
    floor_geometries = {}
    
    for floor_num in range(num_floors):
        floor_id = f"FLOOR_{floor_num:02d}"
        floor_spaces = []
        
        # Create spaces for this floor
        for space_num in range(spaces_per_floor):
            space_guid = f"SPACE_{floor_num:02d}_{space_num:04d}"
            space = SpaceData(
                guid=space_guid,
                name=f"{floor_num}{space_num:03d}",
                long_name=f"Room {floor_num}-{space_num:03d}",
                description=f"Large dataset space {space_num} on floor {floor_num}",
                object_type="Office" if space_num % 3 == 0 else "Meeting Room" if space_num % 3 == 1 else "Storage",
                zone_category="Office" if space_num % 3 == 0 else "Meeting Room" if space_num % 3 == 1 else "Storage",
                number=f"{floor_num}{space_num:03d}",
                elevation=floor_num * 3.5,
                quantities={"Height": 3.0, "Area": 20.0 + (space_num % 10)},
                floor_id=floor_id
            )
            spaces.append(space)
            floor_spaces.append(space_guid)
        
        # Create floor level
        floor_level = FloorLevel(
            id=floor_id,
            name=f"Floor {floor_num}",
            elevation=floor_num * 3.5,
            spaces=floor_spaces,
            has_geometry=True,
            space_count=len(floor_spaces),
            total_area=sum(20.0 + (i % 10) for i in range(spaces_per_floor))
        )
        
        # Create floor geometry with many polygons
        polygons = []
        grid_size = int(spaces_per_floor ** 0.5) + 1  # Square grid layout
        
        for i, space_guid in enumerate(floor_spaces):
            row = i // grid_size
            col = i % grid_size
            
            # Create rectangular polygon for each space
            x_offset = col * 12.0
            y_offset = row * 10.0
            
            points = [
                Point2D(x_offset, y_offset),
                Point2D(x_offset + 10.0, y_offset),
                Point2D(x_offset + 10.0, y_offset + 8.0),
                Point2D(x_offset, y_offset + 8.0)
            ]
            
            polygon = Polygon2D(
                points=points,
                space_guid=space_guid,
                space_name=f"Room {i+1}",
                space_type=spaces[floor_num * spaces_per_floor + i].object_type
            )
            polygons.append(polygon)
        
        floor_geometries[floor_id] = FloorGeometry(
            level=floor_level,
            room_polygons=polygons,
            bounds=(0.0, 0.0, grid_size * 12.0, ((spaces_per_floor // grid_size) + 1) * 10.0)
        )
    
    return spaces, floor_geometries


class TestRenderingPerformance:
    """Test cases for rendering performance with large floor plans."""

    def test_initial_rendering_performance(self, qapp):
        """Test initial rendering performance with 150+ spaces."""
        spaces, floor_geometries = create_large_floor_dataset(num_floors=1, spaces_per_floor=150)
        
        floor_plan_widget = FloorPlanWidget()
        
        # Measure time to set geometry and render
        start_time = time.time()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        qapp.processEvents()  # Process paint events
        end_time = time.time()
        
        rendering_time = end_time - start_time
        
        # Should render within reasonable time (less than 2 seconds)
        assert rendering_time < 2.0, f"Initial rendering took {rendering_time:.2f}s, expected < 2.0s"
        
        # Verify all spaces are loaded
        assert len(floor_plan_widget.floor_geometries) == 1
        floor_geometry = list(floor_plan_widget.floor_geometries.values())[0]
        assert len(floor_geometry.room_polygons) == 150

    def test_zoom_performance_with_large_dataset(self, qapp):
        """Test zoom operations performance with large datasets."""
        spaces, floor_geometries = create_large_floor_dataset(num_floors=1, spaces_per_floor=200)
        
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        qapp.processEvents()
        
        # Test multiple zoom operations
        zoom_times = []
        zoom_levels = [0.5, 1.0, 2.0, 4.0, 1.0]  # Various zoom levels
        
        for zoom_level in zoom_levels:
            start_time = time.time()
            
            # Simulate zoom operation
            floor_plan_widget.floor_plan_canvas.zoom_level = zoom_level
            floor_plan_widget.floor_plan_canvas._update_view_transform()
            floor_plan_widget.floor_plan_canvas.update()
            qapp.processEvents()
            
            end_time = time.time()
            zoom_times.append(end_time - start_time)
        
        # Each zoom operation should be fast (less than 0.5 seconds)
        max_zoom_time = max(zoom_times)
        assert max_zoom_time < 0.5, f"Slowest zoom took {max_zoom_time:.2f}s, expected < 0.5s"
        
        # Average zoom time should be very fast
        avg_zoom_time = sum(zoom_times) / len(zoom_times)
        assert avg_zoom_time < 0.2, f"Average zoom time {avg_zoom_time:.2f}s, expected < 0.2s"

    def test_pan_performance_with_large_dataset(self, qapp):
        """Test pan operations performance with large datasets."""
        spaces, floor_geometries = create_large_floor_dataset(num_floors=1, spaces_per_floor=180)
        
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        qapp.processEvents()
        
        # Test multiple pan operations
        pan_times = []
        pan_offsets = [(100, 0), (0, 100), (-50, -50), (200, 150), (0, 0)]  # Various pan positions
        
        for x_offset, y_offset in pan_offsets:
            start_time = time.time()
            
            # Simulate pan operation
            floor_plan_widget.floor_plan_canvas.pan_offset_x = x_offset
            floor_plan_widget.floor_plan_canvas.pan_offset_y = y_offset
            floor_plan_widget.floor_plan_canvas._update_view_transform()
            floor_plan_widget.floor_plan_canvas.update()
            qapp.processEvents()
            
            end_time = time.time()
            pan_times.append(end_time - start_time)
        
        # Each pan operation should be fast
        max_pan_time = max(pan_times)
        assert max_pan_time < 0.3, f"Slowest pan took {max_pan_time:.2f}s, expected < 0.3s"

    def test_selection_highlighting_performance(self, qapp):
        """Test performance of highlighting selections with many spaces."""
        spaces, floor_geometries = create_large_floor_dataset(num_floors=1, spaces_per_floor=120)
        
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        qapp.processEvents()
        
        # Test highlighting different numbers of spaces
        selection_sizes = [1, 10, 50, 100]
        
        for selection_size in selection_sizes:
            # Create selection of specified size
            selected_spaces = [f"SPACE_00_{i:04d}" for i in range(selection_size)]
            
            start_time = time.time()
            floor_plan_widget.highlight_spaces(selected_spaces)
            qapp.processEvents()
            end_time = time.time()
            
            highlight_time = end_time - start_time
            
            # Highlighting should be fast regardless of selection size
            assert highlight_time < 0.4, f"Highlighting {selection_size} spaces took {highlight_time:.2f}s, expected < 0.4s"

    def test_floor_switching_performance_with_large_floors(self, qapp):
        """Test floor switching performance with multiple large floors."""
        spaces, floor_geometries = create_large_floor_dataset(num_floors=5, spaces_per_floor=100)
        
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        qapp.processEvents()
        
        # Test switching between floors
        floor_ids = list(floor_geometries.keys())
        switch_times = []
        
        for floor_id in floor_ids:
            start_time = time.time()
            floor_plan_widget.set_current_floor(floor_id)
            qapp.processEvents()
            end_time = time.time()
            
            switch_times.append(end_time - start_time)
        
        # Floor switching should be fast
        max_switch_time = max(switch_times)
        assert max_switch_time < 0.8, f"Slowest floor switch took {max_switch_time:.2f}s, expected < 0.8s"
        
        avg_switch_time = sum(switch_times) / len(switch_times)
        assert avg_switch_time < 0.4, f"Average floor switch time {avg_switch_time:.2f}s, expected < 0.4s"


class TestMemoryUsage:
    """Test cases for memory usage with large floor plans."""

    def get_memory_usage_mb(self):
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    def test_memory_usage_with_large_dataset(self, qapp):
        """Test memory usage when loading large floor plans."""
        # Get baseline memory usage
        gc.collect()
        baseline_memory = self.get_memory_usage_mb()
        
        # Create large dataset
        spaces, floor_geometries = create_large_floor_dataset(num_floors=3, spaces_per_floor=200)
        
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        qapp.processEvents()
        
        # Measure memory usage after loading
        current_memory = self.get_memory_usage_mb()
        memory_increase = current_memory - baseline_memory
        
        # Memory increase should be reasonable (less than 100MB for 600 spaces)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB, expected < 100MB"
        
        # Clean up
        floor_plan_widget.close()
        del floor_plan_widget
        del spaces
        del floor_geometries
        gc.collect()

    def test_memory_stability_during_operations(self, qapp):
        """Test memory stability during repeated operations."""
        spaces, floor_geometries = create_large_floor_dataset(num_floors=2, spaces_per_floor=150)
        
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        qapp.processEvents()
        
        # Get initial memory usage
        gc.collect()
        initial_memory = self.get_memory_usage_mb()
        
        # Perform many operations
        floor_ids = list(floor_geometries.keys())
        for _ in range(50):  # 50 iterations
            # Switch floors
            for floor_id in floor_ids:
                floor_plan_widget.set_current_floor(floor_id)
            
            # Zoom operations
            floor_plan_widget._zoom_in()
            floor_plan_widget._zoom_out()
            
            # Highlight selections
            selected_spaces = [f"SPACE_00_{i:04d}" for i in range(0, 20, 2)]
            floor_plan_widget.highlight_spaces(selected_spaces)
            
            qapp.processEvents()
        
        # Check memory usage after operations
        gc.collect()
        final_memory = self.get_memory_usage_mb()
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase significantly during operations
        assert memory_increase < 20, f"Memory increased by {memory_increase:.1f}MB during operations, expected < 20MB"

    def test_memory_cleanup_on_floor_switching(self, qapp):
        """Test that memory is properly cleaned up when switching floors."""
        spaces, floor_geometries = create_large_floor_dataset(num_floors=4, spaces_per_floor=100)
        
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        qapp.processEvents()
        
        # Get memory usage after initial load
        gc.collect()
        initial_memory = self.get_memory_usage_mb()
        
        # Switch floors many times
        floor_ids = list(floor_geometries.keys())
        for _ in range(20):  # 20 complete cycles through all floors
            for floor_id in floor_ids:
                floor_plan_widget.set_current_floor(floor_id)
                qapp.processEvents()
        
        # Force garbage collection
        gc.collect()
        final_memory = self.get_memory_usage_mb()
        memory_increase = final_memory - initial_memory
        
        # Memory should not grow significantly from floor switching
        assert memory_increase < 15, f"Memory increased by {memory_increase:.1f}MB from floor switching, expected < 15MB"


class TestResponsiveness:
    """Test cases for UI responsiveness with large floor plans."""

    def test_ui_responsiveness_during_loading(self, qapp):
        """Test that UI remains responsive during large dataset loading."""
        # Create very large dataset
        spaces, floor_geometries = create_large_floor_dataset(num_floors=1, spaces_per_floor=300)
        
        floor_plan_widget = FloorPlanWidget()
        
        # Track responsiveness during loading
        response_times = []
        
        def check_responsiveness():
            """Check if UI is responsive by processing events."""
            start_time = time.time()
            qapp.processEvents()
            end_time = time.time()
            response_times.append(end_time - start_time)
        
        # Set up timer to check responsiveness during loading
        timer = QTimer()
        timer.timeout.connect(check_responsiveness)
        timer.start(100)  # Check every 100ms
        
        # Load large dataset
        start_load = time.time()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        
        # Wait for loading to complete
        while time.time() - start_load < 3.0:  # Wait up to 3 seconds
            qapp.processEvents()
            if floor_plan_widget.isVisible():
                break
        
        timer.stop()
        
        # Check that UI remained responsive (no single event processing took too long)
        if response_times:
            max_response_time = max(response_times)
            assert max_response_time < 0.5, f"UI became unresponsive for {max_response_time:.2f}s, expected < 0.5s"

    def test_zoom_responsiveness_with_large_dataset(self, qapp):
        """Test zoom responsiveness with large datasets."""
        spaces, floor_geometries = create_large_floor_dataset(num_floors=1, spaces_per_floor=250)
        
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        qapp.processEvents()
        
        # Test rapid zoom operations
        zoom_response_times = []
        
        for _ in range(10):  # 10 rapid zoom operations
            start_time = time.time()
            
            # Zoom in
            floor_plan_widget._zoom_in()
            qapp.processEvents()
            
            # Zoom out
            floor_plan_widget._zoom_out()
            qapp.processEvents()
            
            end_time = time.time()
            zoom_response_times.append(end_time - start_time)
        
        # Each zoom cycle should be responsive
        max_zoom_response = max(zoom_response_times)
        assert max_zoom_response < 0.6, f"Slowest zoom cycle took {max_zoom_response:.2f}s, expected < 0.6s"

    def test_selection_responsiveness_with_large_dataset(self, qapp):
        """Test selection responsiveness with large datasets."""
        spaces, floor_geometries = create_large_floor_dataset(num_floors=1, spaces_per_floor=200)
        
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(floor_geometries)
        floor_plan_widget.show()
        qapp.processEvents()
        
        # Test rapid selection changes
        selection_response_times = []
        
        for i in range(20):  # 20 rapid selection changes
            start_time = time.time()
            
            # Create different selections
            selected_spaces = [f"SPACE_00_{j:04d}" for j in range(i, i + 10)]
            floor_plan_widget.highlight_spaces(selected_spaces)
            qapp.processEvents()
            
            end_time = time.time()
            selection_response_times.append(end_time - start_time)
        
        # Each selection change should be responsive
        max_selection_response = max(selection_response_times)
        assert max_selection_response < 0.4, f"Slowest selection took {max_selection_response:.2f}s, expected < 0.4s"


class TestGeometryExtractionPerformance:
    """Test cases for geometry extraction performance with large datasets."""

    def test_progressive_loading_performance(self, qapp):
        """Test progressive loading performance for large IFC files."""
        # Mock large IFC file
        mock_large_ifc = Mock()
        mock_large_ifc.by_type.side_effect = lambda ifc_type: (
            [Mock() for _ in range(500)] if ifc_type == "IfcSpace" else  # 500 spaces
            [Mock() for _ in range(20)] if ifc_type == "IfcBuildingStorey" else []  # 20 floors
        )
        
        with patch('ifc_room_schedule.visualization.geometry_extractor.IFC_AVAILABLE', True):
            extractor = GeometryExtractor()
            
            # Mock the progressive extraction method
            def mock_progressive_extraction(ifc_file, progress_callback):
                # Simulate progressive loading with callback
                if progress_callback:
                    for i in range(10):
                        progress_callback(i * 10)  # Report progress 0-90%
                        time.sleep(0.01)  # Simulate work
                    progress_callback(100)  # Complete
                
                # Return mock result
                return {f"FLOOR_{i:02d}": Mock() for i in range(20)}
            
            with patch.object(extractor, '_extract_geometry_progressive', side_effect=mock_progressive_extraction):
                progress_updates = []
                
                def progress_callback(progress):
                    progress_updates.append(progress)
                
                start_time = time.time()
                result = extractor.extract_floor_geometry(mock_large_ifc, progress_callback)
                end_time = time.time()
                
                extraction_time = end_time - start_time
                
                # Should complete in reasonable time
                assert extraction_time < 1.0, f"Progressive extraction took {extraction_time:.2f}s, expected < 1.0s"
                
                # Should have provided progress updates
                assert len(progress_updates) > 0, "No progress updates received"
                assert 100 in progress_updates, "Final progress update not received"
                
                # Should return results for all floors
                assert len(result) == 20

    def test_memory_efficient_extraction(self, qapp):
        """Test memory-efficient geometry extraction for large datasets."""
        # Mock large IFC file
        mock_large_ifc = Mock()
        mock_large_ifc.by_type.side_effect = lambda ifc_type: (
            [Mock() for _ in range(300)] if ifc_type == "IfcSpace" else
            [Mock() for _ in range(10)] if ifc_type == "IfcBuildingStorey" else []
        )
        
        with patch('ifc_room_schedule.visualization.geometry_extractor.IFC_AVAILABLE', True):
            extractor = GeometryExtractor()
            
            # Get baseline memory
            gc.collect()
            baseline_memory = self.get_memory_usage_mb()
            
            # Mock extraction to return reasonable-sized data
            mock_result = {}
            for i in range(10):
                floor_level = FloorLevel(
                    id=f"FLOOR_{i:02d}",
                    name=f"Floor {i}",
                    elevation=i * 3.5,
                    spaces=[f"SPACE_{i:02d}_{j:03d}" for j in range(30)],  # 30 spaces per floor
                    has_geometry=True,
                    space_count=30,
                    total_area=750.0
                )
                
                # Create minimal polygons to test memory usage
                polygons = []
                for j in range(30):
                    points = [Point2D(0, 0), Point2D(10, 0), Point2D(10, 8), Point2D(0, 8)]
                    polygon = Polygon2D(
                        points=points,
                        space_guid=f"SPACE_{i:02d}_{j:03d}",
                        space_name=f"Room {j+1}",
                        space_type="Office"
                    )
                    polygons.append(polygon)
                
                mock_result[f"FLOOR_{i:02d}"] = FloorGeometry(
                    level=floor_level,
                    room_polygons=polygons,
                    bounds=(0.0, 0.0, 100.0, 80.0)
                )
            
            with patch.object(extractor, '_extract_geometry_standard', return_value=mock_result):
                result = extractor.extract_floor_geometry(mock_large_ifc)
                
                # Check memory usage after extraction
                current_memory = self.get_memory_usage_mb()
                memory_increase = current_memory - baseline_memory
                
                # Memory increase should be reasonable for 300 spaces across 10 floors
                assert memory_increase < 50, f"Memory increased by {memory_increase:.1f}MB, expected < 50MB"
                
                # Should return all floors
                assert len(result) == 10

    def get_memory_usage_mb(self):
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024


class TestScalabilityLimits:
    """Test cases to determine scalability limits."""

    def test_maximum_spaces_per_floor(self, qapp):
        """Test maximum number of spaces that can be handled per floor."""
        max_spaces_tested = 0
        
        # Test increasing numbers of spaces until performance degrades
        for spaces_count in [100, 200, 300, 400, 500]:
            try:
                spaces, floor_geometries = create_large_floor_dataset(num_floors=1, spaces_per_floor=spaces_count)
                
                floor_plan_widget = FloorPlanWidget()
                
                start_time = time.time()
                floor_plan_widget.set_floor_geometry(floor_geometries)
                floor_plan_widget.show()
                qapp.processEvents()
                end_time = time.time()
                
                loading_time = end_time - start_time
                
                # If loading takes too long, we've found the limit
                if loading_time > 3.0:  # 3 second limit
                    break
                
                max_spaces_tested = spaces_count
                
                # Clean up
                floor_plan_widget.close()
                del floor_plan_widget
                del spaces
                del floor_geometries
                gc.collect()
                
            except Exception as e:
                # If we get an exception, we've exceeded the limit
                break
        
        # Should handle at least 200 spaces per floor
        assert max_spaces_tested >= 200, f"Could only handle {max_spaces_tested} spaces per floor, expected >= 200"

    def test_maximum_number_of_floors(self, qapp):
        """Test maximum number of floors that can be handled."""
        max_floors_tested = 0
        
        # Test increasing numbers of floors
        for floor_count in [5, 10, 15, 20, 25]:
            try:
                spaces, floor_geometries = create_large_floor_dataset(num_floors=floor_count, spaces_per_floor=50)
                
                floor_plan_widget = FloorPlanWidget()
                
                start_time = time.time()
                floor_plan_widget.set_floor_geometry(floor_geometries)
                floor_plan_widget.show()
                qapp.processEvents()
                end_time = time.time()
                
                loading_time = end_time - start_time
                
                # Test floor switching performance
                floor_ids = list(floor_geometries.keys())
                switch_start = time.time()
                for floor_id in floor_ids[:5]:  # Test first 5 floors
                    floor_plan_widget.set_current_floor(floor_id)
                    qapp.processEvents()
                switch_end = time.time()
                
                switch_time = switch_end - switch_start
                
                # If operations take too long, we've found the limit
                if loading_time > 2.0 or switch_time > 1.0:
                    break
                
                max_floors_tested = floor_count
                
                # Clean up
                floor_plan_widget.close()
                del floor_plan_widget
                del spaces
                del floor_geometries
                gc.collect()
                
            except Exception as e:
                break
        
        # Should handle at least 10 floors
        assert max_floors_tested >= 10, f"Could only handle {max_floors_tested} floors, expected >= 10"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # Verbose output for performance tests