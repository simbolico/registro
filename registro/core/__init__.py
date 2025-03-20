"""
Core models for resource-based database entities.

This module provides the main components for working with resources:
- Resource: The base model for all resources
- ResourceTypeBaseModel: Base class for domain models with resource capabilities
- ResourceBaseModel: Abstract base for resource models
"""

from registro.core.resource import Resource
from registro.core.resource_base import (
    ResourceTypeBaseModel,
    ResourceBaseModel,
    ResourceRelationshipMixin,
    ResourceModelType
)

__all__ = [
    "Resource",
    "ResourceTypeBaseModel",
    "ResourceBaseModel",
    "ResourceRelationshipMixin",
    "ResourceModelType"
]
