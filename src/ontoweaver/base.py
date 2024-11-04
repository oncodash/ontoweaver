import logging
import math
import pandas as pd
from collections.abc import Iterable, Generator
from abc import ABCMeta as ABSTRACT, ABCMeta, abstractmethod
from abc import abstractmethod as abstract
from typing import TypeAlias
from typing import Optional

from . import serialize

# TODO? Strategy using a user defined __eq__ method, enabling a more flexible comparison of objects, but in O(n2).
# class Comparer(metaclass=ABCMeta):
#     @abstractmethod
#     def __call__(self, elem1, elem2):
#         raise NotImplementedError
#
# class CompEq(Comparer):
#     def __call__(self, elem1, elem2):
#         return elem1 is elem2
# FIXME use hash functions for comparison.

class Element(metaclass = ABSTRACT):
    """Base class for either Node or Edge.

    Manages allowed properties mechanics."""

    def __init__(self,
                 id        : Optional[str] = None,
                 properties: Optional[dict[str,str]] = {},
                 label     : Optional[str] = None,
                 serializer: Optional[serialize.Serializer] = serialize.All(),
                 ):
        """Instantiate an element.

        :param str id: Unique identifier of the element. If id == None, is then set to the empty string.
        :param dict[str,str] properties: All available properties for this instance.
        :param str label: The label of the element. If label = None, the lower-case version of the class name is used as a label.
        :param Comparer serializer: The comparer to use for equality checks. Default uses the python `is` operator.
        """
        if not id:
            self._id = ''
        else:
            self._id = str(id)

        # Use the setter to get sanity checks.
        self.properties = properties

        if not label:
            self._label = self.__class__.__name__.lower()
        else:
            self._label = str(label)

        self.serializer = serializer

    def __str__(self):
        return self.serializer(self)

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    @staticmethod
    @abstract
    def fields() -> list[str]:
        """List of property fields provided by the (sub)class."""
        raise NotImplementedError

    @abstract
    def as_tuple(self):
        """Convert the element class into Biocypher's expected tuple.

        Filter out properties along the way.
        """
        raise NotImplementedError

    @classmethod
    @abstract
    def from_tuple(cls, t : tuple):
        return cls(t)

    @property
    def id(self) -> str:
        return self._id

    @property
    def label(self) -> str:
        return self._label

    @property
    def properties(self) -> dict[str,str]:
        return self._properties

    @properties.setter
    def properties(self, properties: dict[str,str]):
        """Set available properties.

        Asserts that the passed properties are in the declared fields."""

        # Sanity checks:
        assert(properties is not None)
        # logging.debug(f"Properties of `{type(self).__name__}`: {list(properties.keys())}, available: {list(self.available())}")
        # TODO enable the usage of available() function to disable / enable parts of ontology / certain nodes
        # for p in properties:
        #     if p not in self.available():
        #         logging.error(f"\t\tProperty `{p}` should be available for type `{type(self).__name__}`, available ones: `{list(self.available())}`")
        #         assert(p in self.available())
        self._properties = properties


class Node(Element):
    """Base class for any Node."""

    def __init__(self,
                 id        : Optional[str] = None,
                 properties: Optional[dict[str,str]] = {},
                 label     : Optional[str] = None,  # Set from subclass name.
                 serializer: Optional[serialize.Serializer] = serialize.NodeAll(),
                 ):
        """Instantiate a Node.

        :param str id: Unique identifier of the node. If id == None, is then set to the empty string.
        :param dict[str,str] properties: All available properties for this instance.
        :param str label: The label of the node. If label = None, the lower-case version of the class name is used as a label.
        :param Comparer serializer: The comparer to use for equality checks. Default uses the python `is` operator.
        """
        super().__init__(id, properties, label, serializer)

    Tuple: TypeAlias = tuple[str,str,dict[str,str]]
    def as_tuple(self) -> Tuple:
        """Export the Node as a Biocypher tuple."""
        return (
            self._id,
            self._label,
            # FIXME this has been changed to keep ALL properties. No checking if allowed
            self.properties
        )

    @classmethod
    def from_tuple(cls,
                   biocypher_tuple : tuple[str,str,dict[str,str]],
                   serializer: Optional[serialize.Serializer] = serialize.NodeAll(),
                   ):
        assert(len(biocypher_tuple) == 3)
        return cls(
            id         = biocypher_tuple[0],
            label      = biocypher_tuple[1],
            properties = biocypher_tuple[2],
            serializer = serializer)

    def fields(self) -> list[str]:
        """List of property fields provided by the (sub)class."""
        return list(self.properties.keys())

    def __str__(self):
        return self.serializer(self)

    def __repr__(self):
        return f"<[{self.label}:{self.id}/{self.properties}]>"

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    # def serialize(self):
    #     return {
    #         "id": self._id,
    #         "label": self._label,
    #         "properties": self.properties,
    #         "serializer": self.serializer
    #     }

