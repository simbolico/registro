from sqlmodel import SQLModel, Session, create_engine, select, Field
from registro import resource, Resource
from registro.config import settings

def test_decorator_creates_resource_row(tmp_path):
    @resource(resource_type="item")  # Use different resource type to avoid table conflicts
    class Item:
        title: str = Field(index=True)
    
    db = tmp_path/"t.db"
    engine = create_engine(f"sqlite:///{db}", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as s:
        b = Item(api_name="item1", display_name="Item1", title="T", service="testsvc", instance="demo")
        s.add(b); s.commit(); s.refresh(b)
        assert b.rid.startswith("ri.testsvc.demo.item.")
        # Resource row exists and matches rid
        r = s.exec(select(Resource).where(Resource.rid == b.rid)).one()
        assert r.service == "testsvc" and r.resource_type == "item"
