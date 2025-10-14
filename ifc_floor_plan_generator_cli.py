#!/usr/bin/env python3
"""
IFC Floor Plan Generator - Command Line Interface

This is the main entry point for the IFC Floor Plan Generator CLI.
It replaces the old ifc_floor_plan_generator.py with a proper CLI interface.
"""

import sys
import os

# Add the package to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ifc_floor_plan_generator.cli import main

if __name__ == '__main__':
    sys.exit(main())