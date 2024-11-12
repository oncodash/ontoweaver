from abc import ABCMeta as ABSTRACT, ABCMeta, abstractmethod

from . import base

class Serializer(metaclass=ABSTRACT):
    """Inteface for classes serializing base.Elements by producing a string
    from any part of the state of interest.

    This is used by congregate.Congretater to decide if two elements are duplicates.
    Elements having the same serialization will be considered as duplicates.
    """

    @abstractmethod
    def __call__(self, elem):
        raise NotImplementedError

class node:
    """Serializers operating on base.Node(s)."""

    class ID(Serializer):
        """Serialize a Node by using its ID."""
        def __call__(self, node):
            assert(issubclass(type(node), base.Node))
            return node.id

    class IDLabel(Serializer):
        """Serialize a Node by using its ID and label."""
        def __init__(self):
            self.id = ID()
        def __call__(self, node):
            assert(issubclass(type(node), base.Node))
            return self.id(node) + node.label

    class All(Serializer):
        """Serialize a Node by using its ID, label and properties."""
        def __init__(self):
            self.idlbl = IDLabel()
        def __call__(self, node):
            assert(issubclass(type(node), base.Node))
            return self.idlbl(node) + str(node.properties)

class edge:
    """Serializers operating on base.Edge(s)."""

    class ID(Serializer):
        """Serialize an Edge by using its ID."""
        def __call__(self, edge):
            assert(issubclass(type(edge), base.Edge))
            return edge.id

    class IDLabel(Serializer):
        """Serialize an Edge by using its ID and label."""
        def __init__(self):
            self.id = ID()
        def __call__(self, edge):
            assert(issubclass(type(edge), base.Edge))
            return self.id(edge) + edge.label

    class SourceTarget(Serializer):
        """Serialize an Edge by using its id_source and id_target."""
        def __call__(self, edge):
            assert(issubclass(type(edge), base.Edge))
            return edge.id_source + edge.id_target

    class SourceTargetLabel(Serializer):
        """Serialize an Edge by using its id_source, id_target and label."""
        def __init__(self):
            self.ST = edge.SourceTarget()
        def __call__(self, edge):
            assert(issubclass(type(edge), base.Edge))
            return self.ST(edge) + edge.label

    class All(Serializer):
        """Serialize an Edge by using its id_source, id_target, label and properties."""
        def __init__(self):
            self.idlbl = IDLabel()
            self.ST = edge.SourceTarget()
        def __call__(self, edge):
            assert(issubclass(type(edge), base.Edge))
            return self.ST(edge) + self.idlbl(edge) + str(edge.properties)


class ID(Serializer):
    """Serialize an Edge or a Node by using its ID."""
    def __init__(self):
        self.nodeid = node.ID()
        self.edgeid = edge.ID()

    def __call__(self, elem):
        if issubclass(type(elem), base.Node):
            return self.nodeid(elem)
        elif issubclass(type(elem), base.Edge):
            return self.edgeid(elem)
        else:
            assert(issubclass(type(elem), base.Node) or issubclass(type(elem), base.Edge))

class IDLabel(Serializer):
    """Serialize an Edge or a Node by using its ID and label."""
    def __init__(self):
        self.nodeidlbl = node.IDLabel()
        self.edgeidlbl = edge.IDLabel()

    def __call__(self, elem):
        if issubclass(type(elem), base.Node):
            return self.nodeidlbl(elem)
        elif issubclass(type(elem), base.Edge):
            return self.edgeidlbl(elem)
        else:
            assert(issubclass(type(elem), base.Node) or issubclass(type(elem), base.Edge))

class All(Serializer):
    """Serialize a Node or an Edge by using all their members. """
    def __init__(self):
        self.nodeall = node.All()
        self.edgeall = edge.All()

    def __call__(self, elem):
        if issubclass(type(elem), base.Node):
            return self.nodeall(elem)
        elif issubclass(type(elem), base.Edge):
            return self.edgeall(elem)
        else:
            assert(issubclass(type(elem), base.Node) or issubclass(type(elem), base.Edge))

