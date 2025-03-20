from typing import Optional, List, Any, ForwardRef
from sqlmodel import Field, Relationship
from pydantic import field_validator, model_validator, ValidationInfo, ConfigDict
from sqlalchemy import String, event, insert
from sqlalchemy.orm import mapped_column, object_session, declared_attr
from ontologia.registry.models.database import DatabaseWithTimestampsModel, datetime_with_timezone
from ontologia.registry.models.rid import RID, ServiceStr, InstanceStr, TypeStr, generate_ulid
from ontologia.registry.models.patterns import (
    OBJECT_TYPE_API_NAME_PATTERN, LINK_TYPE_API_NAME_PATTERN,
    ACTION_TYPE_API_NAME_PATTERN, QUERY_TYPE_API_NAME_PATTERN,
    RESERVED_WORDS, validate_string
)
import ulid
import sqlalchemy.schema
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Base Resource model with core identifying fields
class Resource(DatabaseWithTimestampsModel, table=True):
    """
    Base model for resources with a ULID id and a constructed rid.

    Attributes:
        id (str): Auto-generated monotonic ULID identifier (primary key, inherited, immutable).
        rid (str): Constructed resource identifier (e.g., 'service.instance.type.id', unique, immutable).
        service (ServiceStr): Service or domain (e.g., 'ontology', immutable).
        instance (InstanceStr): Instance or environment (e.g., 'main', immutable).
        resource_type (TypeStr): Type of resource (e.g., 'object-type', immutable).
        created_at, updated_at, archived_at, deleted_at, expired_at: Inherited timestamps.

    Uniqueness Guarantees:
        - Monotonic ULID generation prevents collisions even in concurrent scenarios
        - Composite indexes and unique constraints at the database level
        - Multi-component RID structure reduces collision probability
    """
    # Removed immutability enforcement
    # model_config = ConfigDict(frozen=True)  # Enforce immutability

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Override __setattr__ to enforce field-level immutability on critical fields.

        Critical fields (rid, service, instance, resource_type) cannot be modified after
        initialization. Other fields remain mutable.

        Args:
            name (str): Name of the attribute to set
            value (Any): Value to set

        Raises:
            AttributeError: If attempting to modify an immutable field after initialization
        """
        immutable_fields = {"rid", "service", "instance", "resource_type"}
        if name in immutable_fields and hasattr(self, name):
            raise AttributeError(
                f"Cannot modify immutable field '{name}'. Critical fields (rid, service, "
                "instance, resource_type) are immutable after initialization."
            )
        super().__setattr__(name, value)

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
        default_factory=lambda: str(ulid.new()),  # Use direct ULID generation
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
        description="Constructed resource identifier (e.g., 'service.instance.type.id'), immutable once set"
    )
    service: ServiceStr = Field(
        index=True,
        description="Service or domain identifier (e.g., 'ontology'), immutable once set"
    )
    instance: InstanceStr = Field(
        index=True,
        description="Instance or environment identifier (e.g., 'main'), immutable once set"
    )
    resource_type: TypeStr = Field(
        index=True,
        description="Type of resource (e.g., 'object-type'), immutable once set"
    )

    # We'll define relationships in specific models, not here
    # to avoid circular dependencies

    def __init__(self, **data):
        # Generate ID first if not provided
        if "id" not in data or data["id"] is None:
            data["id"] = str(ulid.new())

        # Get the required components with fallbacks
        service = data.get("service", "default-service")
        instance = data.get("instance", "main")
        resource_type = data.get("resource_type", "resource")
        locator = data["id"]

        # Generate the RID if not provided
        if "rid" not in data or data["rid"] is None:
            data["rid"] = f"ri.{service}.{instance}.{resource_type}.{locator}"
            logger.debug(f"RID generated in __init__: {data['rid']}")

        super().__init__(**data)

    @model_validator(mode="before")
    @classmethod
    def generate_rid(cls, values):
        """
        Generate the rid using service, instance, resource_type, and an auto-generated ULID id.

        This is a backup validator to ensure RID is set if not generated in __init__.
        """
        # Skip if rid is already set
        if values.get("rid"):
            return values

        # Generate ID first if not provided
        if "id" not in values or values["id"] is None:
            values["id"] = str(ulid.new())

        # Get the required components with fallbacks
        service = values.get("service", "default-service")
        instance = values.get("instance", "main")
        resource_type = values.get("resource_type", "resource")
        locator = values["id"]

        # Now generate the RID
        values["rid"] = f"ri.{service}.{instance}.{resource_type}.{locator}"
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
            model.rid = f"ri.{model.service}.{model.instance}.{model.resource_type}.{model.id}"
            logger.debug(f"RID generated in consistency check: {model.rid}")

        # Split RID into components
        rid_parts = model.rid.split('.')

        # Validate RID format
        if len(rid_parts) != 5:
            raise ValueError(f"Invalid RID format: '{model.rid}' must have 5 components")

        # Validate RID prefix
        if rid_parts[0] != "ri":
            raise ValueError(f"Invalid RID prefix: '{rid_parts[0]}' must be 'ri'")

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