"""
Decorators for Registro resources.

This module provides decorators that simplify the creation and configuration of
Registro resources, reducing boilerplate code and making the API more user-friendly.
"""

from typing import Optional, Any, Dict, Type
from sqlmodel import Field
from registro.core.resource_base import ResourceTypeBaseModel
from registro.config import settings

def resource(
    *,
    service: Optional[str] = None,
    instance: Optional[str] = None,
    resource_type: Optional[str] = None,
    is_table: bool = True
):
    """
    Decorator to transform a user-defined class into a Registro resource.

    Args:
        service: The service name for this resource. Defaults to settings.DEFAULT_SERVICE.
        instance: The instance name for this resource. Defaults to settings.DEFAULT_INSTANCE.
        resource_type: The resource type identifier. Defaults to the lowercase class name.
        is_table: Whether this resource should be a database table. Defaults to True.

    Returns:
        A decorator function that transforms the class into a Registro resource.

    Example:
        ```python
        from registro import resource
        from sqlmodel import Field

        @resource(resource_type="product")  # is_table=True by default
        class Product:
            name: str = Field(...)
            price: float = Field(...)
        ```
    """
    def decorator(cls):
        # 1) Determine the final resource_type from argument or class name
        actual_resource_type = resource_type or cls.__name__.lower()

        # 2) Copy over user-defined attributes (fields, methods, etc.)
        new_attrs = dict(cls.__dict__)
        for unwanted in ("__dict__", "__weakref__"):
            new_attrs.pop(unwanted, None)

        # 3) Force the resource_type at the class level
        new_attrs["__resource_type__"] = actual_resource_type

        # If the user wants to create an actual database table
        if is_table:
            new_attrs["__tablename__"] = cls.__name__.lower()

        # 4) Dynamically create a new class that inherits from ResourceTypeBaseModel
        #    (which already inherits from SQLModel).
        Derived = type(cls.__name__, (ResourceTypeBaseModel,), new_attrs)

        # 5) Set the _service and _instance so that _create_resource picks them up
        Derived._service = service or settings.DEFAULT_SERVICE
        Derived._instance = instance or settings.DEFAULT_INSTANCE

        return Derived

    return decorator 