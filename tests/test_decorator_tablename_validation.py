import pytest
from registro.decorators import resource

def test_tablename_validation():
    """Test that tablename parameter is validated correctly."""
    # tablename with is_table=False should raise ValueError
    with pytest.raises(ValueError, match="tablename='custom' provided but is_table=False"):
        @resource(resource_type="test", tablename="custom", is_table=False)
        class Bad:
            pass
    
    # tablename with is_table=True should work
    @resource(resource_type="test", tablename="custom", is_table=True)
    class Good:
        pass
    
    assert Good.__tablename__ == "custom"
    assert hasattr(Good, "__table__")
