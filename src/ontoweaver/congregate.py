from abc import ABCMeta as ABSTRACT, ABCMeta, abstractmethod

from . import base
from . import serialize

class Congregater(metaclass=ABCMeta):
    def __init__(self, serializer: serialize.Serializer = serialize.All()):
        self._serializer = serializer
        self._duplicates = {}

    @property
    def serializer(self):
        return self._serializer

    @property
    def duplicates(self):
        return self._duplicates

    @abstractmethod
    def __call__(self, biocypher_tuples):
        raise NotImplementedError


class Congregate(Congregater):
    def __init__(self, elem_cls: base.Element, serializer: serialize.Serializer = serialize.All()):
        assert(issubclass(elem_cls, base.Element))
        self._elem_cls = elem_cls
        super().__init__(serializer)

    def __call__(self, biocypher_tuples):
        for t in biocypher_tuples:
            elem = self._elem_cls.from_tuple(t, serializer = self.serializer)
            self._duplicates[elem] = self._duplicates.get(elem, []) + [elem]

class Nodes(Congregate):
    def __init__(self, serializer: serialize.Serializer = serialize.All()):
        super().__init__(base.Node, serializer)

class Edges(Congregate):
    def __init__(self, serializer: serialize.Serializer = serialize.All()):
        super().__init__(base.GenericEdge, serializer)

