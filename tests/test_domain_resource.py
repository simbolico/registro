import pytest
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import EmailStr, Field

from registro import DomainResource, Resource
from registro.models.rid import RID

class User(DomainResource):
    name: str
    email: str
    preferences: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

def test_domain_resource_to_envelope():
    user = User(
        name="Kevin",
        email="kevin@example.com",
        preferences={"theme": "dark"},
        tags=["admin", "dev"]
    )
    
    # Verify logical object
    assert user.name == "Kevin"
    # Default service='default', instance='prod' based on error message
    assert user.rid.startswith("ri.default.prod.resource.")
    
    # Convert to envelope
    envelope = user.to_envelope()
    
    # Verify physical object
    assert isinstance(envelope, Resource)
    assert envelope.rid == user.rid
    assert envelope.version == 1
    
    # Check meta_tags (should contain non-SQL columns)
    assert envelope.meta_tags["name"] == "Kevin"
    assert envelope.meta_tags["email"] == "kevin@example.com"
    assert envelope.meta_tags["preferences"] == {"theme": "dark"}
    assert envelope.meta_tags["tags"] == ["admin", "dev"]
    
    # Check SQL columns (should NOT be in meta_tags if they are columns)
    # But 'name' and 'email' are NOT columns in Resource, so they ARE in meta_tags.
    # 'rid', 'created_at', 'version' ARE columns.
    assert "rid" not in envelope.meta_tags
    assert "version" not in envelope.meta_tags
    assert "created_at" not in envelope.meta_tags

def test_domain_resource_from_envelope():
    # Create a physical resource manually (simulating DB load)
    rid = RID.generate()
    now = datetime.now(timezone.utc)
    
    payload = {
        "name": "Alice",
        "email": "alice@example.com",
        "preferences": {"lang": "en"},
        "tags": ["user"]
    }
    
    envelope = Resource(
        id=rid.split(".")[-1],
        rid=rid,
        service="test",
        instance="main",
        resource_type="user",
        version=2,
        created_at=now,
        updated_at=now,
        meta_tags=payload
    )
    
    # Hydrate domain object
    user = User.from_envelope(envelope)
    
    assert isinstance(user, User)
    assert user.rid == rid
    assert user.version == 2
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.preferences == {"lang": "en"}
    assert user.tags == ["user"]
    
    # Verify internal cache
    assert user._physical_cache == envelope

def test_domain_resource_schema_evolution():
    # Simulate a scenario where the class has a new field 'phone'
    # but the DB record (envelope) doesn't have it yet (or vice versa)
    
    class UserV2(User):
        phone: Optional[str] = None
        
    rid = RID.generate()
    payload = {
        "name": "Bob",
        "email": "bob@example.com",
        # 'phone' is missing in payload
    }
    
    envelope = Resource(
        id=rid.split(".")[-1],
        rid=rid,
        meta_tags=payload
    )
    
    user = UserV2.from_envelope(envelope)
    assert user.name == "Bob"
    assert user.phone is None
    
    # Now add phone and save back
    user.phone = "123-456"
    new_envelope = user.to_envelope()
    
    assert new_envelope.meta_tags["phone"] == "123-456"
