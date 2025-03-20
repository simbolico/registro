"""
Data models module for the Registro library.

This module provides base models and utilities for working with
database entities and resource identifiers.
"""

from registro.models.database import (
    DatabaseModel,
    TimestampedModel,
    NamedModel,
    datetime_with_timezone
)
from registro.models.rid import (
    RID,
    ServiceStr,
    InstanceStr,
    TypeStr,
    LocatorStr,
    generate_ulid
)
from registro.models.patterns import (
    RESERVED_WORDS,
    OBJECT_TYPE_API_NAME_PATTERN,
    LINK_TYPE_API_NAME_PATTERN,
    ACTION_TYPE_API_NAME_PATTERN,
    QUERY_TYPE_API_NAME_PATTERN,
    validate_string
)

__all__ = [
    # Database models
    "DatabaseModel",
    "TimestampedModel", 
    "NamedModel",
    "datetime_with_timezone",
    
    # RID classes
    "RID",
    "ServiceStr",
    "InstanceStr",
    "TypeStr",
    "LocatorStr",
    "generate_ulid",
    
    # Patterns and validation
    "RESERVED_WORDS",
    "OBJECT_TYPE_API_NAME_PATTERN",
    "LINK_TYPE_API_NAME_PATTERN",
    "ACTION_TYPE_API_NAME_PATTERN", 
    "QUERY_TYPE_API_NAME_PATTERN",
    "validate_string",
]
