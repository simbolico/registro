"""
Validation patterns for resource identifiers and field validation.

This module provides regex patterns and validation functions for:
- Resource identifier components (service, instance, type, locator)
- API names for different resource types
- String validation with regex and reserved word checking

The patterns enforce consistent naming conventions and prevent reserved words
from being used in inappropriate contexts.
"""

import re
from typing import Optional, Pattern, Set
from registro.config import settings

# Reserved words that should not be used for certain identifiers
RESERVED_WORDS: Set[str] = {
    "registro", "resource", "property", "link", "relation",
    "rid", "primaryKey", "typeId", "resourceObject",
    "create", "read", "update", "delete", "list", "all",
    "null", "true", "false", "none", "id",
}

# Regex timeout in seconds (0.1s = 100ms, sufficient for most patterns)
REGEX_TIMEOUT = 0.1

# Pre-compiled regex patterns for API names
OBJECT_TYPE_API_NAME_PATTERN = re.compile(r"^(?=.{1,100}$)[A-Z][A-Za-z0-9]*$")
"""Regex for Object Type API names (PascalCase).
   - Must start with an uppercase letter, followed by alphanumeric characters.
   - Total length: 1 to 100 characters.
   - Example: 'Person' (valid); 'person' (invalid)."""

LINK_TYPE_API_NAME_PATTERN = re.compile(r"^(?=.{1,100}$)[a-z][A-Za-z0-9]*$")
"""Regex for Link Type API names (lowerCamelCase).
   - Must start with a lowercase letter, followed by alphanumeric characters.
   - Total length: 1 to 100 characters.
   - Example: 'owns' (valid); 'Owns' (invalid)."""

ACTION_TYPE_API_NAME_PATTERN = re.compile(r"^(?=.{1,100}$)[A-Za-z][A-Za-z0-9_-]*$")
"""Regex for Action Type API names (flexible naming).
   - Must start with a letter, followed by letters, digits, underscores, or hyphens.
   - Total length: 1 to 100 characters.
   - Example: 'create-user' (valid); 'create$user' (invalid)."""

QUERY_TYPE_API_NAME_PATTERN = re.compile(r"^(?=.{1,100}$)[a-z][A-Za-z0-9]*$")
"""Regex for Query Type API names (lowerCamelCase).
   - Must start with a lowercase letter, followed by alphanumeric characters.
   - Total length: 1 to 100 characters.
   - Example: 'getUsers' (valid); 'GetUsers' (invalid)."""

# Pre-compiled regex patterns for RID components
SERVICE_PATTERN = re.compile(r"^[a-z][a-z-]{0,49}$")
"""Regex for the 'service' component in RIDs.
   - Must start with a lowercase letter, followed by lowercase letters or hyphens.
   - Total length: 1 to 50 characters.
   - Example: 'compute' (valid); 'Compute' (invalid)."""

INSTANCE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,49}$")
"""Regex for the 'instance' component in RIDs.
   - Must start with an alphanumeric character, followed by lowercase letters, digits, or hyphens.
   - Total length: 1 to 50 characters.
   - Example: 'main' (valid); 'Main' (invalid)."""

# TYPE_PATTERN = re.compile(r"^[a-z][a-z-]{1,49}$")
TYPE_PATTERN = re.compile(r"^[a-z][a-z-]{1,49}$")
"""Regex for the 'type' component in RIDs.
   - Must start with a lowercase letter, followed by lowercase letters or hyphens.
   - Total length: 2 to 50 characters.
   - Example: 'resource' (valid); 'Resource' (invalid)."""

LOCATOR_PATTERN = re.compile(r"^[0-9A-HJ-KM-NPQRSTVWXYZ]{26}$")
"""Regex for the 'locator' component in RIDs (ULID).
   - 26 characters using Crockford's base32 (uppercase letters and digits, excluding I, L, O, U).
   - Example: '01J8X9K7M2P3Q5R7T9V1W3Y5Z' (valid); '01J8X9K7M2P3Q5R7T9V1W3YZ' (invalid)."""

def get_rid_pattern() -> Pattern[str]:
    """
    Generate a regex pattern for complete Resource Identifiers (RIDs).
    
    Uses the current RID_PREFIX from settings to create a pattern that matches:
    <prefix>.<service>.<instance>.<type>.<locator>
    
    Returns:
        Pattern[str]: Compiled regex pattern for RIDs
    """
    prefix = re.escape(settings.RID_PREFIX)
    return re.compile(
        rf"^{prefix}\.{SERVICE_PATTERN.pattern[1:-1]}\.{INSTANCE_PATTERN.pattern[1:-1]}\.{TYPE_PATTERN.pattern[1:-1]}\.{LOCATOR_PATTERN.pattern[1:-1]}$"
    )

def validate_string(
    value: str,
    pattern: Pattern[str],
    reserved_words: Optional[Set[str]] = RESERVED_WORDS,
    field_name: str = "value"
) -> str:
    """
    Validate a string against a regex pattern and optional reserved words.
    
    Args:
        value (str): The string to validate
        pattern (Pattern[str]): Pre-compiled regex pattern to match against
        reserved_words (Optional[Set[str]]): Set of reserved words to check against
        field_name (str): Name of the field for error messaging
    
    Returns:
        str: The validated string
    
    Raises:
        TypeError: If `value` is not a string
        ValueError: If validation fails (pattern mismatch or reserved word)
    """
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string, got {type(value).__name__}")

    if not pattern.match(value):
        raise ValueError(f"{field_name} '{value}' does not match pattern {pattern.pattern}")

    if reserved_words and value.lower() in reserved_words:
        raise ValueError(f"{field_name} '{value}' is a reserved word and cannot be used")

    return value 