class Edge(Element):
    """Base class for any Edge."""

    def __init__(self,
                 id        : Optional[str] = None,
                 id_source : Optional[str] = None,
                 id_target : Optional[str] = None,
                 properties: Optional[dict[str,str]] = {},
                 label     : Optional[str] = None,  # Set from subclass name.
                 serializer: Optional[serialize.Serializer] = serialize.EdgeAll(),
                 ):
        """Instantiate an Edge.

        :param str id: Unique identifier of the edge. If id == None, is then set to the empty string.
        :param str id_source: Unique identifier of the source Node. If None, is then set to the empty string.
        :param str id_target: Unique identifier of the target Node. If None, is then set to the empty string.
        :param dict[str,str] properties: All available properties for this instance.
        :param str label: The label of the node. If label = None, the lower-case version of the class name is used as a label.
        :param Comparer comparer: The comparer to use for equality checks. Default uses the python `is` operator.
        """
        super().__init__(id, properties, label, serializer)
        self._id_source = str(id_source)
        self._id_target = str(id_target)

    @staticmethod
    @abstract
    def source_type():
        raise NotImplementedError

    @staticmethod
    @abstract
    def target_type():
        raise NotImplementedError

    @property
    def id_source(self):
        return self._id_source

    @property
    def id_target(self):
        return self._id_target

    Tuple: TypeAlias = tuple[str,str,str,dict[str,str]]
    def as_tuple(self) -> Tuple:
        """Export the Edge as a Biocypher tuple."""
        return (
            self._id,
            self._id_source,
            self._id_target,
            self._label,
            #.FIXME no checking if properties are allowed allowed_properties()
            self.properties
        )

    @classmethod
    def from_tuple(cls,
                   biocypher_tuple : tuple[str,str,str,str,dict[str,str]],
                   serializer: Optional[serialize.Serializer] = serialize.EdgeAll(),
                   ):
        assert(len(biocypher_tuple) == 5)
        return cls(
            id         = biocypher_tuple[0],
            id_source  = biocypher_tuple[1],
            id_target  = biocypher_tuple[2],
            label      = biocypher_tuple[3],
            properties = biocypher_tuple[4],
            serializer = serializer)

    def __repr__(self):
        return f"<[{self.source_type()}:{self.id_source}]--({self.label}:{self.id}/{self.properties})-->[{self.target_type()}:{self.id_target}]>"

    def fields(self) -> list[str]:
        """List of property fields provided by the (sub)class."""
        return list(self.properties.keys())

    def __str__(self):
        return self.serializer(self)

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    # def serialize(self):
    #     return {
    #         "id": self._id,
    #         "id_source": self._id_source,
    #         "id_target": self._id_target,
    #         "label": self._label,
    #         "properties": self.properties,
    #         "serializer": self.serializer
    #     }

class GenericEdge(Edge):
    """Base class for any Edge."""

    def __init__(self,
                 id        : Optional[str] = None,
                 id_source : Optional[str] = None,
                 id_target : Optional[str] = None,
                 properties: Optional[dict[str,str]] = {},
                 label     : Optional[str] = None,  # Set from subclass name.
                 serializer: Optional[serialize.Serializer] = serialize.EdgeAll(),
                 ):
        """Instantiate an Edge.

        :param str id: Unique identifier of the edge. If id == None, is then set to the empty string.
        :param str id_source: Unique identifier of the source Node. If None, is then set to the empty string.
        :param str id_target: Unique identifier of the target Node. If None, is then set to the empty string.
        :param dict[str,str] properties: All available properties for this instance.
        :param str label: The label of the node. If label = None, the lower-case version of the class name is used as a label.
        :param Comparer comparer: The comparer to use for equality checks. Default uses the python `is` operator.
        """
        super().__init__(id, properties, label, serializer)
        self._id_source = str(id_source)
        self._id_target = str(id_target)

    @staticmethod
    def source_type():
        return Node

    @staticmethod
    def target_type():
        return Node


