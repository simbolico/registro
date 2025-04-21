import re
import pytest
from registro.models.rid import RID, generate_ulid, ServiceStr, InstanceStr, TypeStr
from registro.config.settings import settings


def test_generate_ulid_unique_and_format():
    u1 = generate_ulid()
    u2 = generate_ulid()
    assert u1 != u2
    assert re.match(r'^[0-9A-Z]{26}$', u1)


def test_rid_generate_with_defaults():
    rid = RID.generate()
    parts = rid.split('.')
    assert parts[0] == settings.RID_PREFIX
    assert parts[1] == settings.DEFAULT_SERVICE
    assert parts[2] == settings.DEFAULT_INSTANCE
    assert parts[3] == "resource"
    assert len(parts[4]) == 26


def test_rid_validate_valid_and_invalid():
    valid_locator = "0" * 26
    valid_rid = f"{settings.RID_PREFIX}.svc.inst.t.{valid_locator}"
    assert RID.validate(valid_rid, None) == valid_rid
    with pytest.raises(ValueError):
        RID.validate("bad.rid.string", None)


def test_service_instance_type_str_validations():
    assert ServiceStr.validate("svc", None) == "svc"
    with pytest.raises(ValueError):
        ServiceStr.validate("Svc", None)
    assert InstanceStr.validate("inst", None) == "inst"
    with pytest.raises(ValueError):
        InstanceStr.validate("Inst", None)
    assert TypeStr.validate("type-name", None) == "type-name"
    with pytest.raises(ValueError):
        TypeStr.validate("TypeName", None)
