# Registro Examples

This directory contains examples demonstrating different ways to use the Registro resource management framework. Each example showcases different features and integration patterns.

## Example Files

- **basic_usage.py**: Demonstrates the core functionality using both decorator and inheritance approaches
- **alternative_basic_usage.py**: Shows the BaseResourceType inheritance pattern for resource definition
- **custom_resource.py**: Shows how to create custom resource types with relationships between resources
- **integration_example.py**: Demonstrates integrating Registro with FastAPI to build a RESTful API

## Running the Examples

To run the examples, execute them directly with Python from the repository root:

```bash
# Run basic usage example
PYTHONPATH=/path/to/workspace python registro/examples/basic_usage.py

# Run alternative basic usage example
PYTHONPATH=/path/to/workspace python registro/examples/alternative_basic_usage.py

# Run custom resource example
PYTHONPATH=/path/to/workspace python registro/examples/custom_resource.py

# Run integration example (requires FastAPI and uvicorn)
PYTHONPATH=/path/to/workspace python registro/examples/integration_example.py
```

## Example Features

### basic_usage.py

Shows the fundamentals of Registro including:
- Creating a Book resource model using the `@resource` decorator
- Setting up a SQLite database for storing resources
- Creating, querying, and working with resources
- Reading resources by API name and other attributes
- Working with resource relationships

### alternative_basic_usage.py

Shows the same functionality as basic_usage.py but using the inheritance approach:
- Creating a Book resource model by inheriting from `BaseResourceType`
- Explicitly setting service and instance values
- Benefit: More reliable when running scripts directly

### custom_resource.py

Demonstrates more advanced features:
- Creating related resources (Product, DigitalItem, InventoryMovement)
- Setting up complex relationships between resources
- Using foreign keys and SQLModel relationships
- Adding custom validation with field validators
- Supporting both decorator and inheritance approaches

### integration_example.py

Shows how to integrate Registro with web frameworks:
- Building a RESTful API with FastAPI
- Creating API schemas with Pydantic models
- Mapping between API requests and resource models
- Implementing CRUD operations for resources
- Handling resource validation in an API context

## Decorator vs. Inheritance Approaches

Registro supports two approaches for creating resource models:

1. **Decorator approach** (`@resource`):
   - More concise and declarative
   - Preferred for imported modules
   - Example: `@resource(resource_type="book") class Book: ...`

2. **Inheritance approach** (`BaseResourceType`):
   - More explicit and traditional
   - More reliable when running scripts directly
   - Example: `class Book(BaseResourceType, table=True): __resource_type__ = "book" ...`

The examples in this directory demonstrate both approaches, and some even implement conditional logic to use the appropriate approach based on how the file is being executed.

## Common Patterns

All examples demonstrate these common patterns:

1. **Resource Definition**: Creating models that represent resources
2. **RID Generation**: Automatic generation of Resource Identifiers (RIDs)
3. **Resource Querying**: Finding resources by RID, API name, or other attributes
4. **Resource Relationships**: Handling references between resources
5. **Resource Metadata**: Accessing and using resource metadata

## Overview

The examples demonstrate how to use Registro to:
- Create and manage resources with unique identifiers
- Build structured, maintainable, and scalable applications
- Use both the decorator and inheritance-based approaches
- Integrate with web frameworks like FastAPI

## Key Features Demonstrated

Across these examples, you'll see:

1. **Using the @resource Decorator**:
   ```python
   @resource(resource_type="product")
   class Product:
       name: str = Field(...)
       price: float = Field(...)
   ```

2. **Creating Custom Resource Types**:
   ```python
   class CustomResourceBase(BaseResourceType, table=False):
       __status_values__ = {"DRAFT", "ACTIVE", "ARCHIVED"}
       # Custom fields and methods...
   ```

3. **Working with Resource Relationships**:
   - Foreign keys referencing other resources
   - Relationship navigation
   - Querying related resources

4. **Status Management**:
   - Custom status values
   - Status transitions
   - Business logic for status updates

5. **RESTful API Design**:
   - Resource-oriented endpoints
   - Clean separation of database models and API schemas
   - Consistent error handling

## Best Practices

These examples follow Registro best practices:
- Resource-oriented design
- Consistent naming conventions
- Clear separation of concerns
- Comprehensive documentation
- Type hints for better IDE support
- Descriptive error messages

## Troubleshooting

If you encounter issues with the decorator-based approach (`@resource`), try the inheritance-based alternative (`BaseResourceType`). The inheritance approach may be more reliable in certain environments or when running scripts directly. 