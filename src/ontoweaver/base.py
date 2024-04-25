import logging
from collections.abc import Iterable, Generator
from abc import ABCMeta as ABSTRACT
from abc import abstractmethod as abstract
from typing import TypeAlias
from typing import Optional

from enum import Enum

class Element(metaclass = ABSTRACT):
    """Base class for either Node or Edge.

    Manages allowed properties mechanics."""

    def __init__(self,
        id        : Optional[str] = None,
        properties: Optional[dict[str,str]] = {},
        allowed   : Optional[list[str]] = None,
        label     : Optional[str] = None,
    ):
        """Instantiate an element.

        :param str id: Unique identifier of the element. If id == None, is then set to the empty string.
        :param dict[str,str] properties: All available properties for this instance.
        :param list[str] allowed: Allowed property names (the ones that will be exported to the knowledge graph by Biocypher). If allowed == None, all properties are allowed.
        :param str label: The label of the element. If label = None, the lower-case version of the class name is used as a label.
        """
        if not id:
            self._id = ''
        else:
            self._id = str(id)

        # Use the setter to get sanity checks.
        self.properties = properties

        # Use the setter to get sanity checks.
        if not allowed:
            self.allowed = self.available()
        else:
            self.allowed = allowed

        if not label:
            self._label = self.__class__.__name__.lower()
        else:
            self._label = str(label)

    @staticmethod
    @abstract
    def fields() -> list[str]:
        """List of property fields provided by the (sub)class."""
        raise NotImplementedError

    def available(self) -> list[str]:
        """Enumerate all fields declared by the hierarchy of classes above the current instance."""

        # Loop over parent classes, except for the last ones,
        # which are `Node`/`Edge`, `Element` and `object`.
        for Parent in type(self).mro()[:-3]:
            # Call the static method of this class,
            # and yield its content.
            for field in Parent.fields():
                # logging.debug(f"\t\t {type(self).mro()[:-3]}/{Parent.__name__} => {field}")
                yield field

    @abstract
    def as_tuple(self):
        """Convert the element class into Biocypher's expected tuple.

        Filter out properties along the way.
        """
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
        # logging.debug(f"Properties of `{type(self).__name__}`: {list(properties.keys())}, available: {list(self.available())}")
        for p in properties:
            if p not in self.available():
                logging.error(f"\t\tProperty `{p}` should be available for type `{type(self).__name__}`, available ones: `{list(self.available())}`")
                assert(p in self.available())
        self._properties = properties

    @property
    def allowed(self) -> list[str]:
        return self._allowed

    @allowed.setter
    def allowed(self, allowed_properties: list[str]):
        assert(allowed_properties is not None)
        # May be any name, even for another class,
        # so there is not much to check.
        self._allowed = allowed_properties

    def allowed_properties(self):
        """Filter out properties that are not allowed."""
        assert(self._properties is not None)
        assert(self._allowed is not None)
        return {k:self._properties[k] for k in self._properties if k in self._allowed}


class Node(Element):
    """Base class for any Node."""

    def __init__(self,
        id        : Optional[str] = None,
        properties: Optional[dict[str,str]] = {},
        allowed   : Optional[list[str]] = None, # Passed by Adapter.
        label     : Optional[str] = None, # Set from subclass name.
    ):
        """Instantiate a Node.

        :param str id: Unique identifier of the node. If id == None, is then set to the empty string.
        :param dict[str,str] properties: All available properties for this instance.
        :param list[str] allowed: Allowed property names (the ones that will be exported to the knowledge graph by Biocypher). If allowed == None, all properties are allowed. Note: when instantiating through an Adapter.make, you don't need to pass this argument.
        :param str label: The label of the node. If label = None, the lower-case version of the class name is used as a label.
        """
        super().__init__(id, properties, allowed, label)

    Tuple: TypeAlias = tuple[str,str,dict[str,str]]
    def as_tuple(self) -> Tuple:
        """Export the Node as a Biocypher tuple."""
        return (
            self._id,
            self._label,
            # Only keep properties that are allowed.
            self.allowed_properties()
        )


