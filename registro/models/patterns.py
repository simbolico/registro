"""
Validation patterns for resource identifiers and field validation.

This module provides validation functions for:
- Resource identifier components (service, instance, type, locator)
- API names for different resource types
- String validation with regex and reserved word checking

Pattern Documentation:

SERVICE_PATTERN
- Must start with a lowercase letter, followed by lowercase letters or hyphens
- Total length: 1 to 50 characters
- Example: 'compute' (valid); 'Compute' (invalid)

INSTANCE_PATTERN
- Must start with an alphanumeric character, followed by lowercase letters, digits, or hyphens
- Total length: 1 to 50 characters
- Example: 'main' (valid); 'Main' (invalid)

TYPE_PATTERN
- Must start with a lowercase letter, followed by lowercase letters or hyphens
- Total length: 2 to 50 characters
- Example: 'resource' (valid); 'Resource' (invalid)

LOCATOR_PATTERN
- 26 characters using Crockford's base32 (uppercase letters and digits, excluding I, L, O, U)
- Example: '01J8X9K7M2P3Q5R7T9V1W3Y5Z' (valid)

API Name Patterns:
- Object Type: PascalCase, 1-100 chars (e.g., 'Person')
- Link Type: lowerCamelCase, 1-100 chars (e.g., 'owns')
- Action Type: Letters/digits/underscores/hyphens, 1-100 chars (e.g., 'create-user')
- Query Type: lowerCamelCase, 1-100 chars (e.g., 'getUsers')
"""

from typing import Pattern, Set
from registro.config import settings

RESERVED_WORDS: Set[str] = {
    "registro", "resource", "property", "link", "relation",
    "rid", "primaryKey", "typeId", "resourceObject",
    "create", "read", "update", "delete", "list", "all",
    "null", "true", "false", "none", "id",
}

# API name patterns compiled from settings
OBJECT_TYPE_API_NAME_PATTERN = settings.get_compiled_pattern("API_NAME_OBJECT_TYPE")
LINK_TYPE_API_NAME_PATTERN = settings.get_compiled_pattern("API_NAME_LINK_TYPE")
ACTION_TYPE_API_NAME_PATTERN = settings.get_compiled_pattern("API_NAME_ACTION_TYPE")
QUERY_TYPE_API_NAME_PATTERN = settings.get_compiled_pattern("API_NAME_QUERY_TYPE")

def validate_string(
    value: str,
    pattern: Pattern[str],
    reserved_words: Set[str],
    field_name: str = "value"
) -> str:
    """
    Validate a string against a regex pattern and reserved words.

    Args:
        value (str): The string to validate
        pattern (Pattern[str]): Pre-compiled regex pattern to match against
        reserved_words (Set[str]): Set of reserved words to check against
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

    if value.lower() in reserved_words:
        raise ValueError(f"{field_name} '{value}' is a reserved word and cannot be used")

    return value