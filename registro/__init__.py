"""
Registro: Resource-based model system for SQLModel
==================================================

Registro provides a resource-based approach to SQLModel, offering:

- Resource identifiers (RIDs) for globally unique identification
- Automatic resource creation and relationship management
- Validation and pattern enforcement
- Integration with SQLModel and Pydantic v2

Basic usage:

```python
from registro import Resource, ResourceBase
from sqlmodel import SQLModel, Field

class MyModel(ResourceBase, table=True):
    __resource_type__ = "my-model"
    
    name: str = Field(default="")
    value: int = Field(default=0)
```
"""

__version__ = "0.1.0"

# Export core classes
from registro.core.resource import Resource
from registro.core.resource_base import ResourceBase, ResourceBaseModel

# Make these accessible at the package level
__all__ = [
    "Resource",
    "ResourceBase",
    "ResourceBaseModel",
]
