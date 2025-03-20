"""
Base database models for the Registro library.

This module provides abstract base models for database entities with SQLModel and Pydantic v2
integration. These models include:

1. DatabaseModel: Basic model with ID and timestamp tracking
2. TimestampedModel: Adds lifecycle timestamps (archived, deleted, expired)
3. NamedModel: Adds name and description fields

These models can be used as building blocks for your domain models, providing
consistent identification and lifecycle tracking.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any, TypeVar, ClassVar, Type, cast
from zoneinfo import ZoneInfo
import os
import ulid

from pydantic import field_validator, ValidationInfo, ConfigDict
from sqlmodel import SQLModel, Field
from sqlalchemy import String
from sqlalchemy.orm import mapped_column

from registro.config import settings

# Type variables for generic type hints
T = TypeVar('T', bound='DatabaseModel')

def datetime_with_timezone(tz: Optional[ZoneInfo] = None) -> datetime:
    """
    Get the current time with timezone information.
    
    Args:
        tz: Timezone to use (defaults to settings.TIMEZONE)
    
    Returns:
        datetime: Current time with timezone
    
    Raises:
        TypeError: If tz is provided but not a ZoneInfo instance
    """
    if tz is None:
        tz = settings.TIMEZONE
    elif not isinstance(tz, ZoneInfo):
        raise TypeError(f"Expected ZoneInfo, got {type(tz).__name__}")
    
    return datetime.now(tz)

class DatabaseModel(SQLModel, table=False):
    """
    Base model for database entities with a ULID identifier and timestamps.
    
    Abstract class providing a foundation for all database models with automatic ID and
    creation timestamp generation.
    
    Attributes:
        id (str): ULID-based primary key
        created_at (datetime): Timestamp when the entity was created
        updated_at (Optional[datetime]): Timestamp when the entity was last updated
    """
    
    id: str = Field(
        default_factory=lambda: str(ulid.new()),
        sa_column=mapped_column(String, primary_key=True, index=True, unique=True, nullable=False),
        description="Unique identifier (ULID)"
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime_with_timezone(),
        sa_column=mapped_column(nullable=False),
        description="Timestamp when the entity was created"
    )
    
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=mapped_column(onupdate=datetime_with_timezone, nullable=True),
        description="Timestamp when the entity was last updated"
    )
    
    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ensure_timezone(cls: Type[T], v: Optional[datetime]) -> Optional[datetime]:
        """
        Ensure timestamps have timezone information.
        
        Args:
            v: Datetime value to validate
        
        Returns:
            Optional[datetime]: Timezone-aware datetime or None
        """
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=settings.TIMEZONE)
        return v

class TimestampedModel(DatabaseModel, table=False):
    """
    Model with additional lifecycle timestamps.
    
    Extends DatabaseModel with fields to track archiving, deletion, and expiration.
    
    Attributes:
        archived_at (Optional[datetime]): When the entity was archived
        deleted_at (Optional[datetime]): When the entity was deleted
        expired_at (Optional[datetime]): When the entity expired
    """
    
    archived_at: Optional[datetime] = Field(
        default=None,
        sa_column=mapped_column(nullable=True),
        description="When the entity was archived"
    )
    
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=mapped_column(nullable=True),
        description="When the entity was deleted"
    )
    
    expired_at: Optional[datetime] = Field(
        default=None,
        sa_column=mapped_column(nullable=True),
        description="When the entity expired"
    )
    
    @field_validator("archived_at", "deleted_at", "expired_at", mode="before")
    @classmethod
    def ensure_lifecycle_timezone(cls: Type[T], v: Optional[datetime]) -> Optional[datetime]:
        """
        Ensure lifecycle timestamps have timezone information.
        
        Args:
            v: Datetime value to validate
        
        Returns:
            Optional[datetime]: Timezone-aware datetime or None
        """
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=settings.TIMEZONE)
        return v
    
    @property
    def is_active(self) -> bool:
        """Check if the entity is currently active (not archived, deleted, or expired)."""
        return (
            self.archived_at is None and
            self.deleted_at is None and
            (self.expired_at is None or self.expired_at > datetime_with_timezone())
        )

class NamedModel(TimestampedModel, table=False):
    """
    Model with name and description fields.
    
    Extends TimestampedModel with human-readable metadata fields.
    
    Attributes:
        name (Optional[str]): Human-readable name
        description (Optional[str]): Detailed description
    """
    
    name: Optional[str] = Field(
        default=None,
        sa_column=mapped_column(String, index=True, nullable=True),
        description="Human-readable name"
    )
    
    description: Optional[str] = Field(
        default=None,
        sa_column=mapped_column(String, nullable=True),
        description="Detailed description"
    ) 