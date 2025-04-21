import pytest
import re
from registro.models.rid import RID, get_rid_pattern, LocatorStr
from registro.config.settings import settings

VALID_LOCATOR = "0" * 26
VALID_RID = f"{settings.RID_PREFIX}.svc.inst.t.{VALID_LOCATOR}"


def test_validate_accepts_valid_rid():
    assert RID.validate(VALID_RID, None) == VALID_RID


def test_validate_rejects_missing_parts():
    with pytest.raises(ValueError, match="RID must have 5 parts"):  # 4 parts only
        RID.validate("a.b.c.d", None)


def test_validate_rejects_wrong_prefix():
    bad = VALID_RID.replace(settings.RID_PREFIX, "xx", 1)
    with pytest.raises(ValueError, match="RID prefix.*must be"):  # wrong prefix
        RID.validate(bad, None)


def test_validate_rejects_invalid_service_format():
    # uppercase service
    bad = f"{settings.RID_PREFIX}.Svc.inst.t.{VALID_LOCATOR}"
    with pytest.raises(ValueError):
        RID.validate(bad, None)


def test_validate_rejects_invalid_locator():
    # too short locator
    bad = f"{settings.RID_PREFIX}.svc.inst.t.{'0'*25}"
    with pytest.raises(ValueError):
        RID.validate(bad, None)


def test_get_rid_pattern_matches_valid_and_invalid():
    pattern = get_rid_pattern()
    assert pattern.match(VALID_RID)
    # missing trailing part
    assert not pattern.match(VALID_RID.rsplit('.',1)[0])
    # wrong type char
    bad = VALID_RID.replace('.t.', '.T.')
    assert not pattern.match(bad)


def test_locatorstr_rejects_invalid_characters():
    # invalid characters not in ULID allowed set
    with pytest.raises(ValueError):
        LocatorStr.validate("O"*26, None)  # 'O' is disallowed
