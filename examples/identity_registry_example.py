"""
Example demonstrating the new identity and registry system in Registro.

This example shows how to:
1. Use the centralized identity management
2. Create domain models with the simplified base
3. Use the global registry for resource management
"""

from registro.core.identity import RID, new_rid
from registro.core.simple_resource_base import ResourceTypeBaseModel
from registro.core.registry import registry
from registro.domains.user import User

# 1. Identity Management
print("=== Identity Management ===")
rid = new_rid()
print(f"Generated RID: {rid}")
print(f"RID type: {type(rid)}")

# Generate multiple RIDs to show uniqueness
rids = [new_rid() for _ in range(3)]
print(f"Generated RIDs: {rids}")
print(f"All unique: {len(set(rids)) == len(rids)}")

# 2. Custom Resource Types
print("\n=== Custom Resource Types ===")

class Product(ResourceTypeBaseModel):
    """Example product resource."""
    name: str
    price: float
    description: str = ""

# Register the Product type
registry.register("product", Product)

# Create a product instance
product = Product(name="Laptop", price=999.99, description="High-performance laptop")
print(f"Product: {product.model_dump()}")
print(f"Product type name: {product.type_name()}")

# 3. Registry Usage
print("\n=== Registry Usage ===")
print(f"Registered types: {registry.list_types()}")

# Create instances through registry
user = registry.create_instance("user", email="john@example.com", name="John Doe")
product = registry.create_instance("product", name="Mouse", price=29.99)

print(f"User: {user.model_dump()}")
print(f"Product: {product.model_dump()}")

# 4. Timestamp Management
print("\n=== Timestamp Management ===")
print(f"User created at: {user.created_at}")
print(f"User updated at: {user.updated_at}")

# Touch the user to update timestamp
import time
time.sleep(0.01)  # Small delay
user.touch()
print(f"User updated at after touch: {user.updated_at}")
print(f"Updated timestamp changed: {user.updated_at > user.created_at}")

# 5. Type Information
print("\n=== Type Information ===")
print(f"User class: {User}")
print(f"Product class from registry: {registry.get('product')}")
print(f"Is User registered: {registry.is_registered('user')}")
print(f"Is Product registered: {registry.is_registered('product')}")
