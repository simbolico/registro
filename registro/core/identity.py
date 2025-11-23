"""
Centralized identity management for Registro resources.

This module provides the core identity types and functions for generating
unique resource identifiers across the system.
"""

from typing import NewType
from registro.models.rid import generate_ulid

# Type alias for Resource Identifier
RID = NewType("RID", str)

def new_rid() -> RID:
    """
    Generate a new Resource Identifier (RID) using ULID.
    
    Returns:
        RID: A new unique resource identifier
    """
    return RID(generate_ulid())
