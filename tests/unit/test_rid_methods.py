"""Test new RID utility methods."""

import pytest
from registro.models.rid import RID


def test_rid_is_valid_type():
    """Test RID type validation method."""
    # Create a RID with type 'user'
    rid = RID("ri.users.main.user.01GXHP6H7TW89BYT4S9C9JM7XX")
    
    # Test valid type
    assert rid.is_valid_type("user") is True
    
    # Test invalid type
    assert rid.is_valid_type("product") is False
    assert rid.is_valid_type("order") is False


def test_rid_is_from_service():
    """Test RID service validation method."""
    # Create a RID with service 'users'
    rid = RID("ri.users.main.user.01GXHP6H7TW89BYT4S9C9JM7XX")
    
    # Test valid service
    assert rid.is_from_service("users") is True
    
    # Test invalid service
    assert rid.is_from_service("products") is False
    assert rid.is_from_service("orders") is False


def test_rid_methods_with_different_types():
    """Test RID methods with different resource types."""
    # Test with different types
    user_rid = RID("ri.users.main.user.01GXHP6H7TW89BYT4S9C9JM7XX")
    product_rid = RID("ri.products.main.product.01GXHP6H7TW89BYT4S9C9JM7XX")
    order_rid = RID("ri.orders.main.order.01GXHP6H7TW89BYT4S9C9JM7XX")
    
    # Test is_valid_type
    assert user_rid.is_valid_type("user") is True
    assert user_rid.is_valid_type("product") is False
    assert user_rid.is_valid_type("order") is False
    
    assert product_rid.is_valid_type("product") is True
    assert product_rid.is_valid_type("user") is False
    assert product_rid.is_valid_type("order") is False
    
    assert order_rid.is_valid_type("order") is True
    assert order_rid.is_valid_type("user") is False
    assert order_rid.is_valid_type("product") is False


def test_rid_methods_with_different_services():
    """Test RID methods with different services."""
    # Test with different services
    users_rid = RID("ri.users.main.user.01GXHP6H7TW89BYT4S9C9JM7XX")
    products_rid = RID("ri.products.main.product.01GXHP6H7TW89BYT4S9C9JM7XX")
    orders_rid = RID("ri.orders.main.order.01GXHP6H7TW89BYT4S9C9JM7XX")
    
    # Test is_from_service
    assert users_rid.is_from_service("users") is True
    assert users_rid.is_from_service("products") is False
    assert users_rid.is_from_service("orders") is False
    
    assert products_rid.is_from_service("products") is True
    assert products_rid.is_from_service("users") is False
    assert products_rid.is_from_service("orders") is False
    
    assert orders_rid.is_from_service("orders") is True
    assert orders_rid.is_from_service("users") is False
    assert orders_rid.is_from_service("products") is False


def test_rid_methods_with_instances():
    """Test RID methods with different instances."""
    # Test with different instances
    prod_rid = RID("ri.users.prod.user.01GXHP6H7TW89BYT4S9C9JM7XX")
    dev_rid = RID("ri.users.dev.user.01GXHP6H7TW89BYT4S9C9JM7XX")
    
    # Test is_valid_type (should work regardless of instance)
    assert prod_rid.is_valid_type("user") is True
    assert dev_rid.is_valid_type("user") is True
    
    # Test is_from_service (should work regardless of instance)
    assert prod_rid.is_from_service("users") is True
    assert dev_rid.is_from_service("users") is True
