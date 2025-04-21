import re
from registro.models.rid import generate_ulid


def test_generate_ulid_unique_and_length():
    u1 = generate_ulid()
    u2 = generate_ulid()
    assert u1 != u2
    assert len(u1) == len(u2) == 26
    assert re.match(r'^[0-9A-Z]{26}$', u1)
