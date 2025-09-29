def test_resource_singleton():
    from registro import Resource
    from registro.core.resource import Resource as CoreResource
    from registro.resource import Resource as ShimResource
    assert Resource is CoreResource is ShimResource
