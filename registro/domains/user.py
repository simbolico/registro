"""
User domain model for Registro.

This module defines the User resource type as an example of how to
extend the ResourceTypeBaseModel for domain-specific entities.
"""

from typing import Optional
from pydantic import Field, EmailStr

from registro.core.simple_resource_base import ResourceTypeBaseModel
from registro.core.registry import registry

class User(ResourceTypeBaseModel):
    """
    User resource model.
    
    This is an example of how to extend ResourceTypeBaseModel for
    domain-specific entities. It includes common user attributes
    and automatic RID/timestamp management.
    """
    
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    username: Optional[str] = Field(None, max_length=50, description="Username for login")
    is_active: bool = Field(True, description="Whether the user account is active")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "username": "johndoe",
                "is_active": True
            }
        }
    }

# Register the User model with the global registry
registry.register("user", User)
