from sqlmodel import SQLModel, Session, create_engine, select, Field
from registro import resource, Resource
from registro.config import settings

def test_decorator_creates_resource_row(tmp_path):
    @resource(resource_type="book")
    class Book:
        title: str = Field(index=True)
    
    db = tmp_path/"t.db"
    engine = create_engine(f"sqlite:///{db}", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as s:
        b = Book(api_name="bk1", display_name="BK1", title="T", service="testsvc", instance="demo")
        s.add(b); s.commit(); s.refresh(b)
        assert b.rid.startswith("ri.testsvc.demo.book.")
        # Resource row exists and matches rid
        r = s.exec(select(Resource).where(Resource.rid == b.rid)).one()
        assert r.service == "testsvc" and r.resource_type == "book"
