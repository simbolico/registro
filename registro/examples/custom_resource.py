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

# Add the base workspace directory to the Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
workspace_dir = os.path.abspath(os.path.join(parent_dir, '..'))
sys.path.insert(0, workspace_dir)

from typing import ClassVar, Set, Optional, List
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from pydantic import field_validator, ValidationInfo
from registro import BaseResourceType, Resource
from registro.config import settings

"""
## Creating a Base Resource Type

To create custom resources with Registro, you typically:

1. Create a base class that extends `BaseResourceType`
2. Define custom fields, validators, and methods
3. Set the resource service and instance in `__init__`
4. Define status values and other class-level configurations

The example below shows how to create an inventory management system with:
- A base class for all inventory items with custom status values
- Product and DigitalItem resource types extending the base class
- InventoryMovement resource type for tracking stock changes

This pattern allows you to create a domain-specific resource hierarchy.
"""

# Define a custom base class with extended functionality
class InventoryItem(BaseResourceType, table=False):
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
    # This replaces the default status values in BaseResourceType
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

# Create a model for tracking inventory movements
class InventoryMovement(BaseResourceType, table=True):
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


"""
## Database Setup and Resource Creation

Registro works with SQLModel (and SQLAlchemy) for database integration.
This section demonstrates:

1. Setting up a database
2. Creating resource instances
3. Saving resources to the database
4. Working with relationships
5. Implementing business logic
"""

# Create database
sqlite_file = "inventory.db"
if os.path.exists(sqlite_file):
    os.remove(sqlite_file)

engine = create_engine(f"sqlite:///{sqlite_file}", echo=False)  # Set echo=False to reduce output
SQLModel.metadata.create_all(engine)

# Create and save inventory items
with Session(engine) as session:
    # Create physical products
    products = [
        Product(
            api_name=f"product{i}",           # Machine-readable name
            display_name=f"Product {i}",       # Human-readable name
            sku=f"PRD-{i:04d}",                # Stock Keeping Unit
            price=10.99 + i * 5.25,            # Price in currency
            stock_quantity=20 - i,             # Initial stock level
            weight=0.5 + i * 0.25,             # Weight in kg
            dimensions=f"{10+i}x{5+i}x{2+i}"   # Dimensions in cm (LxWxH)
        )
        for i in range(1, 4)
    ]
    
    # Create digital items
    digital_items = [
        DigitalItem(
            api_name=f"digitalItem{i}",                       # Machine-readable name
            display_name=f"Digital Item {i}",                 # Human-readable name
            sku=f"DIG-{i:04d}",                               # Stock Keeping Unit
            price=5.99 + i * 2.00,                            # Price in currency
            stock_quantity=999,                               # High stock (digital)
            file_size=10.5 + i * 20.5,                        # Size in MB
            download_url=f"https://example.com/downloads/item{i}"  # Download URL
        )
        for i in range(1, 3)
    ]
    
    # Add to session and commit
    session.add_all(products)
    session.add_all(digital_items)
    session.commit()
    
    # Apply business logic - update statuses based on stock
    for product in products:
        session.refresh(product)  # Refresh to get the generated RID
        product.update_status_from_stock()  # Update status based on stock quantity
    
    session.commit()
    
    """
    ## Working with Relationships
    
    Here we create InventoryMovement resources that reference products and digital items.
    These movements affect the stock levels of the referenced items and demonstrate:
    
    1. Creating resources with foreign key references
    2. Accessing related resources via relationships
    3. Implementing cross-resource business logic
    """
    
    # Create some inventory movements
    movements = [
        # Add stock to product 1
        InventoryMovement(
            api_name="addStock",
            display_name="Add Stock to Product 1",
            product_rid=products[0].rid,  # Reference to a Product resource by RID
            quantity=5,
            movement_type="ADDITION"
        ),
        # Remove stock from product 2
        InventoryMovement(
            api_name="removeStock",
            display_name="Remove Stock from Product 2",
            product_rid=products[1].rid,  # Reference to a Product resource by RID
            quantity=2,
            movement_type="REMOVAL"
        ),
        # Digital item movement (download)
        InventoryMovement(
            api_name="downloadItem",
            display_name="Download Digital Item 1",
            digital_item_rid=digital_items[0].rid,  # Reference to a DigitalItem resource by RID
            quantity=1,
            movement_type="REMOVAL"  # Track downloads as removals
        )
    ]
    
    session.add_all(movements)
    session.commit()
    
    """
    ## Implementing Business Logic
    
    This section demonstrates how to implement domain-specific business logic
    that spans multiple resources:
    
    1. Update product stock based on movements
    2. Apply status changes based on new stock levels
    3. Use relationships to navigate between resources
    """
    
    # Update product stock based on movements
    for movement in movements:
        session.refresh(movement)  # Refresh to load relationships
        
        # Handle product stock updates
        if movement.product_rid:
            product = movement.product  # Access via relationship
            
            # Apply business rules based on movement type
            if movement.movement_type == "ADDITION":
                product.stock_quantity += movement.quantity
            elif movement.movement_type == "REMOVAL":
                product.stock_quantity = max(0, product.stock_quantity - movement.quantity)
            
            # Update status based on new stock level
            product.update_status_from_stock()
    
    session.commit()

