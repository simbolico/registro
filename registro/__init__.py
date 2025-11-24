"""
Registro - A resource management framework for Python.

Registro provides a consistent way to create, access, and manage resources
in your application. It generates structured resource identifiers (RIDs)
that uniquely identify resources across services and instances.

Core Components:
- ResourceTypeBaseModel: Base class for creating resource types
- Resource: Central registry for all resources
- @resource: Decorator for creating resources
"""

# Version
__version__ = "0.6.0"

# Core exports
from registro.core.resource_base import ResourceTypeBaseModel
from registro.core.resource import Resource
from registro.core.domain import DomainResource

# Decorators
from registro.decorators import resource

# New Identity & Registry System
from registro.core.identity import RID, new_rid, parse_rid, get_resource_type_from_rid
from registro.core.global_registry import registry, register, get, create_instance

# Make isort happy
__all__ = [
    "ResourceTypeBaseModel",
    "Resource",
    "DomainResource",
    "resource",
    # Identity & Registry
    "RID",
    "new_rid",
    "parse_rid", 
    "get_resource_type_from_rid",
    "registry",
    "register",
    "get",
    "create_instance",
]