class Edge(Element):
    """Base class for any Edge."""

    def __init__(self,
        id        : Optional[str] = None,
        id_source : Optional[str] = None,
        id_target : Optional[str] = None,
        properties: Optional[dict[str,str]] = {},
        allowed   : Optional[list[str]] = None, # Passed by Adapter.
        label     : Optional[str] = None, # Set from subclass name.
    ):
        """Instantiate an Edge.

        :param str id: Unique identifier of the edge. If id == None, is then set to the empty string.
        :param str id_source: Unique identifier of the source Node. If None, is then set to the empty string.
        :param str id_target: Unique identifier of the target Node. If None, is then set to the empty string.
        :param dict[str,str] properties: All available properties for this instance.
        :param list[str] allowed: Allowed property names (the ones that will be exported to the knowledge graph by Biocypher). If allowed == None, all properties are allowed. Note: when instantiating through an Adapter.make, you don't need to pass this argument.
        :param str label: The label of the node. If label = None, the lower-case version of the class name is used as a label.
        """
        super().__init__(id, properties, allowed, label)
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
        return self._id_source

    Tuple: TypeAlias = tuple[str,str,str,dict[str,str]]
    def as_tuple(self) -> Tuple:
        """Export the Edge as a Biocypher tuple."""
        return (
            self._id,
            self._id_source,
            self._id_target,
            self._label,
            # Only keep properties that are allowed.
            self.allowed_properties()
        )

#TODO check if function below needed
def node_generator(edge_gen_cls):
    """Wrapper signaling that the function returns list of nodes."""
    class Nodes(Transformer):
        cls = edge_gen_cls

        @staticmethod
        def mro():
            """Substitutes the hierarchy of parent classes for the one of the handled class."""
            return edge_gen_cls.mro()
    return Nodes


