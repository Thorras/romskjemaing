"""
Unit tests for geometry generation functionality - Task 5.3 Implementation.

This test file specifically addresses the requirements for Task 5.3:
- Test shape generation with different IFC elements
- Test geometry caching functionality  
- Test error handling for failed shape generation
- Requirements: 4.1, 4.2, 4.3, 4.4, 8.3
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from ifc_floor_plan_generator.geometry.engine import GeometryEngine
from ifc_floor_plan_generator.models import GeometryConfig, BoundingBox
from ifc_floor_plan_generator.errors.handler import ErrorHandler
from ifc_floor_plan_generator.errors.exceptions import GeometryShapeError


class MockIfcElement:
