from abc import ABCMeta as ABSTRACT, ABCMeta, abstractmethod

from . import base

class Serializer(metaclass=ABSTRACT):
    @abstractmethod
    def __call__(self, elem):
        raise NotImplementedError


class NodeID(Serializer):
    def __call__(self, node):
        assert(issubclass(type(node), base.Node))
        return node.id

class NodeIDLabel(Serializer):
    def __init__(self):
        self.id = NodeID()
    def __call__(self, node):
        assert(issubclass(type(node), base.Node))
        return self.id(node) + node.label

class NodeAll(Serializer):
    def __init__(self):
        self.idlbl = NodeIDLabel()
    def __call__(self, node):
        assert(issubclass(type(node), base.Node))
        return self.idlbl(node) + str(node.properties)


class EdgeID(Serializer):
    def __call__(self, edge):
        assert(issubclass(type(edge), base.Edge))
        return edge.id + edge.id_source + edge.id_target

class EdgeIDLabel(Serializer):
    def __init__(self):
        self.id = EdgeID()
    def __call__(self, edge):
        assert(issubclass(type(edge), base.Edge))
        return self.id(edge) + edge.label

class EdgeAll(Serializer):
    def __init__(self):
        self.idlbl = EdgeIDLabel()
    def __call__(self, edge):
        assert(issubclass(type(edge), base.Edge))
        return self.idlbl(edge) + str(edge.properties)


class ID(Serializer):
    def __init__(self):
        self.nodeid = NodeID()
        self.edgeid = EdgeID()

    def __call__(self, elem):
        if issubclass(type(elem), base.Node):
            return self.nodeid(elem)
        elif issubclass(type(elem), base.Edge):
            return self.edgeid(elem)
        else:
            assert(issubclass(type(elem), base.Node) or issubclass(type(elem), base.Edge))

class IDLabel(Serializer):
    def __init__(self):
        self.nodeidlbl = NodeIDLabel()
        self.edgeidlbl = EdgeIDLabel()

    def __call__(self, elem):
        if issubclass(type(elem), base.Node):
            return self.nodeidlbl(elem)
        elif issubclass(type(elem), base.Edge):
            return self.edgeidlbl(elem)
        else:
            assert(issubclass(type(elem), base.Node) or issubclass(type(elem), base.Edge))

class All(Serializer):
    def __init__(self):
        self.nodeall = NodeAll()
        self.edgeall = EdgeAll()

    def __call__(self, elem):
        if issubclass(type(elem), base.Node):
            return self.nodeall(elem)
        elif issubclass(type(elem), base.Edge):
            return self.edgeall(elem)
        else:
            assert(issubclass(type(elem), base.Node) or issubclass(type(elem), base.Edge))

