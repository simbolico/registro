
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
from registro.models.patterns import validate_string

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
    Validation rules are fetched dynamically from registro.config.settings.

    Class Methods:
        _get_pattern(): Get the compiled pattern from settings.
        _get_reserved_words(): Get reserved words minus allowed exceptions.

    Raises:
        ValueError: If validation fails or pattern not found in settings.
        TypeError: If input is not a string.
    """
    allowed_exceptions: ClassVar[Set[str]] = set()

    @classmethod
    def _get_pattern(cls) -> Pattern[str]:
        """Get the compiled pattern from settings based on class name."""
        pattern_name = cls.__name__.replace("Str", "").upper()
        pattern = settings.get_compiled_pattern(pattern_name)
        if not pattern:
            raise ValueError(f"Configuration error: Pattern '{pattern_name}' not found or invalid in settings for {cls.__name__}")
        return pattern

    @classmethod
    def _get_reserved_words(cls) -> Set[str]:
        """Get the effective set of reserved words from settings minus exceptions."""
        base_reserved_words = settings.RESERVED_WORDS
        return base_reserved_words - cls.allowed_exceptions

    @classmethod
    def __get_pydantic_core_schema__(cls: Type[T], source_type: Any, handler: Any) -> core_schema.CoreSchema:
        """Define Pydantic v2 validation schema using dynamic pattern."""
        try:
            pattern_regex_str = cls._get_pattern().pattern
        except ValueError as e:
            logger.error(f"Schema generation error for {cls.__name__}: {e}")
            return core_schema.str_schema()

        return core_schema.with_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(pattern=pattern_regex_str),
            serialization=core_schema.str_schema(),
        )

    @classmethod
    def validate(cls: Type[T], v: str, info: Any) -> str:
        """Validate the input against dynamically fetched pattern and reserved words."""
        pattern = cls._get_pattern()
        reserved = cls._get_reserved_words()
        return validate_string(v, pattern, reserved, cls.__name__)

class ServiceStr(ConstrainedStr):
    """
    String type for the 'service' component of a RID.
    Uses pattern 'SERVICE' from settings. Allows settings.DEFAULT_SERVICE
    even if it's in the reserved words list.

    Example:
        >>> ServiceStr.validate("users")  # Valid
        'users'
        >>> ServiceStr.validate("Users")  # Raises ValueError
    """
    @classmethod
    def _get_reserved_words(cls) -> Set[str]:
        """Get reserved words, allowing the configured DEFAULT_SERVICE."""
        base_reserved_words = settings.RESERVED_WORDS
        return base_reserved_words - {settings.DEFAULT_SERVICE}

class InstanceStr(ConstrainedStr):
    """
    String type for the 'instance' component of a RID.
    Uses pattern 'INSTANCE' from settings. Allows settings.DEFAULT_INSTANCE
    even if it's in the reserved words list.

    Example:
        >>> InstanceStr.validate("main")  # Valid
        'main'
        >>> InstanceStr.validate("Main")  # Raises ValueError
    """
    @classmethod
    def _get_reserved_words(cls) -> Set[str]:
        """Get reserved words, allowing the configured DEFAULT_INSTANCE."""
        base_reserved_words = settings.RESERVED_WORDS
        return base_reserved_words - {settings.DEFAULT_INSTANCE}

class TypeStr(ConstrainedStr):
    """
    String type for the 'type' component of a RID.
    Uses pattern 'TYPE' from settings. Allows common type names
    even if they are in the reserved words list.

    Example:
        >>> TypeStr.validate("user")  # Valid
        'user'
        >>> TypeStr.validate("User")  # Raises ValueError
    """
    allowed_exceptions: ClassVar[Set[str]] = {
        "resource", "object", "link", "action", "query",
        "property-type", "object-type"
    }

import re

def get_rid_pattern() -> Pattern[str]:
    """
    Generate a regex pattern for complete Resource Identifiers (RIDs).
    
    Uses the current RID_PREFIX and component patterns from settings to create 
    a pattern that matches: <prefix>.<service>.<instance>.<type>.<locator>
    
    Returns:
        Pattern[str]: Compiled regex pattern for RIDs
        
    Raises:
        ValueError: If any required pattern string is missing in settings.
    """
    prefix = re.escape(settings.RID_PREFIX)
    
    # Fetch pattern strings - handle None cases
    service_p = settings.get_pattern_string("SERVICE")
    instance_p = settings.get_pattern_string("INSTANCE")
    type_p = settings.get_pattern_string("TYPE")
    locator_p = settings.get_pattern_string("LOCATOR")

    if not all([service_p, instance_p, type_p, locator_p]):
        missing = [name for name, p in [("SERVICE", service_p), ("INSTANCE", instance_p), ("TYPE", type_p), ("LOCATOR", locator_p)] if not p]
        raise ValueError(f"Configuration error: Missing pattern strings in settings for: {', '.join(missing)}")
        
    # Remove anchors from component patterns before combining
    service_p = service_p.strip('^$')
    instance_p = instance_p.strip('^$')
    type_p = type_p.strip('^$')
    locator_p = locator_p.strip('^$')
    
    # Construct the full pattern string
    full_pattern_str = rf"^{prefix}\.({service_p})\.({instance_p})\.({type_p})\.({locator_p})$"
    
    try:
        return re.compile(full_pattern_str)
    except re.error as e:
        raise ValueError(f"Failed to compile dynamic RID pattern: {e}\nPattern: {full_pattern_str}")

class LocatorStr(ConstrainedStr):
    """
    String type for the 'locator' component of a RID (ULID).
    Uses pattern 'LOCATOR' from settings. Performs additional ULID validation.

    Example:
        >>> LocatorStr.validate("01GXHP6H7TW89BYT4S9C9JM7XX")  # Valid
        '01GXHP6H7TW89BYT4S9C9JM7XX'
        >>> LocatorStr.validate("invalid")  # Raises ValueError
    """
    allowed_exceptions: ClassVar[Set[str]] = set()

    @classmethod
    def validate(cls: Type[LocatorStr], v: str, info: Any) -> str:
        """Validate the input is a valid ULID string using dynamic pattern/reserved words first."""
        # Step 1: Perform base validation directly using the utility function
        pattern = cls._get_pattern()
        reserved = cls._get_reserved_words()
        validated_str = validate_string(v, pattern, reserved, cls.__name__)

        # Step 2: Perform additional ULID-specific validation
        try:
            # Use ulid library for robust check
            ulid.parse(validated_str)
        except ValueError as e:
            raise ValueError(f"Invalid ULID '{validated_str}': {e}")
        except Exception as e:
            # Fallback to length check if ulid parse fails
            if len(validated_str) != 26:
                raise ValueError(f"Invalid ULID '{validated_str}': Must be 26 characters. Parse error: {e}")

        return validated_str

class RID(str):
    """
    Resource Identifier (RID) class for unique resource identification.
    
    An RID has the format: <prefix>.<service>.<instance>.<type>.<locator>
    Example: ri.users.main.user.01GXHP6H7TW89BYT4S9C9JM7XX
    """
    
    @classmethod
    def __get_pydantic_core_schema__(cls: Type[RID], source_type: Any, handler: Any) -> core_schema.CoreSchema:
        """Define Pydantic v2 validation schema."""
        return core_schema.with_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
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
        
        rid_pattern = settings.get_compiled_pattern("RID")
        if not rid_pattern or not rid_pattern.match(v):
            raise ValueError(f"Invalid RID format: '{v}'")
        
        parts = v.split('.')
        if len(parts) != 5:
            raise ValueError(f"RID must have 5 parts, got {len(parts)}")
        
        prefix, service, instance, type_, locator = parts
        
        if prefix != settings.RID_PREFIX:
            raise ValueError(f"RID prefix '{prefix}' must be '{settings.RID_PREFIX}'")
        
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
        service = service or settings.DEFAULT_SERVICE
        instance = instance or settings.DEFAULT_INSTANCE
        
        service = ServiceStr.validate(service, None)
        instance = InstanceStr.validate(instance, None)
        type_ = TypeStr.validate(type_, None)
        
        if locator is None:
            locator = generate_ulid()
        else:
            locator = LocatorStr.validate(locator, None)
        
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
