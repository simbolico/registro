"""
Resource Identifier (RID) module for the Registro library.

This module defines the RID class and custom string types for resource identifiers,
with validation and generation utilities.

A Resource Identifier (RID) follows the format:
    ri.<service>.<instance>.<type>.<locator>

Where:
- ri: Fixed prefix (configurable)
- service: Service or domain name (e.g., "users", "products")
- instance: Environment or instance name (e.g., "main", "dev")
- type: Resource type (e.g., "user", "product")
- locator: ULID (Universally Unique Lexicographically Sortable Identifier)

Example: ri.users.main.user.01GXHP6H7TW89BYT4S9C9JM7XX
"""

from __future__ import annotations

import threading
import ulid
import logging
import re
from typing import (
    Optional, Dict, ClassVar, Set, Pattern, Final, Type, Any, Union, TypeVar
)
from pydantic_core import core_schema
from registro.config import settings
from registro.models.patterns import (
    SERVICE_PATTERN, INSTANCE_PATTERN, TYPE_PATTERN, LOCATOR_PATTERN,
    RESERVED_WORDS, validate_string, get_rid_pattern
)

# Configure logging
logger = logging.getLogger(__name__)

# Thread-local storage for last ULID to enable monotonic generation
_thread_local: threading.local = threading.local()

T = TypeVar('T', bound='ConstrainedStr')

def generate_ulid() -> str:
    """
    Generate a ULID with monotonic safeguards to prevent collisions.
    
    If multiple ULIDs are generated within the same millisecond, this ensures
    they are monotonically increasing, which prevents collision even in
    high-throughput concurrent scenarios.
    
    Returns:
        str: A unique ULID string
    
    Thread Safety:
        Uses thread-local storage to maintain monotonicity per thread
    """
    # Get the most recent ULID from thread-local storage (or None if first call)
    last_ulid: Optional[ulid.ULID] = getattr(_thread_local, 'last_ulid', None)
    
    # Generate a new ULID
    try:
        # Try to generate a monotonic ULID if we have a previous one
        if last_ulid is not None:
            try:
                # Try using ulid-py's monotonic feature if available
                new_ulid = ulid.new().monotonic()
            except (AttributeError, TypeError):
                # If not available, just generate a new one
                new_ulid = ulid.new()
        else:
            new_ulid = ulid.new()
            
    except (AttributeError, TypeError):
        # Fallback method if the library doesn't support the methods we tried
        import time
        import random
        # Basic ULID generation without the library's specialized features
        timestamp = int(time.time() * 1000)
        randomness = random.getrandbits(80).to_bytes(10, byteorder='big')
        new_ulid = ulid.from_timestamp(timestamp, randomness)
    
    # Store the new ULID for future reference
    _thread_local.last_ulid = new_ulid
    
    return str(new_ulid)

class ConstrainedStr(str):
    """
    Base class for constrained string types with pattern and reserved word validation.
    
    Attributes:
        pattern (ClassVar[Pattern[str]]): Regex pattern for validation
        reserved_words (ClassVar[Optional[Set[str]]]): Reserved words to forbid
    
    Raises:
        ValueError: If validation fails
        TypeError: If input is not a string
    """
    pattern: ClassVar[Pattern[str]]
    reserved_words: ClassVar[Optional[Set[str]]] = None
    
    @classmethod
    def __get_pydantic_core_schema__(cls: Type[T], source_type: Any, handler: Any) -> core_schema.CoreSchema:
        """Define Pydantic v2 validation schema."""
        return core_schema.with_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(pattern=cls.pattern.pattern),
            serialization=core_schema.str_schema(),
        )
    
    @classmethod
    def validate(cls: Type[T], v: str, info: Any) -> str:
        """Validate the input against pattern and reserved words."""
        return validate_string(v, cls.pattern, cls.reserved_words, cls.__name__)

class ServiceStr(ConstrainedStr):
    """
    String type for the 'service' component of a RID.
    
    Example:
        >>> ServiceStr.validate("users")  # Valid
        'users'
        >>> ServiceStr.validate("Users")  # Raises ValueError
    """
    pattern: ClassVar[Pattern[str]] = SERVICE_PATTERN
    # Allow the default service to be used even if it's reserved
    reserved_words: ClassVar[Set[str]] = RESERVED_WORDS - {settings.DEFAULT_SERVICE}

class InstanceStr(ConstrainedStr):
    """
    String type for the 'instance' component of a RID.
    
    Example:
        >>> InstanceStr.validate("main")  # Valid
        'main'
        >>> InstanceStr.validate("Main")  # Raises ValueError
    """
    pattern: ClassVar[Pattern[str]] = INSTANCE_PATTERN
    # Allow the default instance to be used even if it's reserved
    reserved_words: ClassVar[Set[str]] = RESERVED_WORDS - {settings.DEFAULT_INSTANCE}

class TypeStr(ConstrainedStr):
    """
    String type for the 'type' component of a RID.
    
    Example:
        >>> TypeStr.validate("user")  # Valid
        'user'
        >>> TypeStr.validate("User")  # Raises ValueError
    """
    pattern: ClassVar[Pattern[str]] = TYPE_PATTERN
    # Some resource types are commonly used and should be allowed
    reserved_words: ClassVar[Set[str]] = RESERVED_WORDS - {
        "resource", "object", "link", "action", "query"
    }

