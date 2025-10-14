#!/usr/bin/env python3
"""
IFC Floor Plan Generator - DEPRECATED

This file has been replaced by the new CLI interface.
Please use ifc_floor_plan_generator_cli.py instead.

For help with the new interface, run:
python ifc_floor_plan_generator_cli.py --help
"""

import sys
import os

print("=" * 60)
print("DEPRECATED: This script has been replaced")
print("=" * 60)
print()
print("Please use the new CLI interface instead:")
print("  python ifc_floor_plan_generator_cli.py --help")
print()
print("Example usage:")
print("  python ifc_floor_plan_generator_cli.py example_config.json")
print("  python ifc_floor_plan_generator_cli.py config.json --verbose")
print()
print("For configuration help:")
print("  python ifc_floor_plan_generator_cli.py --help-config")
print("=" * 60)

# Redirect to new CLI if arguments are provided
if len(sys.argv) > 1:
    print("\nAttempting to redirect to new CLI...")
    try:
        from ifc_floor_plan_generator.cli import main
        sys.exit(main())
    except ImportError as e:
        print(f"Error importing new CLI: {e}")
        print("Please ensure all dependencies are installed.")
        sys.exit(1)

sys.exit(1)