class Adapter(metaclass = ABSTRACT):
    """Base class for implementing a canonical Biocypher adapter."""

    def __init__(self,
    ):
        """Allow to indicate which Element subclasses and which property fields
        are allowed to be exported by Biocypher.

        :param Iterable[Node] node_types: Allowed Node subclasses.
        :param Iterable[Edge] edge_types: Allowed Edge subclasses.
        """

        self._nodes = []
        self._edges = []
        self.errors = []

    def nodes_append(self, node_s) -> None:
        """Append an Node (or each Node in a list of nodes) to the internal list of nodes."""
        if issubclass(type(node_s), Node):
            nodes = [node_s]
        else:
            nodes = node_s

        # logging.debug(f"Nodes: {nodes}.")
        for node in nodes:
            # logging.debug(f"\tAppend node {node}.")
            if node in self._nodes:
                # logging.warning(f"\t\tSkipped Node already declared: `{node}`")
                # return False
                pass
            else:
                self._nodes.append(node.as_tuple())
                # return True

    def edges_append(self, edge_s) -> None:
        """Append an Edge (or each Edge in a list of edges) to the internal list of edges."""
        if issubclass(type(edge_s), Edge):
            edges = [edge_s]
        else:
            edges = edge_s

        # logging.debug(f"Edges: {edges}.")
        for edge in edges:
            # logging.debug(f"\tAppend edge {edge}.")
            if edge in self._edges:
                # logging.warning(f"\t\tSkipped Edge already declared: `{edge}`")
                # return False
                pass
            else:
                self._edges.append(edge.as_tuple())
                # return True

    @property
    def nodes(self) -> Iterable[Node.Tuple]:
        """Return a generator yielding nodes."""
        for n in self._nodes:
            yield n

    @property
    def edges(self) -> Iterable[Edge.Tuple]:
        """Return a generator yielding edges."""
        for e in self._edges:
            yield e


class Transformer:
    """"Class used to manipulate cell values and return them in the correct format."""""

    def __init__(self, target, properties_of, edge = None, columns = None, **kwargs):
        """
        Instantiate transformers.

        :param target: the target ontology / node type to map to.
        :param properties_of: the properties of each node type.
        :param edge: the edge type to use in the mapping.
        :param columns: the columns to use in the mapping.

        """

        self.target = target
        self.properties_of = properties_of
        self.edge = edge
        self.columns = columns
        self.parameters = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_transformer(self):
        return self

    @abstract
    def __call__(self, row, i):
        raise NotImplementedError

    @abstract
    def nodes(self):
        raise NotImplementedError

    @abstract
    def edges(self):
        raise NotImplementedError

    @staticmethod
    @abstract
    def edge_type():
        raise NotImplementedError

    @staticmethod
    @abstract
    def target_type():
       raise NotImplementedError

    @classmethod
    def source_type(cls):
       return cls.edge_type().source_type()

    def valid(self, val):
        if pd.api.types.is_numeric_dtype(type(val)):
            if (math.isnan(val) or val == float("nan")):
                return False
        elif str(val) == "nan":  # Conversion from Pandas' `object` needs to be explicit. # TODO test also for empty strings, in case pandas is not used. Double check if works for paralelization.
            return False
        return True

    def __repr__(self):
        if hasattr(self, "from_subject"):
            from_subject = self.from_subject
        else:
            from_subject = "."

        if self.target:
            target_name = self.target.__name__
        else:
            target_name = "."

        if self.edge:
            edge_name = self.edge.__name__
        else:
            edge_name = "."

        if self.properties_of:
            props = self.properties_of
        else:
            props = "{}"

        params = ""
        parameters = {k:v for k,v in self.parameters.items() if k not in ['subclass', 'from_subject']}
        if parameters:
            p = []
            for k,v in parameters.items():
                p.append(f"{k}={v}")
            params = ','.join(p)

        if from_subject == "." and edge_name == "." and target_name == "." and props == "{}":
            # If this is a property transformer
            link = ""

        elif from_subject == "." and edge_name == "." and (target_name != "." or props != "{}"):
            # This a subject transformer.
            link = f" => [{target_name}/{props}]"

        else:
            # This is a regular transformer.
            link = f" => [{from_subject}]--({edge_name})->[{target_name}/{props}]"

        if self.columns:
            columns = self.columns
        else:
            columns = []

        return f"<Transformer:{type(self).__name__}({params}) {','.join(columns)}{link}>"

class All:
    """Gathers lists of subclasses of Element and their fields
    existing in a given module.

    Is generally used to create an `all` variable in a module:
    .. code-block:: python

        all = base.All(sys.modules[__name__])

    Which can later be used to pass all available Element types to an Adapter:
    .. code-block:: python

        a = MyAdapter( node_types = MyModule.all.nodes() )
    """

    def __init__(self, module):
        self.module = module

    def elements(self, asked: Element = Element) -> list[Element]:
        m = self.module.__dict__
        classes = []
        for c in m:
            if isinstance(m[c], type) \
            and m[c].__module__ == self.module.__name__ \
            and issubclass(m[c], asked):
                classes.append(m[c])
                logging.debug(f"Found `{asked.__name__}` class: `{m[c]}` (prop: `{m[c].fields()}`).")
                # t = m[c]
                # logging.debug(f"\t\t#### {t.mro()[:-3]}/{t.__name__} => {t.fields()}")
        return classes

    def nodes(self) -> list[Node]:
        return self.elements(Node)

    def edges(self) -> list[Edge]:
        return self.elements(Edge)

    def node_fields(self) -> list[str]:
        names = [] # FIXME use a set?
        for c in self.nodes():
            names += c.fields()
        return names

    def edge_fields(self) -> list[str]:
        names = [] # FIXME use a set?
        for c in self.edges():
            names += c.fields()
        return names









