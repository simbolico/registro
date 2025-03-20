"""
Resource model for unique resource identification.

This module defines the Resource model, which provides a structured
approach to identifying entities across systems with Resource Identifiers (RIDs).
Each Resource has:
- A globally unique identifier (ULID)
- A structured RID (service.instance.type.id)
- Service, instance, and type metadata
- Lifecycle timestamps

Resources are immutable after creation, with critical fields protected from modification.
"""

from typing import Optional, List, Any, ForwardRef, ClassVar, Dict, Set
from sqlmodel import Field, Relationship
from pydantic import field_validator, model_validator, ValidationInfo, ConfigDict
from sqlalchemy import String, event, insert
from sqlalchemy.orm import mapped_column, object_session
import ulid
import sqlalchemy.schema
from datetime import datetime, timezone
import logging
import time
import random

from registro.models.database import TimestampedModel, datetime_with_timezone
from registro.models.rid import RID, ServiceStr, InstanceStr, TypeStr, generate_ulid
from registro.config import settings

logger = logging.getLogger(__name__)

class Resource(TimestampedModel, table=True):
    """
    Base model for resources with a ULID id and a constructed rid.
    
    Attributes:
        id (str): Auto-generated monotonic ULID identifier (primary key, immutable).
        rid (str): Constructed resource identifier (e.g., 'ri.service.instance.type.id', unique, immutable).
        service (ServiceStr): Service or domain (e.g., 'users', immutable).
        instance (InstanceStr): Instance or environment (e.g., 'main', immutable).
        resource_type (TypeStr): Type of resource (e.g., 'user', immutable).
        created_at, updated_at, archived_at, deleted_at, expired_at: Inherited timestamps.
    
    Uniqueness:
        - Monotonic ULID generation prevents collisions even in concurrent scenarios
        - Composite indexes and unique constraints at the database level
        - Multi-component RID structure reduces collision probability
    """
    
    # Critical fields are enforced as immutable via __setattr__
    
    __tablename__ = "resource"
    
    # Define SQLAlchemy table constraints and indexes for performance optimization
    __table_args__ = (
        # Composite index for common query patterns (find resources by service+instance)
        sqlalchemy.schema.Index("idx_resource_service_instance", "service", "instance"),
        
        # Composite index for looking up resources by service+type
        sqlalchemy.schema.Index("idx_resource_service_type", "service", "resource_type"),
        
        # Full composite index for RID components (excluding the actual ID)
        sqlalchemy.schema.Index("idx_resource_composite", "service", "instance", "resource_type"),
        
        # Ensure RID uniqueness at the database level
        sqlalchemy.schema.UniqueConstraint("rid", name="uq_resource_rid"),
        
        # Ensure ID uniqueness at the database level
        sqlalchemy.schema.UniqueConstraint("id", name="uq_resource_id")
    )
    
    id: str = Field(
        default_factory=generate_ulid,  # Use the safe generate_ulid function
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        description="Auto-generated monotonic ULID identifier, immutable once set"
    )
    
    rid: str = Field(
        index=True, 
        unique=True, 
        nullable=False,
        description="Constructed resource identifier (e.g., 'ri.service.instance.type.id'), immutable once set"
    )
    
    service: ServiceStr = Field(
        index=True,
        description="Service or domain identifier (e.g., 'users'), immutable once set"
    )
    
    instance: InstanceStr = Field(
        index=True,
        description="Instance or environment identifier (e.g., 'main'), immutable once set"
    )
    
    resource_type: TypeStr = Field(
        index=True,
        description="Type of resource (e.g., 'user'), immutable once set"
    )
    
    # Field-level immutability
    _immutable_fields: ClassVar[Set[str]] = {
        "id", "rid", "service", "instance", "resource_type"
    }
    
    def __setattr__(self, name: str, value: Any) -> None:
        """
        Override __setattr__ to enforce field-level immutability on critical fields.
        
        Critical fields (id, rid, service, instance, resource_type) cannot be modified after
        initialization. Other fields remain mutable.
        
        Args:
            name (str): Name of the attribute to set
            value (Any): Value to set
        
        Raises:
            AttributeError: If attempting to modify an immutable field after initialization
        """
        if name in self._immutable_fields and hasattr(self, name):
            raise AttributeError(
                f"Cannot modify immutable field '{name}'. Critical fields {self._immutable_fields} "
                "are immutable after initialization."
            )
        super().__setattr__(name, value)
    
    def __init__(self, **data):
        """
        Initialize a Resource instance with auto-generated fields if not provided.
        
        Args:
            **data: Resource field values, can include 'id', 'rid', 'service', 'instance', 'resource_type'
        """
        # Generate ID first if not provided
        if "id" not in data or data["id"] is None:
            data["id"] = generate_ulid()
        
        # Get the required components with fallbacks
        service = data.get("service", settings.DEFAULT_SERVICE)
        instance = data.get("instance", settings.DEFAULT_INSTANCE)
        resource_type = data.get("resource_type", "resource")
        locator = data["id"]
        
        # Generate the RID if not provided
        if "rid" not in data or data["rid"] is None:
            data["rid"] = f"{settings.RID_PREFIX}.{service}.{instance}.{resource_type}.{locator}"
            logger.debug(f"RID generated in __init__: {data['rid']}")
        
        super().__init__(**data)
    
    @model_validator(mode="before")
    @classmethod
    def generate_rid(cls, values):
        """
        Generate the rid using service, instance, resource_type, and an auto-generated ULID id.
        
        This is a backup validator to ensure RID is set if not generated in __init__.
        
        Args:
            values: The values being validated
        
        Returns:
            The values with RID added if needed
        """
        # Skip if rid is already set
        if values.get("rid"):
            return values
        
        # Generate ID first if not provided
        if "id" not in values or values["id"] is None:
            values["id"] = generate_ulid()
        
        # Get the required components with fallbacks
        service = values.get("service", settings.DEFAULT_SERVICE)
        instance = values.get("instance", settings.DEFAULT_INSTANCE)
        resource_type = values.get("resource_type", "resource")
        locator = values["id"]
        
        # Now generate the RID
        values["rid"] = f"{settings.RID_PREFIX}.{service}.{instance}.{resource_type}.{locator}"
        logger.debug(f"RID generated in validator: {values['rid']}")
        return values
    
    @model_validator(mode="after")
    @classmethod
    def check_rid_consistency(cls, model):
        """
        Ensure rid matches the format based on service, instance, resource_type, and id.
        
        This validator ensures that:
        1. The RID follows the correct format: ri.<service>.<instance>.<resource_type>.<id>
        2. The components in the RID match the actual field values
        3. The RID is properly constructed with all required components
        
        Args:
            model: The Resource model instance being validated
        
        Returns:
            The validated model instance
        
        Raises:
            ValueError: If the RID is invalid or inconsistent with other fields
        """
        # If rid is still not set (shouldn't happen, but just in case)
        if not model.rid:
            model.rid = f"{settings.RID_PREFIX}.{model.service}.{model.instance}.{model.resource_type}.{model.id}"
            logger.debug(f"RID generated in consistency check: {model.rid}")
        
        # Split RID into components
        rid_parts = model.rid.split('.')
        
        # Validate RID format
        if len(rid_parts) != 5:
            raise ValueError(f"Invalid RID format: '{model.rid}' must have 5 components")
        
        # Validate RID prefix
        if rid_parts[0] != settings.RID_PREFIX:
            raise ValueError(f"Invalid RID prefix: '{rid_parts[0]}' must be '{settings.RID_PREFIX}'")
        
        # Validate components match field values
        if rid_parts[1] != model.service:
            raise ValueError(f"RID service '{rid_parts[1]}' does not match field value '{model.service}'")
        if rid_parts[2] != model.instance:
            raise ValueError(f"RID instance '{rid_parts[2]}' does not match field value '{model.instance}'")
        if rid_parts[3] != model.resource_type:
            raise ValueError(f"RID resource_type '{rid_parts[3]}' does not match field value '{model.resource_type}'")
        if rid_parts[4] != model.id:
            raise ValueError(f"RID id '{rid_parts[4]}' does not match field value '{model.id}'")
        
        return model 