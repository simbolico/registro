import pytest
from sqlmodel import SQLModel, create_engine, Session

from registro.config.settings import settings

@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite://")

@pytest.fixture(autouse=True)
def create_tables(engine):
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture()
def session(engine):
    with Session(engine) as sess:
        yield sess
