from sqlmodel import SQLModel, Field, Session, create_engine, select
from registro.core.resource_base import ResourceTypeBaseModel
from registro.core import Resource
from registro.config import settings

class Book(ResourceTypeBaseModel, table=True):
    __resource_type__ = "book"
    api_name: str = Field(index=True)
    title: str = Field(index=True)

def test_inserting_book_creates_resource(tmp_path):
    settings.DEFAULT_SERVICE = "testsvc"
    settings.DEFAULT_INSTANCE = "demo"
    db = tmp_path / "t.db"
    eng = create_engine(f"sqlite:///{db}")
    SQLModel.metadata.create_all(eng)

    with Session(eng) as s:
        b = Book(api_name="bk1", title="Title")
        s.add(b); s.commit(); s.refresh(b)
        assert b.rid.startswith(f"{settings.RID_PREFIX}.testsvc.demo.book.")
        r = s.exec(select(Resource).where(Resource.rid == b.rid)).one()
        assert r.service == "testsvc" and r.resource_type == "book"
