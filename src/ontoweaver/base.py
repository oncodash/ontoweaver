import logging
import re
from collections.abc import Iterable, Generator
from abc import ABCMeta as ABSTRACT, ABCMeta, abstractmethod
from abc import abstractmethod as abstract
from typing import TypeAlias
from typing import Optional
import pandas as pd
import pandera as pa
from jinja2.compiler import has_safe_repr

from . import errormanager
from . import validate
from . import serialize
from . import exceptions
from . import make_value
from .validate import SkipValidator

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
        return f"<['{self.label}':'{self.id}'/{self.properties}]>"

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
        else:
            st = f"’{self.source_type()}’"
        if self.target_type() == Node:
            tt = "."
        else:
            tt = f"’{self.target_type()}’"

        return f"<[{st}:'{self.id_source}']--('{self.label}':'{self.id}'/{self.properties})-->[{tt}:'{self.id_target}']>"

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

    @staticmethod
    def source_type():
        return Node

    @staticmethod
    def target_type():
        return Node


class Adapter(errormanager.ErrorManager, metaclass = ABSTRACT):
    """Base class for implementing a canonical Biocypher adapter."""

    def __init__(self, raise_errors = True
    ):
        """Allow to indicate which Element subclasses and which property fields
        are allowed to be exported by Biocypher.

        :param Iterable[Node] node_types: Allowed Node subclasses.
        :param Iterable[Edge] edge_types: Allowed Edge subclasses.
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


class Transformer(errormanager.ErrorManager):
    """"Class used to manipulate cell values and return them in the correct format."""""

    def __init__(self, properties_of, value_maker = None, label_maker = None, branching_properties = None, columns = None,
                 output_validator: validate.OutputValidator() = None, multi_type_dict = None, raise_errors = True, **kwargs):
        """
        Instantiate transformers.

        :param properties_of: the properties of each node type.
        :param value_maker: the ValueMaker object used for the logic of cell value selection for each transformer. Default is None.
        :param label_maker: the LabelMaker object used for handling the creation of the output of the transformer. Default is None.
        :param branching_properties: in case of branching on cell values, the dictionary holds the properties for each branch.
        :param columns: the columns to use in the mapping.
        :param output_validator: the OutputValidator object used for validating transformer output. Default is None.
        :param multi_type_dict: the dictionary holding regex patterns for node and edge type branching based on cell values.
        :param raise_errors: whether to raise errors or not. Default is True.
        each transformer is instantiated with a default OutputValidator object, and additional user-defined rules if needed in
        the tabular module.

        """
        super().__init__(raise_errors)

        self.properties_of = properties_of
        self.value_maker = value_maker
        self.label_maker = label_maker
        self.branching_properties = branching_properties
        self.columns = columns
        self.output_validator = output_validator
        if not self.output_validator:
            self.output_validator = validate.OutputValidator(validate.default_validation_rules, raise_errors = raise_errors)
        self.parameters = kwargs
        self.multi_type_dict = multi_type_dict
        self.final_type = None # The final type is to be passed by the label maker class based on the YAML mapping. That
                               # is why here it is None by default
        self.kwargs = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_transformer(self):
        return self

    @abstract
    def __call__(self, row, i):
        raise NotImplementedError

    #FIXME: The functions below are never implemented.
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

    def __repr__(self):

        representation = ""

        if hasattr(self, "from_subject"):
            from_subject = self.from_subject
        else:
            from_subject = "."

        target_name = ""
        edge_name = ""

        if hasattr(self, "multi_type_dict") and self.multi_type_dict is not None:
            for key, value in self.multi_type_dict.items():
                if value['to_object'] and value['via_relation']:
                    target_name = value['to_object']
                    edge_name = value['via_relation']
                elif value['to_object'] and not value['via_relation']:
                    target_name = value['to_object']
                    edge_name = "."


                if self.properties_of:
                    # The transformer is not a branching transformer, and has only one set of properties.
                    props = self.properties_of
                elif self.branching_properties and self.branching_properties.get(value['to_object'], None):
                    # The transformer is a branching transformer, and has multiple sets of properties. We extract the ones for the current type.
                    props = self.branching_properties.get(value['to_object'])
                else:
                    # The transformer has no properties for the type.
                    props = "{}"


                params = ""
                parameters = {k:v for k,v in self.parameters.items() if k not in ['subclass', 'from_subject', "match"]}
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

                for c in columns:
                    if type(c) != str:
                        self.error(f"Column `{c}` is not a string, did you mistype a leading colon?", exception=exceptions.ParsingError)

                representation += (f"<Transformer:{type(self).__name__}({params}) {','.join(columns)}{link}>")

        else:
            #The transformer is a property transformer. We add the property name and value in the tabular.properties() function.
            representation += (f"<Transformer:{type(self).__name__}() {','.join(self.columns) if self.columns else ''} =>")

        return representation

    def validate(self, res):
        """
        Validate the output of the transformer, using the output_validator. of the transformer instance.
        """
        try:
            if isinstance(self.output_validator, validate.SimpleOutputValidator) or isinstance(self.output_validator, SkipValidator):
                # The SimpleOutputValidator and SkipValidator do not use the Pandera package, and the value is therefore not
                # required to be in a DataFrame format. Voiding the creation of a DataFrame here saves computational time for
                # large datasets.
                if self.output_validator(res):
                    return True
                else:
                    return False
            else:
                if self.output_validator(pd.DataFrame([res], columns=["cell_value"])):
                    return True
                else:
                    return False
        except pa.errors.SchemaErrors as error:
            msg = f"Transformer {self.__repr__()} did not produce valid data {error}."
            self.error(msg, exception = exceptions.DataValidationError)

    def create(self, returned_value, row):
        """
        Create the output of the transformer, using the label_maker of the transformer instance.

        Returns:
            Extracted cell value (can be node ID, property value, edge ID), edge type and target node type.
        """
        result_object = self.label_maker(self.validate, returned_value, self.multi_type_dict, self.branching_properties, row)
        if result_object.target_node_type:
            self.target_type = result_object.target_node_type.__name__
        if result_object.target_element_properties is not None:
            self.properties_of = result_object.target_element_properties
        self.final_type = result_object.final_type
        return result_object.extracted_cell_value, result_object.edge_type, result_object.target_node_type


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
