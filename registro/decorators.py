"""
Decorators for Registro resources.

This module provides decorators that simplify the creation and configuration of
Registro resources, reducing boilerplate code and making the API more user-friendly.
"""

from typing import Optional, Any, Dict, ClassVar
from sqlmodel import Field, SQLModel
from registro.core.resource_base import ResourceTypeBaseModel
from registro.config import settings

# Base class for table-based resources
class ResourceTableBase(ResourceTypeBaseModel, table=False):
    """Base class for resources that should be database tables."""
    pass

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

        # 4) Dynamically create a new class that inherits from the appropriate base
        if is_table:
            base_class = ResourceTableBase
            # Use exec to create a proper class with table=True
            class_name = cls.__name__
            class_code = f"""
class {class_name}(ResourceTableBase, table=True):
    __resource_type__ = "{actual_resource_type}"
    __tablename__ = "{cls.__name__.lower()}"
"""
            # Add fields (but skip complex Field objects for now)
            for name, value in cls.__dict__.items():
                if (not name.startswith('_') and 
                    name not in ['__annotations__', '__module__', '__qualname__', '__doc__']):
                    # Skip Field objects that have FieldInfo in their type
                    if 'FieldInfo' in str(type(value)):
                        continue
                    try:
                        class_code += f"    {name} = {repr(value)}\n"
                    except:
                        # Skip if repr fails
                        pass
            
            # Execute
            exec_globals = globals().copy()
            exec_globals['ResourceTableBase'] = ResourceTableBase
            local_vars = {}
            exec(class_code, exec_globals, local_vars)
            Derived = local_vars[class_name]
        else:
            base_class = ResourceTypeBaseModel
            Derived = type(cls.__name__, (base_class,), new_attrs)

        # 5) Set the _service and _instance so that _create_resource picks them up
        Derived._service = service or settings.DEFAULT_SERVICE
        Derived._instance = instance or settings.DEFAULT_INSTANCE

        return Derived

    return decorator 