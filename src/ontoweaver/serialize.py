""" Classes for information fusion, handling unique ID creation.
"""
from abc import ABCMeta as ABSTRACT, ABCMeta, abstractmethod

import logging

from . import base
from . import exceptions
from . import make_labels

logger = logging.getLogger("ontoweaver")

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

    class IDWesternNameInitials(Serializer):
        def __call__(self, node):
            last,first = node.id.split(", ")
            firsts = first.split()
            result = f"{last},"
            for name in firsts:
                result += f" {name[0]}."
            return result

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


class PerType(Serializer):
    """Serialize elements by calling different serializers for different types.
    """
    def __init__(self, type_to_serializer = {"*": ID()}):
        self.type_to_serializer = type_to_serializer

    def __repr__(self):
        return "PerType{{{self.type_to_serializer}}}"

    def __call__(self, elem):
        for cls,serializer in self.type_to_serializer.items():
            # logger.debug(f"Serialize `{elem.as_tuple()}` of type `{type(elem).__name__}`")
            if elem.label == cls:
                # logger.debug(f"│ with serializer `{serializer}`")
                res = serializer(elem)
                # logger.debug(f"└ as `{res}`")
                return res
        if "*" not in self.type_to_serializer.keys():
            raise exceptions.DeclarationError(f"The type of {elem} did not match any key in `SerializePerType`, and you did not indicate a default serialization with a wildcard, add something like `'*': ID()` to your `type_to_serializer` argument.")
        # logger.debug(f"│ with serializer `{serializer}`")
        res = self.type_to_serializer['*'](elem)
        # logger.debug(f"└ as `{res}`")
        return res


class FromTransformer(Serializer):
    def make_transformer(self, transformer_t, fields, **kwargs):
        return transformer_t(
            properties_of=None,
            label_maker = make_labels.SimpleLabelMaker(),
            branching_properties = None,
            columns = fields,
            output_validator = None,
            multi_type_dict = None,
            raise_errors = True,
            **kwargs
        )

    def __init__(self,
            transformer_t,
            fields,
            **kwargs
        ):
            self.transform = self.make_transformer(transformer_t, fields, **kwargs)

    def __call__(self, elem):
        if issubclass(type(elem), base.Node):
            keys = ["id", "label", "properties"]
        elif issubclass(type(elem), base.Edge):
            keys = ["id", "label", "properties" "id_source", "id_target"]
        else:
            assert issubclass(type(elem), base.Node) or issubclass(type(elem), base.Edge)

        # Put the element members in a row dict.
        row = {}
        for k in keys:
            row[k] = getattr(elem, k)

        # Process the row with the transformer,
        # concatenates the resulting strings.
        serialized = ""
        for value, edge_type, node_type, reverse_edge in self.transform(row,0):
            serialized += value

        assert serialized
        return serialized

