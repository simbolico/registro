import pytest
import re
from registro.config.settings import settings


def test_get_and_compile_pattern():
    # SERVICE pattern should accept lowercase
    p = settings.get_compiled_pattern("SERVICE")
    assert p is not None
    assert p.match("abc-de")
    assert not p.match("Abc")


def test_set_pattern_and_override():
    # Override SERVICE pattern to digits only
    settings.set_pattern("SERVICE", r"^[0-9]+$")
    p = settings.get_compiled_pattern("SERVICE")
    assert p.match("1234")
    assert not p.match("abcd")
    # Reset back to default for other tests
    settings.set_pattern("SERVICE", r"^[a-z][a-z-]{0,49}$")


def test_get_pattern_string_nonexistent():
    assert settings.get_pattern_string("NONEXISTENT") is None


def test_reserved_words_property():
    rw = settings.RESERVED_WORDS
    assert isinstance(rw, set)
    # Original reserved words include 'null'
    assert 'null' in rw


def test_api_name_patterns_by_type():
    mapping = settings.API_NAME_PATTERNS_BY_TYPE
    assert 'object-type' in mapping
    assert mapping['object-type'] == 'API_NAME_OBJECT_TYPE'


def test_set_pattern_invalid_name():
    with pytest.raises(ValueError):
        settings.set_pattern("UNKNOWN", r".*")
