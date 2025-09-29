from sqlmodel import SQLModel, Field, Session, create_engine, select
from registro.core.resource_base import ResourceTypeBaseModel
from registro.core import Resource
from registro.config import settings

class Novel(ResourceTypeBaseModel, table=True):
    __resource_type__ = "novel"
    api_name: str = Field(index=True)
    title: str = Field(index=True)

def test_inserting_novel_creates_resource(tmp_path, monkeypatch):
    # Use monkeypatch to avoid leaking global state changes between tests
    monkeypatch.setattr(settings, "DEFAULT_SERVICE", "testsvc")
    monkeypatch.setattr(settings, "DEFAULT_INSTANCE", "demo")
    
    db = tmp_path / "t.db"
    eng = create_engine(f"sqlite:///{db}")
    SQLModel.metadata.create_all(eng)

    with Session(eng) as s:
        b = Novel(api_name="bk1", title="Title")
        s.add(b); s.commit(); s.refresh(b)
        assert b.rid.startswith(f"{settings.RID_PREFIX}.testsvc.demo.novel.")
        r = s.exec(select(Resource).where(Resource.rid == b.rid)).one()
        assert r.service == "testsvc" and r.resource_type == "novel"
