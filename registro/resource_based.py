"""
resource_based.py
--------------
This module defines the core resource model system for the Ontologia framework.
It provides abstract base classes for resource-based data models with automatic
Resource creation, validation, and relationship management.

The module implements three main components:
1. ResourceBaseModel: Abstract base for resource attributes and behavior
2. ResourceRelationshipMixin: Provides relationship to Resource model using SQLModel's Relationship
3. BaseResourceType: Combines the above for complete resource functionality

Key Features:
- Automatic Resource creation when instances are added to session
- Field-level validation and immutability
- Efficient database indexing and constraints
- Helper properties for resource data access
- Type-safe field definitions with SQLModel
"""

from typing import Optional, ClassVar, Dict, Any
from sqlmodel import Field, Relationship
from sqlalchemy import event, Index
from sqlalchemy.orm import declared_attr
from pydantic import field_validator, ValidationInfo

from .models.database import DatabaseWithTimestampsModel, datetime_with_timezone
from .models.rid import generate_ulid
from .models.patterns import (
    OBJECT_TYPE_API_NAME_PATTERN,
    LINK_TYPE_API_NAME_PATTERN,
    ACTION_TYPE_API_NAME_PATTERN,
    QUERY_TYPE_API_NAME_PATTERN,
    RESERVED_WORDS,
    validate_string
)
from .resource import Resource
from .config import settings
import sqlalchemy.schema
import logging

logger = logging.getLogger(__name__)

# Model for additional resource attributes
class ResourceBaseModel(DatabaseWithTimestampsModel, table=False):
    """
    Abstract base model for additional resource attributes linked to Resource via rid.
    Concrete subclasses should define a relationship to Resource if needed.

    Attributes:
        rid (str): Foreign key referencing Resource.rid (primary key in concrete subclasses).
        status (str): Resource status (e.g., 'DRAFT').
        api_name (str): API name, validated based on resource_type from rid.
        display_name (Optional[str]): Display name, defaults to api_name if not set.

    Class attributes:
        __resource_type__ (str): The resource type to use when creating Resources automatically.
                              Must be overridden in subclasses.
    """

    __resource_type__: ClassVar[str] = ""

    @declared_attr
    def __table_args__(cls) -> tuple:
        """
        Define table arguments including indexes with unique names per model.
        Uses the lowercase table name as a prefix for index names to avoid conflicts.
        """
        table_name = cls.__name__.lower()
        return (
            Index(f"idx_{table_name}_api_name", "api_name"),
            Index(f"idx_{table_name}_status", "status"),
            Index(f"idx_{table_name}_status_api_name", "status", "api_name"),
            sqlalchemy.schema.ForeignKeyConstraint(
                ["rid"], ["resource.rid"],
                name=f"fk_{table_name}_resource_rid"
            ),
        )

    rid: str = Field(primary_key=True, foreign_key="resource.rid", default=None)
    status: str = Field(default="DRAFT", index=True)
    api_name: str = Field(index=True, max_length=255)
    display_name: Optional[str] = Field(default=None, nullable=True, max_length=255)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Register event listeners for all subclasses."""
        super().__init_subclass__(**kwargs)
        event.listen(cls, 'before_insert', cls._create_resource)

    @staticmethod
    def _create_resource(mapper, connection, instance):
        """Create Resource automatically if rid is not provided."""
        if instance.rid is not None:
            return

        service = getattr(instance, '_service', settings.DEFAULT_SERVICE)
        instance_name = getattr(instance, '_instance', settings.DEFAULT_INSTANCE)
        resource_type = instance.__class__.__resource_type__

        if not resource_type:
            raise ValueError(f"__resource_type__ must be set on {instance.__class__.__name__}")

        resource_id = str(generate_ulid())
        rid = f"ri.{service}.{instance_name}.{resource_type}.{resource_id}"

        resource_table = Resource.__table__
        connection.execute(
            resource_table.insert().values(
                id=resource_id,
                rid=rid,
                service=service,
                instance=instance_name,
                resource_type=resource_type,
                created_at=datetime_with_timezone()
            )
        )
        instance.rid = rid

    def get_resource(self, session) -> "Resource":
        """Get the associated Resource instance using session."""
        from sqlmodel import select
        return session.exec(select(Resource).where(Resource.rid == self.rid)).first()

    @property
    def resource_data(self) -> dict:
        """Get a dictionary of resource data from the rid."""
        if not self.rid:
            return {}
        parts = self.rid.split('.')
        if len(parts) >= 5:
            return {
                'service': parts[1],
                'instance': parts[2],
                'resource_type': parts[3],
                'id': parts[4]
            }
        return {}

    @property
    def service(self) -> str:
        return self.resource_data.get('service', '')

    @property
    def instance(self) -> str:
        return self.resource_data.get('instance', '')

    @property
    def resource_type(self) -> str:
        return self.resource_data.get('resource_type', '')

    def to_dict(self, include=None, exclude=None):
        """Serialize the model to a dictionary, including derived properties."""
        data = self.model_dump(include=include, exclude=exclude)
        data.update({
            'service': self.service,
            'instance': self.instance,
            'resource_type': self.resource_type
        })
        return data

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = {"DRAFT", "ACTIVE", "EXPERIMENTAL", "DEPRECATED", "DELETED"}
        if v not in allowed:
            raise ValueError(f"Status '{v}' must be one of {allowed}")
        return v

    @field_validator("api_name")
    @classmethod
    def validate_api_name(cls, v, info: ValidationInfo):
        rid = info.data.get("rid")
        if not rid:
            raise ValueError("rid is required for validation")
        parts = rid.split('.')
        if len(parts) < 4:
            raise ValueError("Invalid rid format")
        resource_type = parts[3]
        patterns = {
            "object-type": OBJECT_TYPE_API_NAME_PATTERN,
            "link-type": LINK_TYPE_API_NAME_PATTERN,
            "action-type": ACTION_TYPE_API_NAME_PATTERN,
            "query-type": QUERY_TYPE_API_NAME_PATTERN,
        }
        pattern = patterns.get(resource_type, ACTION_TYPE_API_NAME_PATTERN)
        return validate_string(v, pattern, RESERVED_WORDS, "api_name")

    @field_validator("display_name", mode="after")
    @classmethod
    def set_display_name_default(cls, v, info: ValidationInfo):
        return v if v is not None else info.data.get("api_name")

# Mixin for the Relationship
class ResourceRelationshipMixin:
    """
    Mixin class to provide the 'resource' relationship to concrete
    subclasses of ResourceBaseModel using SQLModel's Relationship V2.
    """
    @declared_attr
    def resource(cls):
        return Relationship(
            back_populates=None,  # Specify if Resource defines a back reference
            sa_relationship_kwargs={
                "primaryjoin": f"{cls.__name__}.rid == Resource.rid",
                "lazy": "joined",
            }
        )

# Intermediate Base Class
class BaseResourceType(ResourceBaseModel, ResourceRelationshipMixin, table=False):
    """
    Intermediate base class combining ResourceBaseModel and ResourceRelationshipMixin.
    Concrete classes inherit from this. Still abstract (table=False).
    """
    pass