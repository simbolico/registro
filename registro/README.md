# Registro

[![PyPI version](https://badge.fury.io/py/registro.svg)](https://badge.fury.io/py/registro)
[![Python Versions](https://img.shields.io/pypi/pyversions/registro.svg)](https://pypi.org/project/registro/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A resource-based model system for SQLModel with automatic Resource creation and validation.

## Features

- 🔑 **Resource Identifiers (RIDs)**: Globally unique, structured identifiers for all resources
- 🔄 **Automatic Resource Creation**: Creates resources automatically when models are persisted
- 🧩 **SQLModel Integration**: Seamless integration with SQLModel and SQLAlchemy
- ✅ **Validation**: Strong field and pattern validation with Pydantic v2
- 🔍 **Type Safety**: Fully typed with type hints and runtime validation
- 📝 **Documentation**: Comprehensive docstrings and examples

## Installation

```bash
pip install registro
```

### With Rye (recommended)

```bash
rye add registro
```

## Quick Start

```python
from registro import Resource, ResourceBase
from sqlmodel import Field, Session, SQLModel, create_engine

# Define a model with resource capabilities
class Book(ResourceBase, table=True):
    __resource_type__ = "book"

    title: str = Field(index=True)
    author: str = Field(index=True)
    year: int = Field(default=2023)

# Create database engine
engine = create_engine("sqlite:///library.db")
SQLModel.metadata.create_all(engine)

# Create and save a book (resource is created automatically)
with Session(engine) as session:
    book = Book(title="The Hitchhiker's Guide to the Galaxy", author="Douglas Adams", year=1979)
    session.add(book)
    session.commit()
    
    # Access the resource ID
    print(f"Book RID: {book.rid}")
    print(f"Service: {book.service}")
    print(f"Resource Type: {book.resource_type}")
```

## Why Registro?

Registro ("registry" in Spanish/Portuguese) provides a systematic way to create and manage resources in your SQLModel-based application:

1. **Consistency**: All resources follow the same identification and lifecycle patterns
2. **Discoverability**: Structured RIDs make resources easily discoverable
3. **Relationships**: Simplified relationship management between resources
4. **Traceability**: Track resource lineage across services and systems

## Documentation

For full documentation, visit [https://yourusername.github.io/registro](https://yourusername.github.io/registro)

## Examples

See the [examples](examples/) directory for more usage examples:

- [Basic Usage](examples/basic_usage.py): Simple resource creation and querying
- [Custom Resources](examples/custom_resource.py): Extending resource types
- [Integration Example](examples/integration_example.py): Using with a complete application

## License

This project is licensed under the MIT License - see the LICENSE file for details. 