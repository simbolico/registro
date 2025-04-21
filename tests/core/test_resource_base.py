import pytest
from sqlmodel import Field
from registro.core.resource_base import ResourceTypeBaseModel
from registro.config.settings import settings

# Dummy model for testing ResourceTypeBaseModel
class Dummy(ResourceTypeBaseModel, table=True):
    __resource_type__ = "dummy"
    api_name: str = Field(default="dummy_api")
    foo: int = Field(default=123)

def test_rid_and_resource_creation(session):
    d = Dummy()
    session.add(d)
    session.commit()
    session.refresh(d)
    assert d.rid.startswith(settings.RID_PREFIX)
    # Underlying Resource model exists
    res = d.get_resource(session)
    assert res is not None
    assert res.rid == d.rid

def test_to_dict_includes_components(session):
    d = Dummy()
    session.add(d)
    session.commit()
    session.refresh(d)
    res = d.get_resource(session)
    data = d.to_dict()
    assert data["service"] == settings.DEFAULT_SERVICE
    assert data["instance"] == settings.DEFAULT_INSTANCE
    assert data["resource_type"] == "dummy"
    # ResourceTypeBaseModel.to_dict does not include resource_id alias
    assert "resource_id" not in data
    assert data["rid"] == d.rid
    assert data["id"] == d.id

def test_resource_relationship_property(session):
    d = Dummy()
    session.add(d)
    session.commit()
    session.refresh(d)
    # get_resource returns the linked Resource instance
    res = d.get_resource(session)
    assert res.rid == d.rid
