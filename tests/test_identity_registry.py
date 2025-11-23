"""
Tests for the new identity and registry system.
"""

import pytest
from datetime import datetime, timezone

from registro.core.identity import RID, new_rid
from registro.core.simple_resource_base import ResourceTypeBaseModel
from registro.core.registry import Registry
from registro.domains.user import User


class TestIdentity:
    """Test the identity module."""
    
    def test_new_rid(self):
        """Test that new_rid generates valid RIDs."""
        rid = new_rid()
        assert isinstance(rid, str)
        assert len(rid) == 26  # ULID standard length
        
        # Ensure multiple calls generate different RIDs
        rid2 = new_rid()
        assert rid != rid2


class TestSimpleResourceBaseModel:
    """Test the simplified ResourceTypeBaseModel."""
    
    def test_resource_creation(self):
        """Test basic resource creation."""
        class TestResource(ResourceTypeBaseModel):
            name: str
            
        resource = TestResource(name="test")
        
        assert resource.name == "test"
        assert resource.rid is not None
        assert isinstance(resource.rid, str)
        assert len(resource.rid) == 26
        assert resource.created_at is not None
        assert resource.updated_at is not None
        assert resource.created_at <= resource.updated_at
        
    def test_type_name(self):
        """Test type_name method."""
        class TestResource(ResourceTypeBaseModel):
            pass
            
        assert TestResource.type_name() == "testresource"
        
    def test_touch(self):
        """Test touch method updates timestamp."""
        class TestResource(ResourceTypeBaseModel):
            pass
            
        resource = TestResource()
        original_updated_at = resource.updated_at
        
        # Small delay to ensure different timestamp
        import time
        time.sleep(0.001)
        
        resource.touch()
        
        assert resource.updated_at > original_updated_at
        assert resource.created_at == resource.created_at  # created_at should not change


class TestRegistry:
    """Test the registry system."""
    
    def setup_method(self):
        """Setup a clean registry for each test."""
        self.registry = Registry()
        
    def test_register_and_get(self):
        """Test registering and getting a type."""
        class TestResource(ResourceTypeBaseModel):
            name: str
            
        self.registry.register("test", TestResource)
        assert self.registry.is_registered("test")
        assert self.registry.get("test") == TestResource
        
    def test_get_nonexistent(self):
        """Test getting a non-existent type raises KeyError."""
        with pytest.raises(KeyError):
            self.registry.get("nonexistent")
            
    def test_unregister(self):
        """Test unregistering a type."""
        class TestResource(ResourceTypeBaseModel):
            pass
            
        self.registry.register("test", TestResource)
        assert self.registry.is_registered("test")
        
        cls = self.registry.unregister("test")
        assert cls == TestResource
        assert not self.registry.is_registered("test")
        
    def test_list_types(self):
        """Test listing registered types."""
        assert self.registry.list_types() == []
        
        class TestResource1(ResourceTypeBaseModel):
            pass
        class TestResource2(ResourceTypeBaseModel):
            pass
            
        self.registry.register("test1", TestResource1)
        self.registry.register("test2", TestResource2)
        
        types = self.registry.list_types()
        assert "test1" in types
        assert "test2" in types
        assert len(types) == 2
        
    def test_create_instance(self):
        """Test creating instances through registry."""
        class TestResource(ResourceTypeBaseModel):
            name: str
            
        self.registry.register("test", TestResource)
        
        instance = self.registry.create_instance("test", name="test_name")
        assert isinstance(instance, TestResource)
        assert instance.name == "test_name"
        assert instance.rid is not None


class TestUserDomain:
    """Test the User domain model."""
    
    def test_user_creation(self):
        """Test creating a user instance."""
        user = User(
            email="test@example.com",
            name="Test User",
            username="testuser"
        )
        
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.username == "testuser"
        assert user.is_active is True  # Default value
        assert user.rid is not None
        assert user.type_name() == "user"
        
    def test_user_registry(self):
        """Test that User is registered with the global registry."""
        from registro.core.registry import registry
        
        assert registry.is_registered("user")
        UserClass = registry.get("user")
        assert UserClass == User
        
    def test_user_creation_via_registry(self):
        """Test creating a user via the registry."""
        from registro.core.registry import registry
        
        user = registry.create_instance(
            "user",
            email="registry@example.com",
            name="Registry User",
            is_active=False
        )
        
        assert isinstance(user, User)
        assert user.email == "registry@example.com"
        assert user.name == "Registry User"
        assert user.is_active is False
