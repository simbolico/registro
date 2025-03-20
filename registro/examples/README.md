# Registro Examples

Welcome to the Registro examples directory! This folder contains examples demonstrating various aspects of using Registro for resource management in Python applications.

### Example Files

- **basic_usage.py**: Introductory example using the @resource decorator for resource definition
- **alternative_basic_usage.py**: Shows the ResourceTypeBaseModel inheritance pattern for resource definition
- **custom_resource.py**: Advanced examples with custom validators, status values, and relationships
- **integration_example.py**: Demonstrates integrating Registro with FastAPI for building APIs

### Running the Examples

To run any example, use Python from the project root:

```bash
python -m registro.examples.basic_usage
```

You can also run them directly if you've installed Registro:

```bash
cd registro/examples
python basic_usage.py
```

### Example Highlights

#### Basic Usage Example

Learn the fundamentals of Registro:

- Creating a simple Book resource using the `@resource` decorator
- Working with resource identifiers (RIDs)
- Querying resources
- Understanding resource relationships

Example output:
```
Created: Book(rid=ri.bookshop.demo.book.01H7..., title='Book 1', author='Author 1')
  RID: ri.bookshop.demo.book.01H7...
  Service: bookshop
  Resource Type: book

Found book by API name: Book(rid=ri.bookshop.demo.book.01H7..., title='Book 1', author='Author 1')
```

#### Alternative Basic Usage

- Creating a Book resource model by inheriting from `ResourceTypeBaseModel`
- Understanding the structure of resource identifiers
- Working with SQLModel queries
- Accessing the Resource registry

#### Custom Resource Example

Learn advanced Registro features:

- Creating custom base classes for domain-specific resources
- Implementing custom validation logic
- Working with specialized status values
- Managing relationships between different resource types
- Extending the resource model with business logic

Example code:
```python
class CustomResourceBase(ResourceTypeBaseModel, table=False):
    """Abstract base for all custom resources"""
    __status_values__ = {
        "DRAFT", "ACTIVE", "ARCHIVED", "DEPRECATED"
    }
    
    # Custom fields and methods...
```

#### Integration Example

See how to integrate Registro with web frameworks:

- Building a FastAPI application with Registro resources
- Defining API endpoints for resource operations
- Separating database models from API schemas
- Implementing proper error handling

### Choosing an Approach

Registro offers two ways to create resources:

1. **Decorator approach** (`@resource`):
   - More concise and elegant code
   - Less boilerplate
   - Example: `@resource(resource_type="book") class Book: ...`

2. **Inheritance approach** (`ResourceTypeBaseModel`):
   - More explicit
   - Works reliably when running scripts directly
   - Example: `class Book(ResourceTypeBaseModel, table=True): __resource_type__ = "book" ...`

Both approaches provide the same core functionality, so choose the one that best fits your coding style and requirements.

### Troubleshooting

If you encounter issues with the decorator-based approach (`@resource`), try the inheritance-based alternative (`ResourceTypeBaseModel`). The inheritance approach may be more reliable in certain environments or when running scripts directly.

### Next Steps

After exploring these examples, you'll be ready to integrate Registro into your own applications. Check the main documentation for detailed API reference and advanced topics. 