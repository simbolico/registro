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
__version__ = "0.1.2"

# Core exports
from registro.core.resource_base import ResourceTypeBaseModel
from registro.core.resource import Resource

# Decorators
from registro.decorators import resource

# Make isort happy
__all__ = [
    "ResourceTypeBaseModel",
    "Resource",
    "resource",
]
