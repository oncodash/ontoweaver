from abc import ABCMeta as ABSTRACT, ABCMeta, abstractmethod

from . import base

class Serializer(metaclass=ABSTRACT):
    @abstractmethod
    def __call__(self, elem):
        raise NotImplementedError

class node:
    class ID(Serializer):
        def __call__(self, node):
            assert(issubclass(type(node), base.Node))
            return node.id

    class IDLabel(Serializer):
        def __init__(self):
            self.id = ID()
        def __call__(self, node):
            assert(issubclass(type(node), base.Node))
            return self.id(node) + node.label

    class All(Serializer):
        def __init__(self):
            self.idlbl = IDLabel()
        def __call__(self, node):
            assert(issubclass(type(node), base.Node))
            return self.idlbl(node) + str(node.properties)

class edge:
    class ID(Serializer):
        def __call__(self, edge):
            assert(issubclass(type(edge), base.Edge))
            return edge.id

    class IDLabel(Serializer):
        def __init__(self):
            self.id = ID()
        def __call__(self, edge):
            assert(issubclass(type(edge), base.Edge))
            return self.id(edge) + edge.label

    class SourceTarget(Serializer):
        def __call__(self, edge):
            assert(issubclass(type(edge), base.Edge))
            return edge.id_source + edge.id_target

    class SourceTargetLabel(Serializer):
        def __init__(self):
            self.ST = edge.SourceTarget()
        def __call__(self, edge):
            assert(issubclass(type(edge), base.Edge))
            return self.ST(edge) + edge.label

    class All(Serializer):
        def __init__(self):
            self.idlbl = IDLabel()
            self.ST = edge.SourceTarget()
        def __call__(self, edge):
            assert(issubclass(type(edge), base.Edge))
            return self.ST(edge) + self.idlbl(edge) + str(edge.properties)


class ID(Serializer):
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

