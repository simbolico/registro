from sqlmodel import Field
from registro.decorators import resource

@resource(resource_type="product")
class Product:
    api_name: str = Field(index=True)
    price: float = Field(default=0.0, ge=0)  # Field constraint: >= 0

def test_decorator_preserves_field_definitions():
    """Test that Field definitions and constraints are preserved by the decorator."""
    # Check that fields are present
    assert 'api_name' in Product.model_fields
    assert 'price' in Product.model_fields
    
    # Check api_name field
    api_name_field = Product.model_fields['api_name']
    assert api_name_field.annotation == str
    assert api_name_field.is_required() == True
    
    # Check price field with constraint
    price_field = Product.model_fields['price']
    assert price_field.annotation == float
    assert price_field.default == 0.0
    assert price_field.is_required() == False
    
    # Check that the ge=0 constraint is preserved
    metadata = getattr(price_field, 'metadata', [])
    assert len(metadata) > 0
    # The constraint should be there (exact format may vary)
