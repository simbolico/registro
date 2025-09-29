from sqlmodel import Field
from registro.decorators import resource

@resource(resource_type="widget", tablename="custom_widgets")
class Widget:
    api_name: str = Field(index=True)
    size: str = Field(default="medium")

def test_decorator_custom_tablename():
    """Test that custom tablename parameter works."""
    assert Widget.__tablename__ == "custom_widgets"
    assert hasattr(Widget, '__table__')
    
    # Should still have proper resource type
    assert Widget.__resource_type__ == "widget"
