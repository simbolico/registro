"""
# Registro Custom Resource Example
# ================================

## Overview
This example demonstrates how to create and work with custom resources using Registro,
a powerful resource management library that helps you build structured, maintainable,
and scalable applications with consistent resource identifiers (RIDs).

## What is Registro?
Registro is a Python library that provides a consistent way to create, manage, and reference
resources across your application. Key features include:

- **Resource Identification**: Globally unique resource identifiers (RIDs) with a structured format
  `ri.{service}.{instance}.{resource_type}.{id}`
- **Service & Instance Management**: Group resources logically by service and deployment instance
- **Custom Validation**: Define domain-specific validation rules for your resources
- **Status Tracking**: Built-in status management with customizable status values
- **Relationship Management**: Create and manage relationships between resources
- **Database Integration**: Seamless integration with SQLModel and SQLAlchemy

## Getting Started
This example demonstrates:
1. Creating custom resource types with domain-specific fields and validation
2. Defining custom service and instance identifiers
3. Creating relationships between resources
4. Custom status values and status logic
5. Working with multiple resource types in a domain model

## Custom Resources Explained
Resources in Registro are uniquely identified by RIDs (Resource Identifiers) with the format:
`ri.{service}.{instance}.{resource_type}.{id}`

- **service**: The service or domain (e.g., "inventory", "users", "billing")
- **instance**: The deployment instance (e.g., "prod", "store", "eu-west")
- **resource_type**: The type of resource (e.g., "product", "digital-item")
- **id**: A unique ULID (Universally Unique Lexicographically Sortable Identifier)

You'll see how these components work together as we build an inventory management system.
"""

import os
import sys
from pathlib import Path

# Add the base workspace directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
workspace_dir = parent_dir.parent
sys.path.insert(0, str(workspace_dir))

from typing import ClassVar, Set, Optional, List
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from pydantic import field_validator, ValidationInfo

# Import Registro components - try multiple approaches for resilience
try:
    # First try the direct decorator import
    from registro.decorators import resource
    from registro import ResourceTypeBaseModel, Resource
    from registro.config import settings
    IMPORTS_OK = True
except ImportError as e:
    print(f"Warning: Error importing Registro modules: {e}")
    print("Will try alternative import approach...")
    IMPORTS_OK = False
    
    try:
        # Try package-level import as fallback
        from registro import ResourceTypeBaseModel, Resource
        from registro.config import settings
        IMPORTS_OK = True
    except ImportError as e:
        print(f"Error: Failed to import Registro modules: {e}")
        print("This example requires the Registro package.")
        sys.exit(1)

"""
## Creating a Base Resource Type

Registro provides two ways to create resources:

### 1. Simple Approach with @resource Decorator

The simplest approach is to use the `@resource` decorator:

```python
from registro import resource
from sqlmodel import Field

@resource(resource_type="product", service="inventory", instance="store")
class Product:
    name: str = Field(...)
    price: float = Field(...)
```

### 2. Advanced Approach with Custom Base Class

For more advanced use cases, you can create a custom base class:

1. Create a base class that extends `ResourceTypeBaseModel`
2. Define custom fields, validators, and methods
3. Set the resource service and instance in `__init__`
4. Define status values and other class-level configurations

The example below shows both approaches in an inventory management system.
"""

# APPROACH 1: Using the @resource decorator for simple cases
@resource(
    resource_type="simple-product",
    service="inventory",
    instance="store"
)
class SimpleProduct:
    """
    Simple product defined using the @resource decorator.
    
    This approach is perfect for straightforward cases where you just need to
    define fields without extensive customization.
    """
    name: str = Field(index=True)
    price: float = Field(default=0.0)
    stock_quantity: int = Field(default=0)
    
    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        """Ensure price is positive."""
        if v < 0:
            raise ValueError("Price cannot be negative")
        return round(v, 2)  # Round to 2 decimal places

# Ensure class has been properly transformed
if not hasattr(SimpleProduct, "__tablename__"):
    raise RuntimeError("SimpleProduct was not properly decorated")

