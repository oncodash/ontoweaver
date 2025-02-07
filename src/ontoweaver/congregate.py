import logging
from abc import ABCMeta as ABSTRACT, ABCMeta, abstractmethod

from . import base
from . import serialize

logger = logging.getLogger("ontoweaver")


class Congregater(metaclass=ABCMeta):
    """Interface for classes detecting duplicated elements (nodes or edges) in BioCypher's tuple lists.

    Their contract is to produce a dictionary mapping a key to a list of duplicates.
    The key takes the form of a string made from serializing some members of the targeted elements.
    The serialization is delegated to an object of type serialize.Serialize.

    The result of the duplicates congregation is available through the `duplicates` property.

    Derived classes should implement the __call__ method.
    """

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
        """Call interface

        Args:
            biocypher_tuples: a list of tuples in the BioCypher format for nodes and/or edges.
        """
        raise NotImplementedError


class Congregate(Congregater):
    """A Congregater that detects duplicated elements of the given type (derivatirng from base.Element)."""

    def __init__(self, elem_cls: base.Element, serializer: serialize.Serializer = serialize.All()):
        """ Constructor.

        Args:
            elem_cls: the class of the Elements that will be processed.
            serializer: a serialize.Serializer object giving the key on which to detect duplicated elements.
        """
        logger.debug(f"Instantiate Congregate {type(self).__name__} for element {elem_cls.__name__} with serializer {type(serializer).__name__}")
        assert(issubclass(elem_cls, base.Element))
        self._elem_cls = elem_cls
        super().__init__(serializer)

    def __call__(self, biocypher_tuples):
        """Call interface

        Args:
            biocypher_tuples: a list of tuples in the BioCypher format for nodes xor edges.
        """
        logger.debug(f"Call Congregate...")
        for t in biocypher_tuples:
            elem = self._elem_cls.from_tuple(t, serializer = self.serializer)
            self._duplicates[elem] = self._duplicates.get(elem, []) + [elem]
        if __debug__:
            logger.debug(f"Congregated in {len(self._duplicates)} keys:")
            for k,l in self._duplicates.items():
                logger.debug(f"  Key `{k}` => {len(l)} elements")


class Nodes(Congregate):
    """A Congregater that detects duplicated Nodes."""

    def __init__(self, serializer: serialize.Serializer = serialize.All()):
        """ Constructor.

        Args:
            serializer: a serialize.Serializer object giving the key on which to detect duplicated Nodes.
        """
        super().__init__(base.Node, serializer)


class Edges(Congregate):
    """A Congregater that detects duplicated Edges."""

    def __init__(self, serializer: serialize.Serializer = serialize.All()):
        """ Constructor.

        Args:
            serializer: a serialize.Serializer object giving the key on which to detect duplicated Nodes.
        """
        super().__init__(base.GenericEdge, serializer)

