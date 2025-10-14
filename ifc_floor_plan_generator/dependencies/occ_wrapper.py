"""
OpenCASCADE dependency wrapper with graceful degradation.

Provides mock classes and graceful error handling when OCC is not available.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import OpenCASCADE
try:
    from OCC.Core import (
        gp_Pln, gp_Pnt, gp_Dir, gp_Ax3,
        TopoDS_Shape, TopoDS_Edge, TopoDS_Compound,
        BRepAlgoAPI_Section,
        BRep_Tool, BRep_Builder,
        TopExp_Explorer, TopAbs_EDGE, TopAbs_VERTEX,
        BRepAdaptor_Curve,
        GCPnts_UniformAbscissa,
        GeomAbs_Line, GeomAbs_Circle, GeomAbs_BSplineCurve,
        TopoDS,
        Bnd_Box, BRepBndLib_Add, BRepTools_ShapeSet
    )
    HAS_OCC = True
    logger.debug("OpenCASCADE successfully imported")
except ImportError as e:
    HAS_OCC = False
    logger.warning(f"OpenCASCADE not available: {e}")
    
    # Create mock classes for type hints and graceful degradation
    class MockOCCClass:
        """Mock class for OpenCASCADE objects when OCC is not available."""
        
        def __init__(self, *args, **kwargs):
            self._mock_name = self.__class__.__name__
            logger.debug(f"Created mock {self._mock_name} instance")
        
        def __getattr__(self, name):
            def mock_method(*args, **kwargs):
                logger.warning(f"Mock {self._mock_name}.{name}() called - OCC not available")
                return None
            return mock_method
        
        def __bool__(self):
            return False
        
        def __str__(self):
            return f"Mock{self._mock_name}"
        
        def __repr__(self):
            return f"Mock{self._mock_name}()"
    
    # Create mock classes for all OCC types
    gp_Pln = type('gp_Pln', (MockOCCClass,), {})
    gp_Pnt = type('gp_Pnt', (MockOCCClass,), {})
    gp_Dir = type('gp_Dir', (MockOCCClass,), {})
    gp_Ax3 = type('gp_Ax3', (MockOCCClass,), {})
    TopoDS_Shape = type('TopoDS_Shape', (MockOCCClass,), {})
    TopoDS_Edge = type('TopoDS_Edge', (MockOCCClass,), {})
    TopoDS_Compound = type('TopoDS_Compound', (MockOCCClass,), {})
    BRepAlgoAPI_Section = type('BRepAlgoAPI_Section', (MockOCCClass,), {})
    BRep_Tool = type('BRep_Tool', (MockOCCClass,), {})
    BRep_Builder = type('BRep_Builder', (MockOCCClass,), {})
    TopExp_Explorer = type('TopExp_Explorer', (MockOCCClass,), {})
    BRepAdaptor_Curve = type('BRepAdaptor_Curve', (MockOCCClass,), {})
    GCPnts_UniformAbscissa = type('GCPnts_UniformAbscissa', (MockOCCClass,), {})
    TopoDS = type('TopoDS', (MockOCCClass,), {})
    Bnd_Box = type('Bnd_Box', (MockOCCClass,), {})
    BRepBndLib_Add = type('BRepBndLib_Add', (MockOCCClass,), {})
    BRepTools_ShapeSet = type('BRepTools_ShapeSet', (MockOCCClass,), {})
    
    # Mock constants
    TopAbs_EDGE = 0
    TopAbs_VERTEX = 1
    GeomAbs_Line = 0
    GeomAbs_Circle = 1
    GeomAbs_BSplineCurve = 2


class OCCDependencyError(Exception):
    """Raised when OCC functionality is required but not available."""
    
    def __init__(self, operation: str, suggestion: str = None):
        self.operation = operation
        self.suggestion = suggestion or "Install OpenCASCADE with: conda install -c conda-forge opencascade"
        
        message = f"OpenCASCADE required for {operation} but not available. {self.suggestion}"
        super().__init__(message)


def require_occ(operation: str = "this operation"):
    """Decorator to require OCC for a function or method.
    
    Args:
        operation: Description of the operation requiring OCC
        
    Raises:
        OCCDependencyError: If OCC is not available
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not HAS_OCC:
                raise OCCDependencyError(operation)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_occ_status() -> Dict[str, Any]:
    """Get detailed status of OpenCASCADE availability.
    
    Returns:
        Dict with OCC status information
    """
    status = {
        "available": HAS_OCC,
        "version": None,
        "features": {
            "geometry_processing": HAS_OCC,
            "section_cutting": HAS_OCC,
            "shape_analysis": HAS_OCC
        }
    }
    
    if HAS_OCC:
        try:
            # Try to get OCC version if available
            import OCC
            if hasattr(OCC, '__version__'):
                status["version"] = OCC.__version__
        except:
            pass
    
    return status


def mock_occ_classes() -> Dict[str, type]:
    """Get dictionary of mock OCC classes for testing.
    
    Returns:
        Dict mapping class names to mock classes
    """
    return {
        'gp_Pln': gp_Pln,
        'gp_Pnt': gp_Pnt,
        'gp_Dir': gp_Dir,
        'gp_Ax3': gp_Ax3,
        'TopoDS_Shape': TopoDS_Shape,
        'TopoDS_Edge': TopoDS_Edge,
        'TopoDS_Compound': TopoDS_Compound,
        'BRepAlgoAPI_Section': BRepAlgoAPI_Section,
        'BRep_Tool': BRep_Tool,
        'BRep_Builder': BRep_Builder,
        'TopExp_Explorer': TopExp_Explorer,
        'BRepAdaptor_Curve': BRepAdaptor_Curve,
        'GCPnts_UniformAbscissa': GCPnts_UniformAbscissa,
        'TopoDS': TopoDS,
        'Bnd_Box': Bnd_Box,
        'BRepBndLib_Add': BRepBndLib_Add,
        'BRepTools_ShapeSet': BRepTools_ShapeSet,
    }


# Export all OCC classes (real or mock)
__all__ = [
    'HAS_OCC',
    'OCCDependencyError',
    'require_occ',
    'get_occ_status',
    'mock_occ_classes',
    # OCC classes
    'gp_Pln', 'gp_Pnt', 'gp_Dir', 'gp_Ax3',
    'TopoDS_Shape', 'TopoDS_Edge', 'TopoDS_Compound',
    'BRepAlgoAPI_Section', 'BRep_Tool', 'BRep_Builder',
    'TopExp_Explorer', 'BRepAdaptor_Curve', 'GCPnts_UniformAbscissa',
    'TopoDS', 'Bnd_Box', 'BRepBndLib_Add', 'BRepTools_ShapeSet',
    # Constants
    'TopAbs_EDGE', 'TopAbs_VERTEX',
    'GeomAbs_Line', 'GeomAbs_Circle', 'GeomAbs_BSplineCurve'
]