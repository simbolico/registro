from registro.decorators import resource

@resource(resource_type="virtual", is_table=False)
class Virtual:
    api_name: str

def test_virtual_is_not_mapped():
    """Test that is_table=False creates a non-table model."""
    assert getattr(Virtual, "__table__", None) is None
    assert Virtual.__resource_type__ == "virtual"
    # Should still inherit base fields from ResourceTypeBaseModel
    assert "rid" in Virtual.model_fields
    assert "api_name" in Virtual.model_fields