"""
## Querying Resources

Registro works seamlessly with SQLModel for querying resources.
This section demonstrates:

1. Querying specific resource types
2. Accessing related resources
3. Using resource properties
4. Working with the Resource registry
"""

# Query inventory
with Session(engine) as session:
    # Get all products
    products = session.exec(select(Product)).all()
    print("Physical Products:")
    for product in products:
        print(f"  {product.display_name} - SKU: {product.sku}, Price: ${product.price:.2f}")
        print(f"    Status: {product.status}, Stock: {product.stock_quantity}")
        print(f"    RID: {product.rid}")  # Resource Identifier (RID)
        print()
    
    # Get all digital items
    digital_items = session.exec(select(DigitalItem)).all()
    print("Digital Items:")
    for item in digital_items:
        print(f"  {item.display_name} - SKU: {item.sku}, Price: ${item.price:.2f}")
        print(f"    File Size: {item.file_size} MB")
        print(f"    RID: {item.rid}")  # Resource Identifier (RID)
        print()
    
    # Get all inventory movements with their relationships
    movements = session.exec(
        select(InventoryMovement)
    ).all()
    
    print("Inventory Movements:")
    for movement in movements:
        # Use relationships to access related resources
        item_info = ""
        if movement.product:
            item_info = f"Product: {movement.product.display_name}"
        elif movement.digital_item:
            item_info = f"Digital Item: {movement.digital_item.display_name}"
        
        print(f"  {movement.display_name} - {movement.movement_type}, Quantity: {movement.quantity}")
        print(f"    {item_info}")
        print(f"    RID: {movement.rid}")  # Resource Identifier (RID)
        print()
    
    """
    ## Resource Registry
    
    All resources are automatically registered in the Resource table,
    allowing you to query them regardless of their specific type.
    This provides a unified view of all resources in your system.
    """
    
    # Query for all resources in the registry
    resources = session.exec(
        select(Resource).order_by(Resource.resource_type)
    ).all()
    
    # Count resources by type
    resource_types = {}
    for resource in resources:
        if resource.resource_type not in resource_types:
            resource_types[resource.resource_type] = 0
        resource_types[resource.resource_type] += 1
    
    print("Resource Summary:")
    for resource_type, count in resource_types.items():
        print(f"  {resource_type}: {count} resources")

"""
## Best Practices for Using Registro

1. **Resource Organization**:
   - Group related resources under the same service
   - Use meaningful instance names for different deployments
   - Create base classes for resource families with shared behavior

2. **Resource Identification**:
   - Use descriptive resource types
   - Choose meaningful api_names and display_names
   - Let Registro handle RID generation

3. **Validation**:
   - Add field validators for all critical fields
   - Use custom status values appropriate to your domain
   - Implement business logic methods that enforce constraints

4. **Relationships**:
   - Use SQLModel relationships for navigating between resources
   - Reference resources by their RIDs in foreign keys
   - Maintain referential integrity in your business logic

5. **Domain-Driven Design**:
   - Model your resources based on your domain concepts
   - Implement domain-specific behavior in resource methods
   - Use Registro to maintain consistent resource identification across domains
"""

print("\nCustom resource example completed successfully!")
