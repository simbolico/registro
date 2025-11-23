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
from sqlmodel import Field, Relationship, JSON, Column
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

    # Arbitrary tags/metadata for governance and indexing
    meta_tags: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
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
        # 1. Se o campo não é protegido, passa direto (fast path)
        if name not in self._immutable_fields:
            super().__setattr__(name, value)
            return
        
        # 2. Verificação de Estado de Inicialização
        # Se o atributo já existe e tem um valor não nulo, consideramos que o objeto está inicializado
        # para aquele campo específico. Apenas bloqueamos se estamos tentando modificar um valor
        # já existente para um valor diferente.
        
        # Durante o __init__, os atributos ainda não existem, então hasattr() retorna False
        if not hasattr(self, name):
            # Campo não existe ainda, permitimos a criação (durante inicialização)
            super().__setattr__(name, value)
            return
        
        # Campo existe, verifica se estamos tentando modificar para um valor diferente
        current_value = getattr(self, name)
        if current_value is None:
            # Valor atual é None (pode acontecer em alguns casos), permitimos a definição
            super().__setattr__(name, value)
            return
        
        # Campo existe e tem um valor não nulo, só permitimos se o valor for o mesmo
        if value != current_value:
            raise AttributeError(
                f"Cannot modify immutable field '{name}'. "
                f"Critical fields {self._immutable_fields} are immutable after initialization."
            )
        
        # Valor é o mesmo, permitimos (sem efeito prático)
        super().__setattr__(name, value)
    
    def __init__(self, **data):
        """
        Initialize a Resource instance with auto-generated fields if not provided.
        
        Args:
            **data: Resource field values, can include 'id', 'rid', 'service', 'instance', 'resource_type'
        """
        # Handle custom RID case
        if "rid" in data and data["rid"] is not None:
            # Validate RID format
            rid_parts = data["rid"].split('.')
            if len(rid_parts) != 5:
                raise ValueError(f"Invalid RID format: '{data['rid']}' must have 5 components")
            
            # Validate RID prefix
            if rid_parts[0] != settings.RID_PREFIX:
                raise ValueError(f"Invalid RID prefix: '{rid_parts[0]}' must be '{settings.RID_PREFIX}'")
            
            # Extract components from RID
            _, service, instance, resource_type, locator = rid_parts
            
            # Set the ID from the RID if not provided
            if "id" not in data or data["id"] is None:
                data["id"] = locator
            elif data["id"] != locator:
                raise ValueError(f"RID locator '{locator}' does not match id '{data['id']}'")
            
            # Set components from RID if not provided
            if "service" not in data or data["service"] is None:
                data["service"] = service
            if "instance" not in data or data["instance"] is None:
                data["instance"] = instance
            if "resource_type" not in data or data["resource_type"] is None:
                data["resource_type"] = resource_type
        else:
            # No RID provided, generate one
            
            # Generate ID first if not provided
            if "id" not in data or data["id"] is None:
                data["id"] = generate_ulid()
            
            # Apply defaults for missing components
            if "service" not in data or data["service"] is None:
                data["service"] = settings.DEFAULT_SERVICE
            if "instance" not in data or data["instance"] is None:
                data["instance"] = settings.DEFAULT_INSTANCE
            if "resource_type" not in data or data["resource_type"] is None:
                data["resource_type"] = "resource"
            
            # Generate RID with the components we have
            data["rid"] = f"{settings.RID_PREFIX}.{data['service']}.{data['instance']}.{data['resource_type']}.{data['id']}"
        
        super().__init__(**data)
    
    @model_validator(mode="before")
    @classmethod
    def prepare_fields(cls, values):
        """
        Prepare and validate fields before Pydantic initialization.
        
        This method ensures ID is generated if not provided and ensures all
        required components for RID construction are available.
        
        Args:
            values: The values being validated
        
        Returns:
            The values with ID added if needed
        """
        # This validator is kept as a backup, but most work is now done in __init__
        return values
    
    @model_validator(mode="after")
    def ensure_rid_consistency(self):
        """
        Ensure RID is properly constructed and consistent with field values.
        
        This validator is now mostly handled in __init__, but kept for compatibility.
        It just ensures the RID is properly formatted.
        
        Returns:
            The validated model instance
        
        Raises:
            ValueError: If the RID is invalid format
        """
        # If RID exists, validate its format
        if self.rid:
            # Validate RID format
            rid_parts = self.rid.split('.')
            if len(rid_parts) != 5:
                raise ValueError(f"Invalid RID format: '{self.rid}' must have 5 components")
            
            # Validate RID prefix
            if rid_parts[0] != settings.RID_PREFIX:
                raise ValueError(f"Invalid RID prefix: '{rid_parts[0]}' must be '{settings.RID_PREFIX}'")
            
            # Extract components from RID
            _, service, instance, resource_type, locator = rid_parts
            
            # Update components from RID if they weren't explicitly provided
            # Don't override if they were explicitly set in the constructor
            if not self.service or self.service == settings.DEFAULT_SERVICE:
                self.service = service
            if not self.instance or self.instance == settings.DEFAULT_INSTANCE:
                self.instance = instance
            if not self.resource_type or self.resource_type == "resource":
                self.resource_type = resource_type
            
            # Ensure ID matches the locator from RID
            if locator != self.id:
                # This is an error - the ID should match the RID locator
                raise ValueError(f"RID locator '{locator}' does not match id '{self.id}'")
        else:
            # No RID provided, generate one from components
            # Ensure we have default values
            if not self.service:
                self.service = settings.DEFAULT_SERVICE
            if not self.instance:
                self.instance = settings.DEFAULT_INSTANCE
            if not self.resource_type:
                self.resource_type = "resource"
                
            # Generate RID
            self.rid = f"{settings.RID_PREFIX}.{self.service}.{self.instance}.{self.resource_type}.{self.id}"
        
        return self 
