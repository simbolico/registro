"""
Resource-based model system for SQLModel.

This module provides the core resource model system for the Registro library,
enabling automatic Resource creation, validation, and relationship management.

It implements:
1. ResourceBaseModel: Abstract base for resource attributes and behavior
2. ResourceRelationshipMixin: Provides relationship to Resource model
3. ResourceTypeBaseModel: Complete resource functionality for domain models

Key features:
- Automatic Resource creation when instances are added to session
- Field-level validation and immutability
- Efficient database indexing and constraints
- Helper properties for resource data access
- Relationship resolution and validation
- Enhanced model serialization
"""

from typing import Optional, ClassVar, Dict, Any, Type, TypeVar, Set, List, Union
from sqlmodel import Field, Relationship, SQLModel, Session, select
from sqlalchemy import event, Index
from sqlalchemy.orm import declared_attr
from pydantic import field_validator, ValidationInfo

from registro.models.database import TimestampedModel, datetime_with_timezone
from registro.models.rid import generate_ulid
from registro.models.patterns import (
    OBJECT_TYPE_API_NAME_PATTERN,
    LINK_TYPE_API_NAME_PATTERN,
    ACTION_TYPE_API_NAME_PATTERN,
    QUERY_TYPE_API_NAME_PATTERN,
    RESERVED_WORDS,
    validate_string
)
from registro.core.resource import Resource
from registro.config import settings
import sqlalchemy.schema
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='ResourceBaseModel')

