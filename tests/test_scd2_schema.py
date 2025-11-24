import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, create_engine, select
from registro.core.resource import Resource
from registro.models.rid import RID
from datetime import datetime, timezone

# Use in-memory SQLite for speed
DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(DATABASE_URL)
    Resource.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Resource.metadata.drop_all(engine)

def test_scd2_schema_allows_history(session: Session):
    """
    Test that the schema allows multiple records with the same RID
    as long as only one is active (valid_to is None).
    """
    rid = RID.generate()
    now = datetime.now(timezone.utc)
    
    # 1. Create first version (Active)
    v1 = Resource(rid=rid, version=1)
    session.add(v1)
    session.commit()
    session.refresh(v1)
    
    assert v1.valid_to is None
    
    # 2. Retire first version
    v1.valid_to = now
    session.add(v1)
    session.commit()
    
    # 3. Create second version (Active) with SAME RID
    # We must explicitly provide a new ID because otherwise it defaults to RID locator
    v2 = Resource(rid=rid, version=2, id=RID.generate().split(".")[-1])
    
    # This should SUCCEED with the new schema
    # But FAIL with the old schema (IntegrityError)
    try:
        session.add(v2)
        session.commit()
    except IntegrityError as e:
        pytest.fail(f"Schema rejected inserting a second version of the same RID: {e}")
        
    # Verify both exist
    stmt = select(Resource).where(Resource.rid == rid)
    results = session.exec(stmt).all()
    assert len(results) == 2

def test_scd2_schema_prevents_double_active(session: Session):
    """
    Test that the schema PREVENTS two active records for the same RID.
    """
    rid = RID.generate()
    
    # 1. Create first version (Active)
    v1 = Resource(rid=rid, version=1)
    session.add(v1)
    session.commit()
    
    # 2. Try to create second version (Active) with SAME RID
    v2 = Resource(rid=rid, version=2, id=RID.generate().split(".")[-1])
    session.add(v2)
    
    # This MUST fail
    with pytest.raises(IntegrityError):
        session.commit()
