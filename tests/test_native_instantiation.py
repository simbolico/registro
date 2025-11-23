"""
Test native instantiation of Resource without monkey patches.

This test verifies that the Resource class can be instantiated natively
by Pydantic v2/SQLModel without requiring external monkey patches.
"""

import pytest
from registro.core.resource import Resource


def test_create_resource_native():
    """
    Test that Resource can be created natively without monkey patches.
    
    This is the critical test that should pass after fixing the 
    __setattr__ implementation to properly check Pydantic initialization.
    """
    # Create a resource with minimal data
    r = Resource(service="test", resource_type="unit")
    
    # Verify basic properties
    assert r.rid is not None
    assert r.service == "test"
    assert r.resource_type == "unit"
    assert r.id is not None
    
    # Verify RID format
    rid_parts = r.rid.split('.')
    assert len(rid_parts) == 5
    assert rid_parts[0] == "ri"  # Default prefix
    assert rid_parts[1] == "test"  # Service
    assert rid_parts[2] == "prod"  # Default instance
    assert rid_parts[3] == "unit"  # Resource type
    assert rid_parts[4] == r.id  # ID should match


def test_resource_immutability_after_creation():
    """
    Test that immutable fields cannot be modified after creation.
    
    This verifies that our __setattr__ fix doesn't break immutability.
    """
    r = Resource(service="test", resource_type="unit")
    
    # Store original values
    original_id = r.id
    original_rid = r.rid
    original_service = r.service
    original_instance = r.instance
    original_type = r.resource_type
    
    # Attempting to modify immutable fields should raise AttributeError
    with pytest.raises(AttributeError):
        r.service = "hacked"
    
    with pytest.raises(AttributeError):
        r.instance = "hacked"
        
    with pytest.raises(AttributeError):
        r.resource_type = "hacked"
        
    with pytest.raises(AttributeError):
        r.id = "hacked"
        
    with pytest.raises(AttributeError):
        r.rid = "hacked"
    
    # Verify values didn't change
    assert r.id == original_id
    assert r.rid == original_rid
    assert r.service == original_service
    assert r.instance == original_instance
    assert r.resource_type == original_type


def test_resource_with_custom_rid():
    """
    Test creating a Resource with a custom RID.
    
    This verifies that custom RIDs are preserved and components
    are correctly extracted from them.
    """
    custom_rid = "ri.customsvc.dev.custom.01H8X6Z4X2Y3Z4A5B6C7D8E9F0"
    r = Resource(rid=custom_rid)
    
    # Verify RID is preserved
    assert r.rid == custom_rid
    
    # Verify components are extracted correctly
    assert r.service == "customsvc"
    assert r.instance == "dev"
    assert r.resource_type == "custom"
    assert r.id == "01H8X6Z4X2Y3Z4A5B6C7D8E9F0"


def test_resource_defaults():
    """
    Test that Resource uses configured defaults correctly.
    """
    # Create resource with no explicit values
    r = Resource()
    
    # Verify defaults are applied
    assert r.service == "default"  # DEFAULT_SERVICE
    assert r.instance == "prod"  # DEFAULT_INSTANCE
    assert r.resource_type == "resource"  # Default type
    
    # Verify RID is generated with defaults
    rid_parts = r.rid.split('.')
    assert len(rid_parts) == 5
    assert rid_parts[1] == "default"
    assert rid_parts[2] == "prod"
    assert rid_parts[3] == "resource"


def test_resource_mutable_fields():
    """
    Test that non-immutable fields can be modified normally.
    """
    r = Resource(service="test", resource_type="unit")
    
    # meta_tags should be mutable
    assert r.meta_tags == {}
    r.meta_tags["key"] = "value"
    assert r.meta_tags == {"key": "value"}
    
    # Other non-immutable fields (if any) should also be modifiable
