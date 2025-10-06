"""
Comprehensive Test Runner for Interactive Floor Plan Enhancement

Runs all unit tests, integration tests, and performance tests for the interactive floor plan enhancement.
Provides detailed reporting and performance metrics.
"""

import pytest
import sys
import os
import time
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def run_test_suite(test_file, description):
    """Run a specific test suite and return results."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Run pytest with detailed output
    result = pytest.main([
        test_file,
        "-v",  # Verbose output
        "-s",  # Don't capture output
        "--tb=short",  # Short traceback format
        "--durations=10",  # Show 10 slowest tests
        "-x"  # Stop on first failure
    ])
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n{description} completed in {duration:.2f} seconds")
    print(f"Result: {'PASSED' if result == 0 else 'FAILED'}")
    
    return result == 0, duration


def main():
    """Run all comprehensive tests for the interactive floor plan enhancement."""
    print("Interactive Floor Plan Enhancement - Comprehensive Test Suite")
    print("=" * 70)
    
    # Define test suites
    test_suites = [
        ("tests/test_floor_plan_widget.py", "Unit Tests - FloorPlanWidget Components"),
        ("tests/test_enhanced_geometry_extractor.py", "Unit Tests - Enhanced GeometryExtractor"),
        ("tests/test_enhanced_space_list_widget.py", "Unit Tests - Enhanced SpaceListWidget"),
        ("tests/test_ui_synchronization_integration.py", "Integration Tests - UI Synchronization"),
        ("tests/test_floor_switching_integration.py", "Integration Tests - Floor Switching"),
        ("tests/test_performance_large_floor_plans.py", "Performance Tests - Large Floor Plans"),
    ]
    
    # Track results
    results = []
    total_duration = 0
    
    # Run each test suite
    for test_file, description in test_suites:
        if os.path.exists(test_file):
            success, duration = run_test_suite(test_file, description)
            results.append((description, success, duration))
            total_duration += duration
        else:
            print(f"\nWarning: Test file {test_file} not found, skipping...")
            results.append((description, False, 0))
    
    # Print summary
    print(f"\n{'='*70}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*70}")
    
    passed_count = 0
    failed_count = 0
    
    for description, success, duration in results:
        status = "PASSED" if success else "FAILED"
        print(f"{description:<50} {status:>8} ({duration:>6.2f}s)")
        
        if success:
            passed_count += 1
        else:
            failed_count += 1
    
    print(f"\n{'='*70}")
    print(f"Total Test Suites: {len(results)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Total Duration: {total_duration:.2f} seconds")
    print(f"Overall Result: {'PASSED' if failed_count == 0 else 'FAILED'}")
    print(f"{'='*70}")
    
    # Return appropriate exit code
    return 0 if failed_count == 0 else 1


def run_specific_test_category(category):
    """Run tests for a specific category."""
    category_tests = {
        "unit": [
            ("tests/test_floor_plan_widget.py", "Unit Tests - FloorPlanWidget Components"),
            ("tests/test_enhanced_geometry_extractor.py", "Unit Tests - Enhanced GeometryExtractor"),
            ("tests/test_enhanced_space_list_widget.py", "Unit Tests - Enhanced SpaceListWidget"),
        ],
        "integration": [
            ("tests/test_ui_synchronization_integration.py", "Integration Tests - UI Synchronization"),
            ("tests/test_floor_switching_integration.py", "Integration Tests - Floor Switching"),
        ],
        "performance": [
            ("tests/test_performance_large_floor_plans.py", "Performance Tests - Large Floor Plans"),
        ]
    }
    
    if category not in category_tests:
        print(f"Unknown category: {category}")
        print(f"Available categories: {', '.join(category_tests.keys())}")
        return 1
    
    print(f"Running {category.upper()} tests for Interactive Floor Plan Enhancement")
    print("=" * 70)
    
    results = []
    total_duration = 0
    
    for test_file, description in category_tests[category]:
        if os.path.exists(test_file):
            success, duration = run_test_suite(test_file, description)
            results.append((description, success, duration))
            total_duration += duration
        else:
            print(f"\nWarning: Test file {test_file} not found, skipping...")
            results.append((description, False, 0))
    
    # Print category summary
    print(f"\n{'='*70}")
    print(f"{category.upper()} TEST SUMMARY")
    print(f"{'='*70}")
    
    passed_count = sum(1 for _, success, _ in results if success)
    failed_count = len(results) - passed_count
    
    for description, success, duration in results:
        status = "PASSED" if success else "FAILED"
        print(f"{description:<50} {status:>8} ({duration:>6.2f}s)")
    
    print(f"\nPassed: {passed_count}, Failed: {failed_count}, Duration: {total_duration:.2f}s")
    
    return 0 if failed_count == 0 else 1


def run_quick_tests():
    """Run a quick subset of tests for rapid feedback."""
    print("Interactive Floor Plan Enhancement - Quick Test Suite")
    print("=" * 60)
    
    # Quick tests - focus on core functionality
    quick_tests = [
        ("tests/test_floor_plan_widget.py::TestFloorPlanWidget::test_initialization", "FloorPlanWidget Init"),
        ("tests/test_enhanced_geometry_extractor.py::TestGeometryExtractorInitialization", "GeometryExtractor Init"),
        ("tests/test_enhanced_space_list_widget.py::TestEnhancedSpaceListWidget::test_initialization_with_floor_filter", "SpaceListWidget Floor Filter"),
        ("tests/test_ui_synchronization_integration.py::TestBidirectionalSpaceSelection::test_space_list_to_floor_plan_selection", "UI Synchronization"),
    ]
    
    results = []
    total_duration = 0
    
    for test_spec, description in quick_tests:
        print(f"\nRunning {description}...")
        start_time = time.time()
        
        result = pytest.main([
            test_spec,
            "-v",
            "--tb=short",
            "-x"
        ])
        
        end_time = time.time()
        duration = end_time - start_time
        success = result == 0
        
        results.append((description, success, duration))
        total_duration += duration
        
        print(f"{description}: {'PASSED' if success else 'FAILED'} ({duration:.2f}s)")
    
    # Quick summary
    print(f"\n{'='*60}")
    print("QUICK TEST SUMMARY")
    print(f"{'='*60}")
    
    passed_count = sum(1 for _, success, _ in results if success)
    failed_count = len(results) - passed_count
    
    print(f"Passed: {passed_count}, Failed: {failed_count}")
    print(f"Total Duration: {total_duration:.2f} seconds")
    print(f"Result: {'PASSED' if failed_count == 0 else 'FAILED'}")
    
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick":
            exit_code = run_quick_tests()
        elif command in ["unit", "integration", "performance"]:
            exit_code = run_specific_test_category(command)
        elif command == "help":
            print("Interactive Floor Plan Enhancement Test Runner")
            print("\nUsage:")
            print("  python run_comprehensive_tests.py           # Run all tests")
            print("  python run_comprehensive_tests.py quick     # Run quick test subset")
            print("  python run_comprehensive_tests.py unit      # Run unit tests only")
            print("  python run_comprehensive_tests.py integration # Run integration tests only")
            print("  python run_comprehensive_tests.py performance # Run performance tests only")
            print("  python run_comprehensive_tests.py help      # Show this help")
            exit_code = 0
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' for available commands")
            exit_code = 1
    else:
        exit_code = main()
    
    sys.exit(exit_code)