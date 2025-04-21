import re
import pytest
from registro.models.patterns import validate_string, RESERVED_WORDS


def test_validate_string_happy_path():
    pattern = re.compile(r'^[a-z]+$')
    assert validate_string("abc", pattern, set(), "field") == "abc"


def test_validate_string_type_error():
    pattern = re.compile(r'.*')
    with pytest.raises(TypeError):
        validate_string(123, pattern, set(), "field")


def test_validate_string_pattern_mismatch():
    pattern = re.compile(r'^[0-9]+$')
    with pytest.raises(ValueError) as exc:
        validate_string("abc", pattern, set(), "field")
    assert "does not match pattern" in str(exc.value)


def test_validate_string_reserved_word():
    pattern = re.compile(r'^[a-z]+$')
    with pytest.raises(ValueError) as exc:
        validate_string("null", pattern, {"null"}, "field")
    assert "reserved word" in str(exc.value).lower()
