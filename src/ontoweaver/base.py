import logging
from collections.abc import Iterable
from abc import ABCMeta as ABSTRACT, abstractmethod
from abc import abstractmethod as abstract
from typing import TypeAlias
from typing import Optional

from . import errormanager
from . import serialize
from . import exceptions
from . import transformer
import types

logger = logging.getLogger("ontoweaver")

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

class ErrorManager:
    def __init__(self, raise_errors = True):
        self.raise_errors = raise_errors

    def error(self, msg, section = None, index = None, exception = RuntimeError, indent = 0):
        location = ""
        if section:
            location = f" [for {section}"
            if index:
                location += f" #{index}"
            location += "]"

        err = "\t"*indent
        err += msg
        err += location

        logger.error(err)

        if self.raise_errors:
            raise exception(err)

        return err


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
        :param str label: The label of the element.
        :param Comparer serializer: The comparer to use for equality checks. Default uses the python `is` operator.
        """
        if not id:
            self._id = ''
        else:
            self._id = str(id)

        # Use the setter to get sanity checks.
        self.properties = properties

        if not label:
            # Do not change the name here, or BioCypher will have problem
            # finding back labels.
            self._label = self.__class__.__name__ 
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
    def from_tuple(cls,
                   biocypher_tuple : tuple,
                   serializer: Optional[serialize.Serializer] = serialize.All()
        ):
        # return cls(biocypher_tuple,serializer)
        raise NotImplementedError

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
        assert(type(properties) == dict)
        # logger.debug(f"Properties of `{type(self).__name__}`: {list(properties.keys())}, available: {list(self.available())}")
        # TODO enable the usage of available() function to disable / enable parts of ontology / certain nodes
        # for p in properties:
        #     if p not in self.available():
        #         logger.error(f"\t\tProperty `{p}` should be available for type `{type(self).__name__}`, available ones: `{list(self.available())}`")
        #         assert(p in self.available())
        self._properties = properties


class Node(Element):
    """Base class for any Node."""

    def __init__(self,
                 id        : Optional[str] = None,
                 properties: Optional[dict[str,str]] = {},
                 label     : Optional[str] = None,  # Set from subclass name.
                 serializer: Optional[serialize.Serializer] = serialize.node.All(),
                 ):
        """Instantiate a Node.

        :param str id: Unique identifier of the node. If id == None, is then set to the empty string.
        :param dict[str,str] properties: All available properties for this instance.
        :param str label: The label of the node.
        :param Comparer serializer: The comparer to use for equality checks. Default uses the python `is` operator.
        """
        super().__init__(id = id, properties = properties, label = label, serializer = serializer)

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
                   serializer: Optional[serialize.Serializer] = serialize.node.All(),
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
        return f"({self.label}:{self.id}/{self.properties})"

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
                 serializer: Optional[serialize.Serializer] = serialize.edge.All(),
                 ):
        """Instantiate an Edge.

        :param str id: Unique identifier of the edge. If id == None, is then set to the empty string.
        :param str id_source: Unique identifier of the source Node. If None, is then set to the empty string.
        :param str id_target: Unique identifier of the target Node. If None, is then set to the empty string.
        :param dict[str,str] properties: All available properties for this instance.
        :param str label: The label of the node.
        :param Comparer comparer: The comparer to use for equality checks. Default uses the python `is` operator.
        """
        super().__init__(id = id, properties = properties, label = label, serializer = serializer)
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

    @id_source.setter
    def id_source(self, id_source):
        self._id_source = id_source

    @property
    def id_target(self):
        return self._id_target

    @id_target.setter
    def id_target(self, id_target):
        self._id_target = id_target

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
                   serializer: Optional[serialize.Serializer] = serialize.edge.All()
                   ):
        assert(len(biocypher_tuple) == 5)
        logging.debug(biocypher_tuple)
        return cls(
            id         = biocypher_tuple[0],
            id_source  = biocypher_tuple[1],
            id_target  = biocypher_tuple[2],
            properties = biocypher_tuple[4],
            label      = biocypher_tuple[3],
            serializer = serializer)

    def __repr__(self):
        if self.source_type() == Node:
            st = "."
        elif self.source_type() == None:
            st = ""
        else:
            st = f"{self.source_type().__name__}"
        if self.target_type() == Node:
            tt = "."
        else:
            tt = f"{'>'.join([t.__name__ for t in self.target_type()])}"

        return f"<({st}:{self.id_source})--[{self.label}:{self.id}/{self.properties}]-->({tt}:{self.id_target})>"

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
                 serializer: Optional[serialize.Serializer] = serialize.edge.All(),
                 ):
        """Instantiate an Edge.

        :param str id: Unique identifier of the edge. If id == None, is then set to the empty string.
        :param str id_source: Unique identifier of the source Node. If None, is then set to the empty string.
        :param str id_target: Unique identifier of the target Node. If None, is then set to the empty string.
        :param dict[str,str] properties: All available properties for this instance.
        :param str label: The label of the node.
        :param Comparer comparer: The comparer to use for equality checks. Default uses the python `is` operator.
        """
        super().__init__(id = id, id_source = id_source, id_target = id_target, properties = properties, label = label, serializer = serializer)

        logging.debug(f"GenericEdge ID: {id}")

    @staticmethod
    def source_type():
        return Node

    @staticmethod
    def target_type():
        return Node



class Adapter(errormanager.ErrorManager, metaclass = ABSTRACT):
    """Base class for implementing an adapter that consumes tabular data."""

    def __init__(self, raise_errors = True):
        """Allow to indicate which Element subclasses and which property fields
        are allowed to be exported by Biocypher.
        """
        self._nodes = []
        self._edges = []
        self.errors = []
        super().__init__(raise_errors)


    def nodes_append(self, node_s) -> None:
        """Append an Node (or each Node in a list of nodes) to the internal list of nodes."""
        if issubclass(type(node_s), Node):
            nodes = [node_s]
        else:
            nodes = node_s

        # logger.debug(f"Nodes: {nodes}.")
        for node in nodes:
            # logger.debug(f"\tAppend node {node}.")
            # Checking for duplicates in reconciliation, otherwise complexity too high.
            self._nodes.append(node.as_tuple())
            # return True

    def edges_append(self, edge_s) -> None:
        """Append an Edge (or each Edge in a list of edges) to the internal list of edges."""
        if issubclass(type(edge_s), Edge):
            edges = [edge_s]
        else:
            edges = edge_s

        # logger.debug(f"Edges: {edges}.")
        for edge in edges:
            # logger.debug(f"\tAppend edge {edge}.")
            # Checking for duplicates in reconciliation, otherwise complexity too high.
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

    @abstractmethod
    def run(self):
        raise NotImplementedError()

    def __call__(self):
        for local_nodes, local_edges in self.run():
            yield local_nodes, local_edges


class Declare(errormanager.ErrorManager):
    """
    Declarations of functions used to declare and instantiate object classes used by the Adapter for the mapping
    of the data frame.

    Args:
        module: The module in which to insert the types declared by the configuration.
    """

    def __init__(self,
                 module=types,
                 raise_errors = True,
                 ):
        super().__init__(raise_errors)
        self.module = module



    def make_node_class(self, name, properties={}, base=Node):
        """
        LabelMaker a node class with the given name and properties.

        Args:
            name: The name of the node class.
            properties (dict): The properties of the node class.
            base: The base class for the node class.

        Returns:
            The created node class.
        """
        # If type already exists, return it.
        if hasattr(self.module, name):
            cls = getattr(self.module, name)
            logger.debug(
                f"\t\tNode class `{name}` (prop: `{cls.fields()}`) already exists, I will not create another one.")
            for p in properties.values():
                if p not in cls.fields():
                    logger.warning(f"\t\t\tProperty `{p}` not found in declared fields for node class `{cls.__name__}`.")
            return cls

        def fields():
            return list(properties.values())

        attrs = {
            "__module__": self.module.__name__,
            "fields": staticmethod(fields),
        }
        t = types.new_class(name, (base,), {}, lambda ns: ns.update(attrs))
        logger.debug(f"\t\tDeclare Node class `{t.__name__}` (prop: `{properties}`).")
        setattr(self.module, t.__name__, t)
        return t

    def make_edge_class(self, name, source_t, target_t, properties={}, base=Edge):
        """
        LabelMaker an edge class with the given name, source type, target type, and properties.

        Args:
            name: The name of the edge class.
            source_t: The source type of the edge.
            target_t: The target type of the edge.
            properties (dict): The properties of the edge class.
            base: The base class for the edge class.

        Returns:
            The created edge class.
        """
        # If type already exists, check if the fields are the same.
        if hasattr(self.module, name):
            cls = getattr(self.module, name)
            cls_fields = cls.fields()

            # Compare the properties with the existing class fields
            if properties == cls_fields:
                logger.info(
                    f"\t\tEdge class `{name}` (prop: `{cls_fields}`) already exists with the same properties, I will not create another one.")
                return cls

            logger.warning(f"\t\tEdge class `{name}` already exists, but properties do not match.")
            # If properties do not match, we proceed to create a new class with the new properties.
            # FIXME: Would make much more sense to just append(?) new properties to existing class instead of creating new class.

        def fields():
            return properties

        def st():
            return source_t

        def tt():
            return [target_t]

        attrs = {
            "__module__": self.module.__name__,
            "fields": staticmethod(fields),
            "source_type": staticmethod(st),
            "target_type": staticmethod(tt),
        }
        t = types.new_class(name, (base,), {}, lambda ns: ns.update(attrs))
        logger.debug(f"\t\tDeclare Edge class `{t.__name__}` (prop: `{properties}`).")
        setattr(self.module, t.__name__, t)
        return t

    def make_transformer_class(self, transformer_type, multi_type_dictionary = None, branching_properties = None,
                               properties=None, columns=None, output_validator=None, label_maker = None, **kwargs):
        """
        LabelMaker a transformer class with the given parameters.

        Args:
            multi_type_dictionary: Dictionary of regex rules and corresponding types in case of cell value match.
            transformer_type: The class of the transformer.
            properties: The properties of the transformer.
            columns: The columns to be processed by the transformer.
            output_validator: validate.OutputValidator instance for transformer output validation.
            **kwargs: Additional keyword arguments.

        Returns:
            The created transformer class.

        Raises:
            TypeError: If the transformer type is not an existing transformer.
        """
        if hasattr(transformer, transformer_type):
            parent_t = getattr(transformer, transformer_type)
            kwargs.setdefault("subclass", parent_t)
            if not issubclass(parent_t, transformer.Transformer):
                self.error(f"Object `{transformer_type}` is not an existing transformer.", exception = exceptions.DeclarationError)
            logger.debug(f"\t\tDeclare Transformer class '{transformer_type}'.")
            return parent_t(properties_of=properties,
                            columns=columns,
                            output_validator=output_validator,
                            multi_type_dict = multi_type_dictionary,
                            branching_properties = branching_properties,
                            label_maker = label_maker,
                            raise_errors = self.raise_errors,
                            **kwargs)
        else:
            # logger.debug(dir(generators))
            self.error(f"Cannot find a transformer class with name `{transformer_type}`.", exception = exceptions.DeclarationError)


class All:
    """Gathers lists of subclasses of Element and their fields
    existing in a given module.

    Is generally used to label_maker an `all` variable in a module:
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
                logger.debug(f"Found `{asked.__name__}` class: `{m[c]}` (prop: `{m[c].fields()}`).")
                # t = m[c]
                # logger.debug(f"\t\t#### {t.mro()[:-3]}/{t.__name__} => {t.fields()}")
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
