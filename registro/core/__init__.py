"""
Core models for resource-based database entities.

This module provides the main components for working with resources:
- Resource: The base model for all resources
- ResourceTypeBaseModel: Base class for domain models with resource capabilities
- ResourceBaseModel: Abstract base for resource models
- Identity: Centralized identity management
- Registry: Global type registry for resource types
"""

from registro.core.resource import Resource
from registro.core.resource_base import (
    ResourceTypeBaseModel,
    ResourceBaseModel,
    ResourceRelationshipMixin,
    ResourceModelType
)
from registro.core.identity import RID, new_rid
from registro.core.simple_resource_base import ResourceTypeBaseModel as SimpleResourceTypeBaseModel
from registro.core.registry import registry

__all__ = [
    "Resource",
    "ResourceTypeBaseModel",
    "ResourceBaseModel",
    "ResourceRelationshipMixin",
    "ResourceModelType",
    "RID",
    "new_rid",
    "SimpleResourceTypeBaseModel",
    "registry"
]
