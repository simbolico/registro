# Registro

[![PyPI version](https://badge.fury.io/py/registro.svg)](https://badge.fury.io/py/registro)
[![Python Versions](https://img.shields.io/pypi/pyversions/registro.svg)](https://pypi.org/project/registro/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Registro is a resource management framework for Python applications that provides structured resource identification, validation, and lifecycle management. Built on SQLModel, it offers a consistent approach to defining, creating, and interacting with resources across applications and services.

## Key Features

- **Resource Identifiers (RIDs)**: Globally unique, structured identifiers (`ri.{service}.{instance}.{resource_type}.{id}`) for all resources
- **Dual Implementation Approaches**: Support for both decorator-based (`@resource`) and inheritance-based (`BaseResourceType`) implementation
- **SQLModel Integration**: Seamless integration with SQLModel and SQLAlchemy for database operations
- **Validation**: Field and pattern validation through Pydantic with customizable validators
- **Type Safety**: Comprehensive type hints for improved IDE support and runtime type checking
- **Status Management**: Built-in resource status tracking with customizable status values
- **Relationship Handling**: Tools for defining and navigating resource relationships
- **Metadata Management**: Automatic tracking of creation, update, and lifecycle events

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

Extend `BaseResourceType` for explicit control and reliability when running scripts directly:

```python
from registro import BaseResourceType
from sqlmodel import Field, Session, SQLModel, create_engine

class Book(BaseResourceType, table=True):
    __resource_type__ = "book"
    
    # Define service and instance in __init__
    def __init__(self, **data):
        self._service = "library"
        self._instance = "prod"
        super().__init__(**data)
    
    # Resource-specific fields
    title: str = Field(index=True)
    author: str = Field(index=True)
    year: int = Field(default=2023)
```

### Decorator Approach

Use the `@resource` decorator for concise, declarative definitions:

```python
from registro import resource
from sqlmodel import Field, SQLModel

@resource(resource_type="book", service="library", instance="prod")
class Book:
    # Resource-specific fields
    title: str = Field(index=True)
    author: str = Field(index=True)
    year: int = Field(default=2023)
```

### Working with Resources

```python
# Database setup
engine = create_engine("sqlite:///library.db")
SQLModel.metadata.create_all(engine)

# Create and save resources
with Session(engine) as session:
    # Create a book resource
    book = Book(
        title="The Hitchhiker's Guide to the Galaxy",
        author="Douglas Adams",
        year=1979,
        api_name="hitchhikers-guide",  # Required for resource identification
        display_name="Hitchhiker's Guide to the Galaxy"  # Human-readable name
    )
    session.add(book)
    session.commit()
    
    # Access resource properties
    print(f"Book RID: {book.rid}")                     # ri.library.prod.book.01ABC123...
    print(f"Service: {book.service}")                  # library
    print(f"Resource Type: {book.resource_type}")      # book
    
    # Query resources
    from sqlmodel import select
    
    # Find by API name (unique identifier)
    result = session.exec(
        select(Book).where(Book.api_name == "hitchhikers-guide")
    ).first()
    
    # Find by RID (globally unique)
    result = session.exec(
        select(Book).where(Book.rid == "ri.library.prod.book.01ABC123...")
    ).first()
```

## Implementation Approaches

### When to Use the Inheritance Approach

- For scripts that are run directly (`python script.py`)
- When creating domain-specific base classes
- For custom status values or lifecycle management
- When you need explicit control over service and instance values

### When to Use the Decorator Approach

- For cleaner, more concise code
- When the module is primarily imported by other modules
- When using standard resource lifecycle patterns
- For simpler resources without custom initialization needs

## Advanced Features

### Custom Status Values

```python
class InventoryItem(BaseResourceType, table=False):
    __status_values__ = {
        "DRAFT", "IN_STOCK", "LOW_STOCK", 
        "OUT_OF_STOCK", "DISCONTINUED"
    }
    
    # Status-specific logic
    def update_status_from_stock(self):
        if self.stock_quantity <= 0:
            self.status = "OUT_OF_STOCK"
        elif self.stock_quantity < 10:
            self.status = "LOW_STOCK"
        else:
            self.status = "IN_STOCK"
```

### Resource Relationships

```python
class Order(BaseResourceType, table=True):
    __resource_type__ = "order"
    
    # Foreign key to customer resource
    customer_rid: str = Field(foreign_key="customer.rid")
    
    # Relationship definition
    customer: "Customer" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Order.customer_rid]"}
    )
```

### Custom Validation

```python
from pydantic import field_validator

class Product(BaseResourceType, table=True):
    __resource_type__ = "product"
    
    sku: str = Field(index=True)
    price: float = Field(default=0.0)
    
    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v):
        """Ensure SKU is uppercase and properly formatted."""
        if not isinstance(v, str):
            raise ValueError("SKU must be a string")
        return v.upper()
    
    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        """Ensure price is positive and properly formatted."""
        if v < 0:
            raise ValueError("Price cannot be negative")
        return round(v, 2)  # Round to 2 decimal places
```

## Examples

The repository includes comprehensive examples demonstrating Registro's capabilities:

- **basic_usage.py**: Fundamental resource creation and querying
- **alternative_basic_usage.py**: Inheritance-based resource definition
- **custom_resource.py**: Advanced resource types with relationships
- **integration_example.py**: Using Registro with FastAPI

Each example demonstrates both decorator and inheritance approaches and includes detailed documentation and best practices.

## Configuration

Configure Registro's default service and instance through settings:

```python
from registro.config import settings

# Set global defaults
settings.DEFAULT_SERVICE = "my-service"
settings.DEFAULT_INSTANCE = "prod"
```

## Best Practices

1. **Use appropriate approach**: Choose decorator or inheritance based on your use case
2. **Be consistent**: Use the same approach throughout your application
3. **Include required fields**: Always set `api_name` and `display_name`
4. **Handle direct execution**: Use conditional logic when scripts may be run directly
5. **Implement validation**: Add field validators for domain-specific rules
6. **Document resource types**: Include clear docstrings for all resource classes

## License

MIT License - See LICENSE file for details. 