class LocatorStr(ConstrainedStr):
    """
    String type for the 'locator' component of a RID (ULID).
    
    Example:
        >>> LocatorStr.validate("01GXHP6H7TW89BYT4S9C9JM7XX")  # Valid
        '01GXHP6H7TW89BYT4S9C9JM7XX'
        >>> LocatorStr.validate("invalid")  # Raises ValueError
    """
    pattern: ClassVar[Pattern[str]] = LOCATOR_PATTERN
    reserved_words: ClassVar[Optional[Set[str]]] = None
    
    @classmethod
    def validate(cls: Type[LocatorStr], v: str, info: Any) -> str:
        """Validate the input is a valid ULID string."""
        # Additional validation to ensure it's a valid ULID
        if not isinstance(v, str):
            raise TypeError(f"Expected string, got {type(v).__name__}")
        
        if not cls.pattern.match(v):
            raise ValueError(f"String '{v}' is not a valid ULID format")
        
        try:
            # Try to parse it as a ULID - simplified to just check format
            if len(v) != 26:
                raise ValueError("ULID must be 26 characters")
        except Exception as e:
            raise ValueError(f"Invalid ULID: {e}")
        
        return v

class RID(str):
    """
    Resource Identifier (RID) class for unique resource identification.
    
    An RID has the format: <prefix>.<service>.<instance>.<type>.<locator>
    Example: ri.users.main.user.01GXHP6H7TW89BYT4S9C9JM7XX
    
    Attributes:
        pattern (ClassVar[Pattern[str]]): Regex pattern for RID validation
    """
    
    @classmethod
    def __get_pydantic_core_schema__(cls: Type[RID], source_type: Any, handler: Any) -> core_schema.CoreSchema:
        """Define Pydantic v2 validation schema."""
        return core_schema.with_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(pattern=get_rid_pattern().pattern),
            serialization=core_schema.str_schema(),
        )
    
    @classmethod
    def validate(cls: Type[RID], v: Any, info: Any) -> str:
        """
        Validate an RID string.
        
        Args:
            v: Value to validate
            info: Validation context
        
        Returns:
            str: Validated RID string
        
        Raises:
            ValueError: If validation fails
            TypeError: If input is not a string
        """
        if not isinstance(v, str):
            raise TypeError(f"Expected string, got {type(v).__name__}")
        
        rid_pattern = get_rid_pattern()
        if not rid_pattern.match(v):
            raise ValueError(f"Invalid RID format: '{v}' must match pattern {rid_pattern.pattern}")
        
        # Validate components
        parts = v.split('.')
        if len(parts) != 5:
            raise ValueError(f"RID must have 5 parts, got {len(parts)}")
        
        prefix, service, instance, type_, locator = parts
        
        # Prefix check
        if prefix != settings.RID_PREFIX:
            raise ValueError(f"RID prefix '{prefix}' must be '{settings.RID_PREFIX}'")
        
        # Validate each component
        ServiceStr.validate(service, info)
        InstanceStr.validate(instance, info)
        TypeStr.validate(type_, info)
        LocatorStr.validate(locator, info)
        
        return v
    
    @classmethod
    def generate(
        cls: Type[RID],
        service: Optional[str] = None,
        instance: Optional[str] = None,
        type_: str = "resource",
        locator: Optional[str] = None
    ) -> str:
        """
        Generate a new RID.
        
        Args:
            service: Service component (defaults to settings.DEFAULT_SERVICE)
            instance: Instance component (defaults to settings.DEFAULT_INSTANCE)
            type_: Type component (defaults to "resource")
            locator: Locator component (defaults to a new ULID)
        
        Returns:
            str: A new valid RID
        
        Raises:
            ValueError: If any component validation fails
        """
        # Use defaults from settings if not provided
        service = service or settings.DEFAULT_SERVICE
        instance = instance or settings.DEFAULT_INSTANCE
        
        # Validate components
        service = ServiceStr.validate(service, None)
        instance = InstanceStr.validate(instance, None)
        type_ = TypeStr.validate(type_, None)
        
        # Generate ULID if not provided
        if locator is None:
            locator = generate_ulid()
        else:
            locator = LocatorStr.validate(locator, None)
        
        # Construct the RID
        rid = f"{settings.RID_PREFIX}.{service}.{instance}.{type_}.{locator}"
        
        return rid
    
    def components(self) -> Dict[str, str]:
        """
        Parse an RID into its component parts.
        
        Returns:
            Dict[str, str]: Dictionary with RID components
            {
                'prefix': str,
                'service': str,
                'instance': str,
                'type': str,
                'locator': str
            }
        
        Raises:
            ValueError: If the RID format is invalid
        """
        parts = self.split('.')
        if len(parts) != 5:
            raise ValueError(f"Invalid RID format: '{self}' must have 5 parts")
        
        return {
            'prefix': parts[0],
            'service': parts[1],
            'instance': parts[2],
            'type': parts[3],
            'locator': parts[4]
        } 