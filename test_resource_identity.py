def test_single_source_of_truth():
    from registro import Resource
    from registro.resource import Resource as Shim
    from registro.core.resource import Resource as Core
    assert Resource is Shim is Core
