"""
Decorators for Registro resources.

This version preserves annotations, Field(...) definitions, validators,
methods, docstrings, and model_config while creating proper SQLModel table
classes without using exec().
"""

from typing import Optional, Any, Dict
from types import new_class
from registro.core.resource_base import ResourceTypeBaseModel
from registro.config import settings

# Base class for table-based resources
class ResourceTableBase(ResourceTypeBaseModel, table=False):
    """Base class for resources that should be database tables."""
    pass

_SKIP_ATTRS = {"__dict__", "__weakref__", "__module__", "__doc__", "__annotations__", "__qualname__"}

def _build_sqlmodel_class(
    name: str,
    base: type,
    *,
    table: bool,
    attrs: Dict[str, Any],
) -> type:
    """
    Build a new SQLModel (or non-table) class with SQLModel's metaclass
    using types.new_class so we can pass kwds={'table': True}.
    """
    def exec_body(ns):
        # Maintain module & doc before validators are processed
        ns["__module__"] = attrs.get("__module__", base.__module__)
        if attrs.get("__doc__"):
            ns["__doc__"] = attrs["__doc__"]

        # Annotations must be present so Field(...) are correctly parsed
        ns["__annotations__"] = dict(attrs.get("__annotations__", {}))

        # Copy everything else (methods, validators, constants, model_config, etc.)
        for k, v in attrs.items():
            if k in _SKIP_ATTRS:
                continue
            ns[k] = v

    # kwds propagates to SQLModel's metaclass (equivalent to class X(SQLModel, table=True))
    return new_class(name, (base,), kwds={"table": table}, exec_body=exec_body)

def resource(
    *,
    service: Optional[str] = None,
    instance: Optional[str] = None,
    resource_type: Optional[str] = None,
    is_table: bool = True,
    tablename: Optional[str] = None,
):
    """
    Decorator to transform a user-defined class into a Registro resource.

    Args:
        service: Overrides default service (settings.DEFAULT_SERVICE if omitted).
        instance: Overrides default instance (settings.DEFAULT_INSTANCE if omitted).
        resource_type: Explicit resource type (defaults to class name in lowercase).
        is_table: Create a real table model (True) or a non-table model (False).
        tablename: Optional explicit __tablename__ when is_table=True.
    """
    def decorator(cls):
        actual_resource_type = resource_type or cls.__name__.lower()
        # Start with the original attributes so validators/methods are preserved
        attrs = dict(cls.__dict__)

        # Force the resource type (needed by ResourceBaseModel.__init_subclass__)
        attrs["__resource_type__"] = actual_resource_type

        # If table, ensure a tablename is present
        if is_table:
            attrs.setdefault("__tablename__", (tablename or cls.__name__.lower()))

        # Choose base and create the derived class through SQLModel's metaclass
        base = ResourceTableBase if is_table else ResourceTypeBaseModel
        Derived = _build_sqlmodel_class(cls.__name__, base, table=is_table, attrs=attrs)

        # Stash defaults for the auto-create-resource hook
        Derived._service = service or settings.DEFAULT_SERVICE
        Derived._instance = instance or settings.DEFAULT_INSTANCE

        return Derived

    return decorator 