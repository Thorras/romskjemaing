"""Simple end-to-end test to verify pytest discovery."""

import pytest

def test_simple():
    """Simple test to verify pytest works."""
    assert True

class TestSimpleE2E:
    """Simple test class."""
    
    def test_class_method(self):
        """Simple class method test."""
        assert True