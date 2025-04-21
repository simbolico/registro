# Registro Examples

Welcome to the Registro examples directory! This folder contains examples demonstrating various aspects of using Registro for resource management in Python applications.

### Example Files

- **basic_usage.py**: Introductory example using the @resource decorator for resource definition
- **alternative_basic_usage.py**: Shows the ResourceTypeBaseModel inheritance pattern for resource definition
- **custom_resource.py**: Advanced examples with custom validators, status values, relationships, and enhanced ResourceTypeBaseModel features
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
- Using enhanced ResourceTypeBaseModel features (relationship helpers, field validators, to_dict)

Example code for enhanced features:
```python
class Employee(ResourceTypeBaseModel, table=True):
    """Employee resource demonstrating relationship helpers."""
    __resource_type__ = "employee"
    
    # Fields...
    department_rid: str = Field(foreign_key="department.rid", index=True)
    department_api_name: str = Field(index=True)
    
    def link_department(self, session, department=None, 
                       department_rid=None, department_api_name=None):
        """Link employee to department using the enhanced link_resource method."""
        return self.link_resource(
            session=session,
            model_class=Department,
            rid_field="department_rid",
            api_name_field="department_api_name",
            api_name_value=department_api_name
        )
```

#### Integration Example

See how to integrate Registro with web frameworks:

- Building a FastAPI application with Registro resources
- Defining API endpoints for resource operations
- Separating database models from API schemas
- Implementing proper error handling

### ResourceTypeBaseModel Enhanced Features

ResourceTypeBaseModel now includes several powerful enhancements:

1. **Simplified Initialization**
   - Pass service and instance directly to constructor
   - Automatically initializes with defaults if not provided

2. **Relationship Helpers**
   - `get_related_resource()`: Find related resources by RID or API name
   - `link_resource()`: Link to another resource with a single method call
   - Simplifies creating and maintaining relationships

3. **Field Validation Utilities**
   - `validate_identifier()`: Ensure field values are valid identifiers
   - `validate_related_field_match()`: Compare fields between related resources

4. **Enhanced Serialization**
   - Improved `to_dict()` method with comprehensive metadata
   - Configurable serialization for relationships

### Choosing an Approach

Registro offers two ways to create resources:

1. **Decorator approach** (`@resource`):
   - More concise and elegant code
   - Less boilerplate
   - Example: `@resource(resource_type="book") class Book: ...`

2. **Inheritance approach** (`ResourceTypeBaseModel`):
   - More explicit
   - Works reliably when running scripts directly
   - Access to enhanced relationship helpers and field validators
   - Example: `class Book(ResourceTypeBaseModel, table=True): __resource_type__ = "book" ...`

Both approaches provide the same core functionality, so choose the one that best fits your coding style and requirements.

### Troubleshooting

If you encounter issues with the decorator-based approach (`@resource`), try the inheritance-based alternative (`ResourceTypeBaseModel`). The inheritance approach may be more reliable in certain environments or when running scripts directly.

### Next Steps

After exploring these examples, you'll be ready to integrate Registro into your own applications. Check the main documentation for detailed API reference and advanced topics. 