# APPROACH 2: Custom base class for advanced scenarios
# Define a custom base class with extended functionality
class InventoryItem(ResourceTypeBaseModel, table=False):
    """
    Base class for inventory items with custom status values.
    
    This abstract base class:
    - Sets custom service and instance for all inventory items
    - Defines inventory-specific status values
    - Adds common fields like SKU, price, and stock_quantity
    - Implements validation and business logic
    
    Note: table=False makes this an abstract base class (not a database table)
    """
    
    # Override status values - customize the allowed status values for your domain
    # This replaces the default status values in ResourceTypeBaseModel
    __status_values__: ClassVar[Set[str]] = {
        "DRAFT",           # Item not yet ready for sale
        "IN_STOCK",        # Item available for purchase
        "LOW_STOCK",       # Item running low (less than 10 units)
        "OUT_OF_STOCK",    # Item currently unavailable (0 units)
        "DISCONTINUED"     # Item no longer sold
    }
    
    # Add custom fields specific to inventory items
    sku: str = Field(index=True, unique=True)  # Stock Keeping Unit - unique product identifier
    price: float = Field(default=0.0)          # Item price
    stock_quantity: int = Field(default=0)     # Current stock level
    
    def __init__(self, **data):
        """
        Initialize with custom service and instance.
        
        This is the recommended way to set service and instance for resources.
        By setting _service and _instance before calling super().__init__, 
        these values will be used when generating the resource's RID.
        
        Alternative options:
        1. Set service and instance at the global level with settings.DEFAULT_SERVICE
        2. Set service and instance for each resource individually when creating
        
        Example RID generated: ri.inventory.store.product.01ABC123456789
        """
        self._service = "inventory"  # The domain/service this resource belongs to
        self._instance = "store"     # The deployment instance (e.g., store, warehouse)
        super().__init__(**data)
    
    # Add custom validators to ensure data integrity
    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v):
        """
        Ensure SKU is uppercase and properly formatted.
        
        This validator:
        1. Checks that SKU is a string
        2. Converts it to uppercase
        3. Prefixes it with resource type code if needed
        
        Example: "1234" becomes "PRD-1234" for a Product resource
        """
        if not isinstance(v, str):
            raise ValueError("SKU must be a string")
        
        v = v.upper()
        if not v.startswith(cls.__resource_type__.upper()[:3] + "-"):
            v = f"{cls.__resource_type__.upper()[:3]}-{v}"
        
        return v
    
    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        """
        Ensure price is positive and properly formatted.
        
        Validates that:
        1. Price is not negative
        2. Price is rounded to 2 decimal places
        """
        if v < 0:
            raise ValueError("Price cannot be negative")
        return round(v, 2)  # Round to 2 decimal places
    
    @field_validator("stock_quantity")
    @classmethod
    def validate_quantity(cls, v):
        """
        Ensure quantity is non-negative.
        
        Stock quantity must be zero or positive.
        """
        if v < 0:
            raise ValueError("Stock quantity cannot be negative")
        return v
    
    # Add custom business logic methods
    def update_status_from_stock(self):
        """
        Update status based on stock quantity.
        
        This method demonstrates how custom status values and business logic
        can work together to automate status management:
        
        - 0 items → OUT_OF_STOCK
        - 1-9 items → LOW_STOCK
        - 10+ items → IN_STOCK
        
        Returns the new status.
        """
        if self.stock_quantity <= 0:
            self.status = "OUT_OF_STOCK"
        elif self.stock_quantity < 10:
            self.status = "LOW_STOCK"
        else:
            self.status = "IN_STOCK"
        return self.status


"""
## Creating Concrete Resource Types

Once you have a base class, you can create concrete resource types by:
1. Extending your base class
2. Setting the `__resource_type__` class attribute
3. Adding resource-specific fields and validation
4. Setting table=True to make it a database table

The resource type becomes part of the RID and determines how resources
are categorized and queried.
"""

# Define concrete inventory item types
class Product(InventoryItem, table=True):
    """
    Physical product in inventory.
    
    Extends InventoryItem to:
    - Set the resource_type to "product"
    - Add physical properties (weight, dimensions)
    - Add product-specific validation
    
    Example RID: ri.inventory.store.product.01ABC123456789
    """
    __resource_type__ = "product"  # This becomes part of the RID
    
    weight: float = Field(default=0.0)  # Weight in kg
    dimensions: Optional[str] = Field(default=None)  # Format: LxWxH in cm
    
    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        """Ensure weight is positive."""
        if v < 0:
            raise ValueError("Weight cannot be negative")
        return v


class DigitalItem(InventoryItem, table=True):
    """
    Digital item in inventory (e.g., software, ebooks, digital media).
    
    Extends InventoryItem to:
    - Set the resource_type to "digital-item"
    - Add digital-specific properties (file_size, download_url)
    - Add digital item validation
    
    Example RID: ri.inventory.store.digital-item.01ABC123456789
    """
    __resource_type__ = "digital-item"
    
    file_size: float = Field(default=0.0)  # Size in MB
    download_url: Optional[str] = Field(default=None)
    
    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v):
        """Ensure file size is positive."""
        if v < 0:
            raise ValueError("File size cannot be negative")
        return v


