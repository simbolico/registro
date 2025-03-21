# Registro

[![PyPI version](https://badge.fury.io/py/registro.svg)](https://badge.fury.io/py/registro)
[![Python Versions](https://img.shields.io/pypi/pyversions/registro.svg)](https://pypi.org/project/registro/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Registro is a resource management framework for Python applications that provides structured resource identification, validation, and lifecycle management. Built on SQLModel, it offers a consistent approach to defining, creating, and interacting with resources across applications and services.

## Key Features

- **Resource Identifiers (RIDs)**: Globally unique, structured identifiers (`ri.{service}.{instance}.{resource_type}.{id}`) for all resources
- **Dual Implementation Approaches**: Support for both decorator-based (`@resource`) and inheritance-based (`ResourceTypeBaseModel`) implementation
- **SQLModel Integration**: Seamless integration with SQLModel and SQLAlchemy for database operations
- **Validation**: Field and pattern validation through Pydantic with customizable validators
- **Type Safety**: Comprehensive type hints for improved IDE support and runtime type checking
- **Status Management**: Built-in resource status tracking with customizable status values
- **Relationship Handling**: Tools for defining and navigating resource relationships
- **Metadata Management**: Automatic tracking of creation, update, and lifecycle events
- **Relationship Helpers**: Simplified resource linking and relationship management
- **Enhanced Serialization**: Comprehensive to_dict method with relationship support

## Installation

### Standard Installation

```bash
pip install registro
```

### With Rye (Recommended)

```bash
rye add registro
```

## Usage

Registro offers two implementation approaches: inheritance-based and decorator-based.

### Inheritance Approach

Extend `ResourceTypeBaseModel` for explicit control and reliability when running scripts directly:

```python
from registro import ResourceTypeBaseModel
from sqlmodel import Field, Session, SQLModel, create_engine

class Book(ResourceTypeBaseModel, table=True):
    __resource_type__ = "book"
    
    # Define fields
    title: str = Field()
    author: str = Field()
    
    # Optionally specify service and instance in constructor
    def __init__(self, **data):
        # You can now pass service and instance directly to constructor
        super().__init__(**data)
```

### Decorator Approach

Use the `@resource` decorator for a cleaner, more concise syntax:

```python
from registro import resource
from sqlmodel import Field

@resource(resource_type="book")
class Book:
    title: str = Field(...)
    author: str = Field(...)
```

## Relationship Management

ResourceTypeBaseModel provides powerful relationship management tools:

```python
# Define models with relationships
class Author(ResourceTypeBaseModel, table=True):
    __resource_type__ = "author"
    name: str = Field()
    books: List["Book"] = Relationship(back_populates="author")

class Book(ResourceTypeBaseModel, table=True):
    __resource_type__ = "book"
    title: str = Field()
    author_rid: str = Field(foreign_key="author.rid")
    author_api_name: str = Field()
    author: Optional[Author] = Relationship(back_populates="books")
    
    def link_author(self, session, author=None, author_rid=None, author_api_name=None):
        """Link to author using enhanced link_resource helper."""
        return self.link_resource(
            session=session,
            resource=author,
            model_class=Author,
            rid_field="author_rid",
            api_name_field="author_api_name",
            rid_value=author_rid,
            api_name_value=author_api_name
        )
```

## Examples

See the `examples/` directory for complete working examples:

- **Basic Usage**: Simple resource creation and querying
- **Custom Resources**: Advanced resource types with relationships
- **Enhanced Features**: Demonstrations of relationship helpers and validators

## Advanced Features

### Resource Relationships

ResourceTypeBaseModel includes helper methods for relationship management:

```python
# Find related resources by RID or API name
related_resource = book.get_related_resource(
    Author, 
    api_name="john-doe",
    session=session
)

# Link resources with a single method call
book.link_resource(
    session=session,
    model_class=Author,
    rid_field="author_rid",
    api_name_field="author_api_name",
    api_name_value="john-doe"
)
```

### Data Serialization

Enhanced serialization with the `to_dict()` method:

```python
# Get a dictionary representation of a resource
book_dict = book.to_dict()
print(book_dict["rid"])         # Resource ID
print(book_dict["service"])     # Service name
print(book_dict["title"])       # Model field
```

### Field Validation

Utility methods for common validation tasks:

```python
@field_validator("code")
@classmethod
def validate_code(cls, v):
    # Use built-in identifier validation
    return cls.validate_identifier(v, "Department code")

# Validate relationships
cls.validate_related_field_match(author, "status", "ACTIVE")
```

## License

MIT License - See LICENSE file for details. 