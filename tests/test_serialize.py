import ontoweaver

def test_serialize():
    node = ("Source:1", "Source", {"p1":"z"})

    edge = ("Link:0", "Source:1", "Target:2", "Link", {})

    class Source(ontoweaver.base.Node):
        pass
    class Target(ontoweaver.base.Node):
        pass
    class Link(ontoweaver.base.Edge):
        @staticmethod
        def source_type():
            return Source
        @staticmethod
        def target_type():
            return Target

    serializer = ontoweaver.serialize.All()

    s = Source.from_tuple(node, serializer)
    l =   Link.from_tuple(edge, serializer)

    assert(str(s) == "Source:1Source{'p1': 'z'}")
    assert(str(l) == "Source:1Target:2Link:0Link{}")


    serializer = ontoweaver.serialize.ID()

    s = Source.from_tuple(node, serializer)
    l =   Link.from_tuple(edge, serializer)

    assert(str(s) == "Source:1")
    assert(str(l) == "Link:0")


    serializer = ontoweaver.serialize.IDLabel()

    s = Source.from_tuple(node, serializer)
    l =   Link.from_tuple(edge, serializer)

    assert(str(s) == "Source:1Source")
    assert(str(l) == "Link:0Link")


if __name__ == "__main__":
    test_serialize()
