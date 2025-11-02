# Registro

[![PyPI version](https://badge.fury.io/py/registro.svg)](https://badge.fury.io/py/registro)
[![Python Versions](https://img.shields.io/pypi/pyversions/registro.svg)](https://pypi.org/project/registro/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Registro is a resource management framework for Python applications that provides structured resource identification, validation, and lifecycle management. Built on SQLModel, it offers a consistent approach to defining, creating, and interacting with resources across applications and services.

## Key Features

- **Resource Identifiers (RIDs)**: Globally unique, structured identifiers (`{prefix}.{service}.{instance}.{resource_type}.{id}`) for all resources.
- **Configurable Validation:** Customize regex patterns and reserved words for RIDs and API names via settings or environment variables.
- **Dual Implementation Approaches**: Support for both decorator-based (`@resource`) and inheritance-based (`ResourceTypeBaseModel`) implementation.
- **SQLModel Integration**: Seamless integration with SQLModel and SQLAlchemy for database operations.
- **Validation**: Field and pattern validation through Pydantic using the configured rules.
- **Type Safety**: Comprehensive type hints for improved IDE support and runtime type checking.
- **Status Management**: Built-in resource status tracking with customizable status values.
- **Relationship Handling**: Tools for defining and navigating resource relationships.
- **Metadata Management**: Automatic tracking of creation, update, and lifecycle events.
- **Relationship Helpers**: Simplified resource linking and relationship management.
- **Enhanced Serialization**: Comprehensive `to_dict()` method with relationship support.

## Installation

### Standard Installation

```bash
pip install registro
```

### With UV (Recommended)

```bash
uv add registro
```

### With Rye

```bash
rye add registro
```

## Configuration

Registro allows customization of default behaviors, validation patterns, and reserved words through the `registro.config.settings` object or environment variables. Configuration should typically be done **before** defining or importing your resource models.

**Precedence:** Environment variables override programmatic settings, which override library defaults.

**Configurable Items:**

1.  **RID Prefix:**
    *   `settings.RID_PREFIX = "myprefix"`
    *   `export REGISTRO_RID_PREFIX="myprefix"` (Default: "ri")
2.  **Default Service & Instance:**
    *   `settings.DEFAULT_SERVICE = "my-service"`
    *   `settings.DEFAULT_INSTANCE = "staging"`
    *   `export REGISTRO_DEFAULT_SERVICE="my-service"`
    *   `export REGISTRO_DEFAULT_INSTANCE="staging"` (Defaults: "default", "prod")
3.  **Reserved Words:**
    *   `settings.RESERVED_WORDS = {"internal", "system", "config"}`
    *   `export REGISTRO_RESERVED_WORDS="internal,system,config"` (See `models/patterns.py` for defaults)
4.  **Validation Patterns:** Define the regex used for validating RID components and API names.
    *   `settings.set_pattern("SERVICE", r"^[a-z]{3,10}$")` # Override service pattern
    *   `settings.set_pattern("API_NAME_OBJECT_TYPE", r"^[A-Z][a-zA-Z]*$")` # Override object type API name pattern
    *   `export REGISTRO_PATTERN_SERVICE="^[a-z]{3,10}$"`
    *   `export REGISTRO_PATTERN_API_NAME_OBJECT_TYPE="^[A-Z][a-zA-Z]*$"`
    *   *Pattern Names (used in `set_pattern` and env vars):* `RID_PREFIX`, `SERVICE`, `INSTANCE`, `TYPE`, `LOCATOR`, `API_NAME_OBJECT_TYPE`, `API_NAME_LINK_TYPE`, `API_NAME_ACTION_TYPE`, `API_NAME_QUERY_TYPE`. (See `config/settings.py` for defaults).
5.  **API Name Pattern Mapping:** Map specific `resource_type` strings to the *name* of the pattern used for their `api_name` validation.
    *   ```python
        settings.API_NAME_PATTERNS_BY_TYPE = {
            "object-type": "API_NAME_OBJECT_TYPE", # Default mapping
            "link-type": "API_NAME_LINK_TYPE",   # Default mapping
            "my-custom-type": "MY_CUSTOM_PATTERN_NAME", # Custom mapping
            "default": "API_NAME_ACTION_TYPE" # Fallback pattern name
        }
        # Ensure "MY_CUSTOM_PATTERN_NAME" is also set via settings.set_pattern()
        settings.set_pattern("MY_CUSTOM_PATTERN_NAME", r"^[a-z_]+$")
        ```
    *   `export REGISTRO_API_NAME_MAPPING='{"my-custom-type": "MY_CUSTOM_PATTERN_NAME"}'` (Overrides are merged with defaults).

## Usage

Registro offers two implementation approaches: inheritance-based and decorator-based.

### Inheritance Approach

Extend `ResourceTypeBaseModel` for explicit control and reliability when running scripts directly:

```python
from registro import ResourceTypeBaseModel
from sqlmodel import Field, Session, SQLModel, create_engine

class Book(ResourceTypeBaseModel, table=True):
    __resource_type__ = "book" # Used in RID generation & API name validation mapping

    # Define fields
    title: str = Field()
    author: str = Field()

    # Optionally specify service and instance in constructor (overrides settings defaults)
    def __init__(self, **data):
        # You can pass service and instance directly to constructor
        super().__init__(**data) # Handles setting _service and _instance
```

### Decorator Approach

Use the `@resource` decorator for a cleaner, more concise syntax:

```python
from registro import resource
from sqlmodel import Field

@resource(
    resource_type="book", # Explicitly set resource type
    service="library",    # Optional: Override settings.DEFAULT_SERVICE
    instance="main"       # Optional: Override settings.DEFAULT_INSTANCE
)
class Book:
    title: str = Field(...)
    author: str = Field(...)
```

## Relationship Management

ResourceTypeBaseModel provides powerful relationship management tools:

```python
from typing import List, Optional
from registro import ResourceTypeBaseModel
from sqlmodel import Field, Relationship, Session

# Define models with relationships
class Author(ResourceTypeBaseModel, table=True):
    __resource_type__ = "author"
    name: str = Field()
    books: List["Book"] = Relationship(back_populates="author")

class Book(ResourceTypeBaseModel, table=True):
    __resource_type__ = "book"
    title: str = Field()
    author_rid: Optional[str] = Field(default=None, foreign_key="author.rid", index=True)
    author_api_name: Optional[str] = Field(default=None, index=True) # Optional, for convenience
    author: Optional[Author] = Relationship(back_populates="books")

    def link_author(self, session: Session, author: Optional[Author] = None,
                   author_rid: Optional[str] = None, author_api_name: Optional[str] = None) -> Author:
        """Link to author using enhanced link_resource helper."""
        # Example: Link by API name
        return self.link_resource(
            session=session,
            resource=author, # Optional: pass fetched resource directly
            model_class=Author,
            rid_field="author_rid", # Field on Book to store Author's RID
            api_name_field="author_api_name", # Field on Book to store Author's API name
            rid_value=author_rid, # Optional: find author by RID
            api_name_value=author_api_name # Optional: find author by API name
        )
```

## Examples

See the `examples/` directory for complete working examples:

- **Basic Usage**: Simple resource creation and querying using both approaches.
- **Custom Resources**: Advanced resource types with relationships, custom base classes, and custom status values.
- **Integration Example**: Demonstrates using Registro with FastAPI.

## Advanced Features

### Resource Relationships

ResourceTypeBaseModel includes helper methods for relationship management:

```python
# Find related resources by RID or API name
related_author = book.get_related_resource(
    Author,
    api_name="john-doe",
    session=session
)

# Link resources with a single method call
author = book.link_author(session=session, author_api_name="jane-roe")
```

### Data Serialization

Enhanced serialization with the `to_dict()` method, including RID components:

```python
# Get a dictionary representation of a resource
book_dict = book.to_dict()
print(book_dict["rid"])         # Full Resource ID (e.g., ri.library.main.book.ulid)
print(book_dict["service"])     # Service name (e.g., 'library')
print(book_dict["instance"])    # Instance name (e.g., 'main')
print(book_dict["resource_type"])# Resource type (e.g., 'book')
print(book_dict["resource_id"]) # ULID locator part
print(book_dict["title"])       # Model field
```

### Field Validation

Utility methods for common validation tasks:

```python
from pydantic import field_validator

class Department(ResourceTypeBaseModel, table=True):
    # ...
    code: str = Field()

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        # Use built-in identifier validation
        return cls.validate_identifier(v, "Department code")

# In another model or logic:
# Validate relationships
# employee.validate_related_field_match(department, "status", "ACTIVE")
```