class ResourceBaseModel(TimestampedModel, table=False):
    """
    Abstract base model for additional resource attributes linked to Resource via rid.
    
    Concrete subclasses should set __resource_type__ and optionally define a relationship
    to Resource.
    
    Attributes:
        rid (str): Foreign key referencing Resource.rid (primary key in concrete subclasses)
        status (str): Resource status (e.g., 'DRAFT')
        api_name (str): API name, validated based on resource_type from rid
        display_name (Optional[str]): Display name, defaults to api_name if not set
    
    Class attributes:
        __resource_type__ (str): The resource type to use when creating Resource automatically
                              Must be overridden in subclasses
    """
    
    __resource_type__: ClassVar[str] = ""
    __status_values__: ClassVar[Set[str]] = {
        "DRAFT", "ACTIVE", "EXPERIMENTAL", "DEPRECATED", "DELETED"
    }
    
    @declared_attr
    def __table_args__(cls) -> tuple:
        """
        Define table arguments including indexes with unique names per model.
        
        Uses the lowercase table name as a prefix for index names to avoid conflicts.
        
        Returns:
            tuple: SQLAlchemy table arguments
        """
        table_name = cls.__name__.lower()
        return (
            Index(f"idx_{table_name}_api_name", "api_name"),
            Index(f"idx_{table_name}_status", "status"),
            Index(f"idx_{table_name}_status_api_name", "status", "api_name"),
            sqlalchemy.schema.ForeignKeyConstraint(
                ["rid"], ["resource.rid"],
                name=f"fk_{table_name}_resource_rid",
                ondelete="CASCADE"
            ),
        )
    
    rid: str = Field(
        primary_key=True,
        foreign_key="resource.rid",
        default=None
    )
    
    status: str = Field(
        default="DRAFT",
        index=True
    )
    
    api_name: str = Field(
        index=True
    )
    
    display_name: Optional[str] = Field(
        default=None,
        nullable=True
    )
    
    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        Register event listeners for all subclasses.
        
        Ensures that the _create_resource method is called before 
        instances are inserted into the database.
        
        Args:
            **kwargs: Keyword arguments for the subclass
        
        Raises:
            ValueError: If __resource_type__ is not set on the subclass
        """
        super().__init_subclass__(**kwargs)
        
        # Check that __resource_type__ is set
        if cls.__tablename__ is not None and cls.__resource_type__ == "":
            raise ValueError(f"__resource_type__ must be set on {cls.__name__}")
        
        # Register event listeners for database operations
        event.listen(cls, 'before_insert', cls._create_resource)
    
    @staticmethod
    def _create_resource(mapper, connection, instance):
        """
        Create Resource automatically if rid is not provided.
        
        This method is called by SQLAlchemy before an instance is inserted
        into the database. If the instance doesn't have a rid already,
        a new Resource is created and linked to the instance.
        
        Args:
            mapper: SQLAlchemy mapper
            connection: SQLAlchemy connection
            instance: Model instance being inserted
        
        Raises:
            ValueError: If __resource_type__ is not set on the class
        """
        if instance.rid is not None:
            return
        
        # Get service and instance names from instance or settings
        service = getattr(instance, '_service', settings.DEFAULT_SERVICE)
        instance_name = getattr(instance, '_instance', settings.DEFAULT_INSTANCE)
        resource_type = instance.__class__.__resource_type__
        
        if not resource_type:
            raise ValueError(f"__resource_type__ must be set on {instance.__class__.__name__}")
        
        # Generate a new Resource ID
        resource_id = str(generate_ulid())
        rid = f"{settings.RID_PREFIX}.{service}.{instance_name}.{resource_type}.{resource_id}"
        
        # Insert the Resource using the SQLAlchemy table directly
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
        
        # Set the RID on the instance
        instance.rid = rid
    
    def get_resource(self, session: Session) -> Resource:
        """
        Get the associated Resource instance using session.
        
        Args:
            session: SQLAlchemy session
        
        Returns:
            Resource: The associated Resource instance
        """
        return session.exec(select(Resource).where(Resource.rid == self.rid)).first()
    
    @property
    def resource_data(self) -> Dict[str, str]:
        """
        Get a dictionary of resource data from the rid.
        
        Returns:
            Dict[str, str]: Dictionary with resource components
        """
        if not self.rid:
            return {}
        
        parts = self.rid.split('.')
        if len(parts) >= 5:
            return {
                'prefix': parts[0],
                'service': parts[1],
                'instance': parts[2],
                'resource_type': parts[3],
                'id': parts[4]
            }
        return {}
    
    @property
    def service(self) -> str:
        """Get the service component from the RID."""
        return self.resource_data.get('service', '')
    
    @property
    def instance(self) -> str:
        """Get the instance component from the RID."""
        return self.resource_data.get('instance', '')
    
    @property
    def resource_type(self) -> str:
        """Get the resource_type component from the RID."""
        return self.resource_data.get('resource_type', '')
    
    @property
    def resource_id(self) -> str:
        """Get the id component from the RID."""
        return self.resource_data.get('id', '')
    
    def to_dict(self, include=None, exclude=None):
        """
        Serialize the model to a dictionary, including derived properties.
        
        Args:
            include: Fields to include
            exclude: Fields to exclude
        
        Returns:
            Dict: Serialized model data
        """
        data = self.model_dump(include=include, exclude=exclude)
        data.update({
            'service': self.service,
            'instance': self.instance,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id
        })
        return data
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """
        Validate that status is one of the allowed values.
        
        Args:
            v: The status value
        
        Returns:
            str: The validated status
        
        Raises:
            ValueError: If status is not allowed
        """
        allowed = cls.__status_values__
        if v not in allowed:
            raise ValueError(f"Status '{v}' must be one of {allowed}")
        return v
    
    @field_validator("api_name")
    @classmethod
    def validate_api_name(cls, v, info: ValidationInfo):
        """
        Validate api_name based on resource_type from rid.
        
        Different resource types have different naming conventions.
        
        Args:
            v: API name to validate
            info: Validation context
        
        Returns:
            str: Validated API name
        
        Raises:
            ValueError: If validation fails
        """
        rid = info.data.get("rid")
        resource_type = cls.__resource_type__
        
        # If we have a RID, extract the resource type from it
        if rid:
            parts = rid.split('.')
            if len(parts) >= 4:
                resource_type = parts[3]
        
        patterns = {
            "object-type": OBJECT_TYPE_API_NAME_PATTERN,
            "link-type": LINK_TYPE_API_NAME_PATTERN,
            "action-type": ACTION_TYPE_API_NAME_PATTERN,
            "query-type": QUERY_TYPE_API_NAME_PATTERN,
        }
        
        # Get the appropriate pattern or default to ACTION_TYPE_API_NAME_PATTERN
        pattern = patterns.get(resource_type, ACTION_TYPE_API_NAME_PATTERN)
        
        # Validate the API name
        return validate_string(v, pattern, RESERVED_WORDS, "api_name")
    
    @field_validator("display_name", mode="after")
    @classmethod
    def set_display_name_default(cls, v, info: ValidationInfo):
        """
        Set display_name to api_name if not provided.
        
        Args:
            v: The display_name value
            info: Validation context
        
        Returns:
            str: The display_name or api_name
        """
        return v if v is not None else info.data.get("api_name")

class ResourceRelationshipMixin:
    """
    Mixin class to provide the 'resource' relationship to ResourceBaseModel.
    
    Adds a SQLModel Relationship to the Resource model.
    """
    
    @declared_attr
    def resource(cls):
        """
        Define relationship to Resource model.
        
        Returns:
            Relationship: SQLModel relationship to Resource
        """
        return Relationship(
            back_populates=None,
            sa_relationship_kwargs={
                "primaryjoin": f"{cls.__name__}.rid == Resource.rid",
                "lazy": "joined",
            }
        )

class ResourceTypeBaseModel(ResourceBaseModel, ResourceRelationshipMixin, table=False):
    """
    Complete resource-based model combining all functionality.
    
    Concrete classes should inherit from this and set __resource_type__.
    
    Features:
    - Automatic Resource creation
    - Resource metadata access (service, instance, etc.)
    - Relationship helper methods
    - Field validation utilities
    - Enhanced serialization to dict
    
    Example:
        ```python
        class Product(ResourceTypeBaseModel, table=True):
            __resource_type__ = "product"
            
            name: str = Field()
            price: float = Field()
        ```
    """
    __resource_type__ = "resource"
    
    def __init__(self, **data):
        """
        Initialize resource with service and instance information.
        
        Args:
            **data: Resource data including optional service and instance
        """
        # Extract service and instance with defaults from data
        self._service = data.pop("service", None) or settings.DEFAULT_SERVICE
        self._instance = data.pop("instance", None) or settings.DEFAULT_INSTANCE
        super().__init__(**data)
    
    def get_related_resource(self, 
                            model_class: Type["ResourceTypeBaseModel"], 
                            rid: Optional[str] = None, 
                            api_name: Optional[str] = None,
                            session: Session = None) -> Optional["ResourceTypeBaseModel"]:
        """
        Get a related resource by either RID or API name.
        
        Args:
            model_class: The SQLModel class to query
            rid: Optional resource ID to search by
            api_name: Optional API name to search by
            session: SQLModel session for database access
            
        Returns:
            The found resource or None if not found
            
        Raises:
            ValueError: If session is not provided
        """
        if session is None:
            raise ValueError("Session is required to get related resources")
            
        if rid:
            stmt = select(model_class).where(model_class.rid == rid)
            return session.exec(stmt).first()
        elif api_name:
            stmt = select(model_class).where(model_class.api_name == api_name)
            return session.exec(stmt).first()
        return None
    
    def link_resource(self, 
                     session: Session,
                     resource: Optional["ResourceTypeBaseModel"] = None,
                     model_class: Optional[Type["ResourceTypeBaseModel"]] = None,
                     rid_field: Optional[str] = None,
                     api_name_field: Optional[str] = None,
                     rid_value: Optional[str] = None, 
                     api_name_value: Optional[str] = None) -> "ResourceTypeBaseModel":
        """
        Link this resource to another resource based on provided information.
        
        This helper simplifies setting up relationships between resources.
        
        Args:
            session: SQLModel session for database access
            resource: Optional pre-fetched resource to link
            model_class: Resource model class to query if resource not provided
            rid_field: Field name on this resource to store the related resource's RID
            api_name_field: Field name on this resource to store the related resource's API name
            rid_value: RID to search by if resource not provided
            api_name_value: API name to search by if resource not provided
            
        Returns:
            The linked resource
            
        Raises:
            ValueError: If the related resource cannot be found
        """
        # Use provided resource, or find by RID or API name
        linked_resource = resource
        if not linked_resource and model_class and session:
            linked_resource = self.get_related_resource(
                model_class, 
                rid=rid_value, 
                api_name=api_name_value, 
                session=session
            )
            
        if not linked_resource:
            raise ValueError(f"Could not find related resource of type {model_class.__name__}")
            
        # Set relationship fields if provided
        if rid_field and hasattr(self, rid_field):
            setattr(self, rid_field, linked_resource.rid)
            
        if api_name_field and hasattr(self, api_name_field):
            setattr(self, api_name_field, linked_resource.api_name)
            
        return linked_resource
    
    def to_dict(self, include_relationships: bool = False, exclude: Optional[Union[Set[str], Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Convert resource to a dictionary representation.
        
        Args:
            include_relationships: Whether to include relationship data
            exclude: Fields to exclude from serialization
            
        Returns:
            Dictionary representation of the resource
        """
        # Set up exclude set
        exclude_set = {"resource"}
        if exclude:
            if isinstance(exclude, set):
                exclude_set.update(exclude)
            elif isinstance(exclude, dict):
                for key, value in exclude.items():
                    if value:
                        exclude_set.add(key)
        
        # Get base fields from model_dump
        data = self.model_dump(exclude=exclude_set)
        
        # Add resource metadata
        data.update({
            "rid": self.rid,
            "service": self.service,
            "instance": self.instance,
            "resource_type": self.resource_type
        })
        
        return data
    
    @classmethod
    def validate_identifier(cls, value: str, field_name: str) -> str:
        """
        Validate that a field contains a valid identifier.
        
        Args:
            value: The string value to validate
            field_name: Name of the field being validated
            
        Returns:
            The validated value
            
        Raises:
            ValueError: If the value is not a valid identifier
        """
        if not value or not value.isidentifier():
            raise ValueError(f"{field_name} must be a valid Python identifier")
        return value
        
    @classmethod
    def validate_related_field_match(cls, 
                                    resource: "ResourceTypeBaseModel", 
                                    field_name: str, 
                                    expected_value: Any) -> "ResourceTypeBaseModel":
        """
        Validate that a field in a related resource matches the expected value.
        
        Args:
            resource: The related resource to validate
            field_name: Name of the field to check
            expected_value: Expected value of the field
            
        Returns:
            The validated resource
            
        Raises:
            ValueError: If the field value doesn't match the expected value
        """
        if resource is None:
            return None
            
        actual_value = getattr(resource, field_name, None)
        if actual_value != expected_value:
            raise ValueError(
                f"Related resource {resource.__class__.__name__} has {field_name}='{actual_value}' "
                f"but expected '{expected_value}'"
            )
        return resource

# Types for type hints
ResourceModelType = TypeVar('ResourceModelType', bound=ResourceTypeBaseModel) 