class Adapter(metaclass = ABSTRACT):
    """Base class for implementing a canonical Biocypher adapter."""

    def __init__(self,
        node_types : Iterable[Node],
        node_fields: list[str],
        edge_types : Iterable[Edge],
        edge_fields: list[str],
    ):
        """Allow to indicate which Element subclasses and which property fields
        are allowed to be exported by Biocypher.

        :param Iterable[Node] node_types: Allowed Node subclasses.
        :param list[str] node_fields: Allowed property fields for the Node subclasses.
        :param Iterable[Edge] edge_types: Allowed Edge subclasses.
        :param list[str] edge_fields: Allowed property fields for the Edge subclasses.
        """
        if not node_types or not edge_types:
            raise ValueError("You must allow at least one node type and one edge type.")

        self._node_types  = node_types
        self._node_fields = node_fields
        self._edge_types  = edge_types
        self._edge_fields = edge_fields
        self._nodes = []
        self._edges = []

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
                self._nodes.append(node)
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
                self._edges.append(edge)
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

    @property
    def node_types(self) -> Iterable[Node]:
        return self._node_types

    @property
    def node_fields(self) -> list[str]:
        return self._node_fields

    @property
    def edge_types(self) -> Iterable[Edge]:
        return self._edge_types

    @property
    def edge_fields(self) -> list[str]:
        return self._edge_fields

    def allows(self, elem_type: Element) -> bool:
        """Returns True if the given class is in the allowed list.

        Example:
        .. code-block:: python

            if self.allows( MyNode ):
                pass

        :param Element elem_type: The given class.
        :returns bool: True if a Node is in node_types or an Edge in edge_types.
        """
        # FIXME: double-check if we want strict class equality or issubclass.
        def allowed_by(elem,types):
            return any(issubclass(e, elem) or e == elem for e in types)

        # For Nodes: just test.
        if issubclass(elem_type, Node):
            return allowed_by(elem_type, self._node_types)

        # For Edges: double-check target and source Node types as well.
        elif issubclass(elem_type, Edge):
            if allowed_by(elem_type, self._edge_types):
                # logging.debug(f"\tEdge type `{elem_type.__name__}` is allowed")
                if not allowed_by(elem_type.source_type(), self._node_types):
                    logging.warning(f"\t\tWARNING: you allowed the `{elem_type.__name__}` edge type, but not its source (`{elem_type.source_type().__name__}`) node type.")
                    return False
                elif not allowed_by(elem_type.target_type(), self._node_types):
                    logging.warning(f"\t\tWARNING: you allowed the `{elem_type.__name__}` edge type, but not its target (`{elem_type.target_type().__name__}`) node type.")
                    return False
                else:
                    # logging.debug(f"\tBoth source type `{elem_type.source_type().__name__}` and target type `{elem_type.target_type().__name__}` are allowed.")
                    return True
            else:
                # logging.debug(f"\tEdge type `{elem_type.__name__}` is not allowed")
                return False

        # For EdgeGenerators: recursive call to edge. 
        elif issubclass(elem_type, Transformer):
            return self.allows(elem_type.edge_type())
        else:
            raise TypeError("`elem_type` should be of type `Element`")

    def make_node(self, *args, **kwargs) -> tuple:
        """Make a Biocypher tuple of the given class.

        Automatically filter property fields based on what was passed to the Adapter.

        WARNING: for the sake of clarity, only named arguments are allowed after the Element class.

        Example:
        .. code-block:: python

            yield self.make( MyNode, id=my_id, properties={"my_field": my_value} )

        :param Node <unnamed>: Class of the node to create.
        :param **kwargs: Named arguments to pass to instantiate the given class.
        :returns tuple: A Biocypher tuple representing the node.
        """
        assert(len(args) == 1)
        this = args[0]
        # logging.debug(f"##### {this}")
        if issubclass(this, Node):
            # logging.debug(f"\tMake node of type `{this}`.")
            yield this(*(args[1:]), allowed=self.node_fields, **kwargs).as_tuple()
        elif issubclass(this, Transformer):
            gen = this(*(args[1:]), allowed=self.node_fields, **kwargs)
            for n in gen.nodes():
                # logging.debug(f"\t\tGenerate Node `{n}`.")
                yield n.as_tuple()
        else:
            raise TypeError(f"First argument `{this}` should be a subclass of `{Node}`")


    def make_edge(self, *args, **kwargs) -> tuple:
        """Make a Biocypher tuple of the given class.

        Automatically filter property fields based on what was passed to the Adapter.

        WARNING: for the sake of clarity, only named arguments are allowed after the Element class.

        :param Edge <unnamed>: Class of the edge to create.
        :param **kwargs: Named arguments to pass to instantiate the given class.
        :returns tuple: A Biocypher tuple representing the edge.
        """
        assert(len(args) == 1)
        this = args[0]
        if issubclass(this, Edge):
            # logging.debug(f"\tMake edge of type `{this}`.")
            yield this(*(args[1:]), allowed=self.edge_fields, **kwargs).as_tuple()
        elif issubclass(this, Transformer):
            gen = this(*(args[1:]), allowed=self.edge_fields, **kwargs)
            for e in gen.edges():
                logging.debug(f"\t\tGenerate Edge `{e}`.")
                yield e.as_tuple()
        else:
            raise TypeError(f"First argument `{this}` should be a subclass of `Edge`")


class Transformer():
    def __init__(self,
                 id: Optional[str] = None,
                 id_source: Optional[str] = None,
                 id_target: Optional[str] = None,
                 properties: Optional[dict[str, str]] = {},
                 allowed: Optional[list[str]] = None,  # Passed by Adapter.
                 label: Optional[str] = None,  # Set from subclass name.
                 columns=None
                 ):

        self.id = id
        self.id_source = id_source
        self.id_target = id_target
        self.properties = properties
        self.allowed = allowed
        self.label = label
        self.columns = columns

    def __call__(self, row, col_name_cell_value=dict, **kwargs):

        if isinstance(self.columns, list):
            raise NotImplementedError
        else:
            raise None

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
    def separator():
        raise NotImplementedError

    @staticmethod
    @abstract
    def target_type():
       raise NotImplementedError

    @classmethod
    def source_type(cls):
       return cls.edge_type().source_type()

    def make_node(self, id):
        #we beed to know the node type as well as the edge type, when generating transformers we need to ask user to specify node types
        node_t = self.target_type()
        return node_t(id = id,
            properties = self.properties, allowed = self.allowed, label = self.label)


    def make_edge(self, id_target):
        edge_t = self.edge_type()
        return edge_t(id = self.id, id_source = self.id_source,
            id_target = id_target,
            properties = self.properties, allowed = self.allowed, label = self.label)




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








