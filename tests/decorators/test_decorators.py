import pytest
from sqlmodel import Field
from registro.decorators import resource
from registro.config.settings import settings

@resource(resource_type="book", service="lib", instance="x")
class Book:
    title: str = Field(default="tic-tac-toe")
    author: str = Field(default="Unknown")


def test_decorator_creates_model_and_table():
    # Instantiation assigns correct attributes
    b = Book(api_name="book", title="1984", author="Orwell")
    assert b.service == "lib"
    assert b.instance == "x"
    assert b.resource_type == "book"
    assert b.api_name == "book"
    assert b.title == "1984"
    assert b.author == "Orwell"


def test_to_dict_on_decorated():
    b = Book(api_name="book", title="Dune")
    data = b.to_dict()
    assert data['title'] == "Dune"
    # author default
    assert data.get('author') == "Unknown"
    assert data['service'] == "lib"
    assert data['instance'] == "x"
    assert data['resource_type'] == "book"
    assert data['api_name'] == "book"
