"""
Unified base model for resource types in Registro.

This module provides the ResourceTypeBaseModel that serves as a base for
all resource types with automatic RID generation and timestamp management.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, TypeVar
from pydantic import BaseModel, Field

from .identity import RID, new_rid

T = TypeVar("T", bound="ResourceTypeBaseModel")

class ResourceTypeBaseModel(BaseModel):
    """
    Base model for all resource types with automatic RID generation and timestamps.
    
    This model provides:
    - Automatic RID generation using ULID
    - Created and updated timestamp management
    - Type name inference from class name
    - Touch method for updating timestamps
    """
    
    rid: RID = Field(default_factory=new_rid, description="Resource identifier")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the resource was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the resource was last updated"
    )
    
    model_config = {
        "arbitrary_types_allowed": True,  # Allow arbitrary types for future extensibility
        "validate_assignment": True,      # Ensure field validation on updates
        "use_enum_values": True,          # Use enum values instead of enum objects
    }
        
    @classmethod
    def type_name(cls) -> str:
        """
        Get the type name of the resource.
        
        Returns:
            str: The class name in lowercase
        """
        return cls.__name__.lower()
    
    def touch(self) -> None:
        """
        Update the updated_at timestamp to current time.
        
        This method uses object.__setattr__ to bypass any potential
        immutability constraints that might be in place.
        """
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))
    
    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Create a dictionary representation of the model.
        
        Args:
            **kwargs: Additional arguments to pass to the parent method
            
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        # Ensure we don't modify the original kwargs dict
        dump_kwargs = kwargs.copy()
        
        # Set default values if not provided
        if "exclude_none" not in dump_kwargs:
            dump_kwargs["exclude_none"] = True
            
        if "by_alias" not in dump_kwargs:
            dump_kwargs["by_alias"] = True
            
        return super().model_dump(**dump_kwargs)