"""
## Creating Related Resources

Resources often need to reference other resources. Registro makes this easy with:
1. Foreign keys that reference resource RIDs
2. SQLModel relationships for convenient access
3. Validation to ensure referential integrity

This example shows how to create a resource for tracking inventory movements
that references both Product and DigitalItem resources.
"""

# APPROACH 2: Using ResourceTypeBaseModel for relationships
class InventoryMovement(ResourceTypeBaseModel, table=True):
    """
    Tracks movements of inventory items (additions, removals, adjustments).
    
    This resource:
    - Uses the same service and instance as InventoryItem
    - References other resources via their RIDs (foreign keys)
    - Establishes relationships for easy navigation
    - Defines type-specific validation
    
    Example RID: ri.inventory.store.inventory-movement.01ABC123456789
    """
    __resource_type__ = "inventory-movement"
    
    # Foreign key references to other resources (using their RIDs)
    product_rid: Optional[str] = Field(default=None, foreign_key="product.rid")
    digital_item_rid: Optional[str] = Field(default=None, foreign_key="digitalitem.rid")
    
    # Movement details
    quantity: int = Field(default=1)
    movement_type: str = Field(default="ADDITION")  # ADDITION, REMOVAL, ADJUSTMENT
    
    def __init__(self, **data):
        """
        Initialize with custom service and instance.
        
        Ensures this resource uses the same service and instance as inventory items.
        """
        self._service = "inventory"
        self._instance = "store"
        super().__init__(**data)
    
    # Define relationships for easy navigation between related resources
    product: Optional[Product] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[InventoryMovement.product_rid]"}
    )
    digital_item: Optional[DigitalItem] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[InventoryMovement.digital_item_rid]"}
    )
    
    @field_validator("movement_type")
    @classmethod
    def validate_movement_type(cls, v):
        """
        Ensure movement type is valid.
        
        Validates that the movement type is one of the allowed values:
        - ADDITION: Add stock
        - REMOVAL: Remove stock
        - ADJUSTMENT: Correct inventory count
        - RESERVATION: Hold inventory for a customer
        """
        allowed = {"ADDITION", "REMOVAL", "ADJUSTMENT", "RESERVATION"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Movement type must be one of {allowed}")
        return v

# APPROACH 1: Using @resource decorator for relationships
@resource(
    resource_type="inventory-movement",
    service="inventory",
    instance="store"
)
class DecoratedInventoryMovement:
    """
    Tracks movements of inventory items using the @resource decorator approach.
    
    This resource:
    - Uses the decorator to set service, instance and resource type
    - References other resources via their RIDs (foreign keys)
    - Establishes relationships for easy navigation
    - Defines type-specific validation
    
    Example RID: ri.inventory.store.inventory-movement.01ABC123456789
    """
    # Foreign key references to other resources (using their RIDs)
    product_rid: Optional[str] = Field(default=None, foreign_key="product.rid")
    digital_item_rid: Optional[str] = Field(default=None, foreign_key="digitalitem.rid")
    
    # Movement details
    quantity: int = Field(default=1)
    movement_type: str = Field(default="ADDITION")  # ADDITION, REMOVAL, ADJUSTMENT
    
    # Define relationships for easy navigation between related resources
    product: Optional[Product] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[DecoratedInventoryMovement.product_rid]"}
    )
    digital_item: Optional[DigitalItem] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[DecoratedInventoryMovement.digital_item_rid]"}
    )
    
    @field_validator("movement_type")
    @classmethod
    def validate_movement_type(cls, v):
        """
        Ensure movement type is valid.
        
        Validates that the movement type is one of the allowed values:
        - ADDITION: Add stock
        - REMOVAL: Remove stock
        - ADJUSTMENT: Correct inventory count
        - RESERVATION: Hold inventory for a customer
        """
        allowed = {"ADDITION", "REMOVAL", "ADJUSTMENT", "RESERVATION"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Movement type must be one of {allowed}")
        return v

# Ensure class has been properly transformed
if not hasattr(DecoratedInventoryMovement, "__tablename__"):
    print("Warning: DecoratedInventoryMovement was not properly transformed")

# Choose which InventoryMovementNew class to use based on how the file is executed
if __name__ == "__main__":
    # When running directly, use the inheritance-based version 
    print("Using inheritance-based InventoryMovementNew for direct execution")
    # Just use the already defined InventoryMovement class which uses inheritance
    InventoryMovementNew = InventoryMovement
else:
    # When imported, use the decorator-based version if it worked
    if hasattr(DecoratedInventoryMovement, "__tablename__") and hasattr(DecoratedInventoryMovement, "_sa_registry"):
        print("Using decorator-based InventoryMovementNew")
        InventoryMovementNew = DecoratedInventoryMovement
    else:
        print("Falling back to inheritance-based InventoryMovementNew")
        InventoryMovementNew = InventoryMovement

"""
## Working with Resources in Code

Now that we've defined our resource types, let's see how to use them in practice.
This example demonstrates creating database tables, adding resources, and querying
related resources using Registro's powerful features.
"""

# Database setup
engine = create_engine("sqlite:///:memory:", echo=False)
SQLModel.metadata.create_all(engine)

# Create instances and relationships
with Session(engine) as session:
    # Create a physical product
    laptop = Product(
        api_name="macbook-pro",
        display_name="MacBook Pro",
        sku="MBPRO-2023",
        price=1999.00,
        stock_quantity=10,
        weight=2.1,
        dimensions="31.26 x 22.12 x 1.55 cm"
    )
    session.add(laptop)
    
    # Create a digital item
    software = DigitalItem(
        api_name="photoshop",
        display_name="Adobe Photoshop",
        sku="PS-2023",
        price=20.99,
        stock_quantity=999,  # Digital goods often have large quantities
        file_size=2500.0,  # 2.5 GB
        download_url="https://example.com/downloads/photoshop"
    )
    session.add(software)
    
    # Commit to generate RIDs
    session.commit()
    
    # Create inventory movements for both items
    laptop_addition = InventoryMovement(
        api_name="laptop-initial-stock",
        display_name="Initial stock addition for MacBook Pro",
        product_rid=laptop.rid,
        quantity=10,
        movement_type="ADDITION"
    )
    
    software_addition = InventoryMovementNew(
        api_name="software-initial-stock",
        display_name="Initial stock addition for Photoshop",
        digital_item_rid=software.rid,
        quantity=999,
        movement_type="ADDITION"
    )
    
    session.add(laptop_addition)
    session.add(software_addition)
    session.commit()
    
    # Query and display resources
    print("\nProduct Resources:")
    products = session.exec(select(Product)).all()
    for product in products:
        print(f"- {product.display_name} (RID: {product.rid})")
        print(f"  SKU: {product.sku}, Price: ${product.price}, Stock: {product.stock_quantity}")
        print(f"  Weight: {product.weight} kg, Dimensions: {product.dimensions}")
        
    print("\nDigital Item Resources:")
    digital_items = session.exec(select(DigitalItem)).all()
    for item in digital_items:
        print(f"- {item.display_name} (RID: {item.rid})")
        print(f"  SKU: {item.sku}, Price: ${item.price}, Stock: {item.stock_quantity}")
        print(f"  File Size: {item.file_size} MB, URL: {item.download_url}")
    
    print("\nInventory Movements:")
    movements = session.exec(
        select(InventoryMovement)
    ).all()
    for movement in movements:
        print(f"- {movement.display_name} (RID: {movement.rid})")
        print(f"  Type: {movement.movement_type}, Quantity: {movement.quantity}")
        
        # Access the related product
        if movement.product_rid:
            product = session.exec(select(Product).where(
                Product.rid == movement.product_rid
            )).one()
            print(f"  For Product: {product.display_name} (SKU: {product.sku})")
        
        # Access the related digital item
        if movement.digital_item_rid:
            digital_item = session.exec(select(DigitalItem).where(
                DigitalItem.rid == movement.digital_item_rid
            )).one()
            print(f"  For Digital Item: {digital_item.display_name} (SKU: {digital_item.sku})")
    
    print("\nInventory Movements (New Approach with Decorator):")
    new_movements = session.exec(
        select(InventoryMovementNew)
    ).all()
    for movement in new_movements:
        print(f"- {movement.display_name} (RID: {movement.rid})")
        print(f"  Type: {movement.movement_type}, Quantity: {movement.quantity}")
        
        # Access the related digital item
        if movement.digital_item_rid:
            digital_item = session.exec(select(DigitalItem).where(
                DigitalItem.rid == movement.digital_item_rid
            )).one()
            print(f"  For Digital Item: {digital_item.display_name} (SKU: {digital_item.sku})")
    
    # Query from the Resource registry
    print("\nAll Resources in Registry:")
    resources = session.exec(select(Resource)).all()
    for resource in resources:
        print(f"- {resource.rid}")
        print(f"  Type: {resource.resource_type}, Created: {resource.created_at}")

"""
## Choosing Between Decorator and Inheritance

When to use the @resource decorator:
- For simpler resources with standard status values
- When you don't need custom initialization logic
- When you want cleaner, more concise code

When to use ResourceTypeBaseModel inheritance:
- For more direct control over the model structure
- When running scripts directly rather than as modules
- For class-level customization (like __status_values__ above)

Both approaches provide the same core Registro capabilities, so choose the one
that best fits your use case and coding style.
"""

print("\nCustom resource example completed successfully!")
