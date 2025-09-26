"""
Data Module

Data models and structures for IFC spatial data representation.
"""

from .space_model import SpaceData, Space
from .surface_model import SurfaceData, Surface
from .space_boundary_model import SpaceBoundaryData
from .relationship_model import RelationshipData
from .space_repository import SpaceRepository
from .room_schedule_model import RoomSchedule

__all__ = [
    'SpaceData', 'Space',
    'SurfaceData', 'Surface',
    'SpaceBoundaryData',
    'RelationshipData',
    'SpaceRepository',
    'RoomSchedule'
]