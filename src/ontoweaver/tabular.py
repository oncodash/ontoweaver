import sys
import math
import types as pytypes
import logging
from typing import Optional
from collections.abc import Iterable
from enum import Enum, EnumMeta

import pandas as pd

from . import base
from . import types
from . import transformer


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class Enumerable(Enum, metaclass=MetaEnum):
    pass


class TypeAffixes(str, Enumerable):
    suffix = "suffix"
    prefix = "prefix"
    none = "none"


class PandasAdapter(base.Adapter):
    """Interface for extracting data from a Pandas DataFrame with a simple mapping configuration based on declared types.

    The general idea is that each row of the table is mapped to a source node,
    and some column values are mapped to an edge leading to another node.
    Some other columns may also be mapped to properties of either a node or an edge.

    The class expect a configuration formed by three objects:
        - the type of the source node mapped for each row.
        - a dictionary mapping each column name to the type of the edge (which contains the type of both the source and target node),
        - a dictionary mapping each (node or edge) type to another dictionary listing which column is extracted to which property.

    Note that, when using the `configure` mapping,
    types are created by default in the `ontoweaver.types` module,
    so that you may access the list of all declared types by using:
        - `ontoweaver.types.all.nodes()`,
        - `ontoweaver.types.all.node_fields()`,
        - `ontoweaver.types.all.edges()`,
        - `ontoweaver.types.all.edge_fields()`.
    """

    def __init__(self,
                 df: pd.DataFrame,
                 row_type: base.Node,
                 node_type_of: dict[str, base.Node],
                 edge_type_of: dict[str, base.Edge],
                 properties_of: dict[str, dict[str, str]],
                 transformers: dict[str, base.Transformer],
                 node_types: Optional[Iterable[base.Node]] = None,
                 node_fields: Optional[list[str]] = None,
                 edge_types: Optional[Iterable[base.Edge]] = None,
                 edge_fields: Optional[list[str]] = None,
                 skip_nan=True,
                 type_affix: Optional[TypeAffixes] = TypeAffixes.suffix,
                 type_affix_sep: Optional[str] = ":",
                 ):
        """
        Instantiate the adapter.

        :param pandas.Dataframe df: the table containing the input data.
        :param ontoweaver.base.Node row_type: the source node (or subject, depending on your vocabulary reference) type, mapped for each row.
        :param dict[str, base.Edge] node_type_of: a dictionary mapping each column (or field) name to the type of the node.
        :param dict[str, base.Edge] edge_type_of: a dictionary mapping each column (or field) name to the type of the edge.
        :param dict[base.Node, dict[str,str]] properties_of: a dictionary mapping each element (both node or edge) type to a dictionary listing which column is extracted to which property.
        :param Iterable[Node] node_types: Allowed Node subclasses.
        :param list[str] node_fields: Allowed property fields for the Node subclasses.
        :param Iterable[Edge] edge_types: Allowed Edge subclasses.
        :param list[str] edge_fields: Allowed property fields for the Edge subclasses.
        :param TypeAffixes type_affix: Where to add a type annotation to the labels (either TypeAffixes.prefix, TypeAffixes.suffix or TypeAffixes.none).
        :param str type_affix_sep: String use to separate a labe from the type annotation (WARNING: double-check that your BioCypher config does not use the same character as a separator).
        """
        super().__init__(node_types, node_fields, edge_types, edge_fields)

        logging.info("DataFrame info:")
        # logging.info(df.info()) # FIXME is displayed on stdout after all calls, use a stream with the buf arg here.
        logging.debug("Columns:")
        for c in df.columns:
            logging.debug(f"\t`{c}`")
        logging.info("\n" + str(df))
        self.df = df

        if not type_affix in TypeAffixes:
            raise ValueError(f"`type_affix`={type_affix} is not one of the allowed values ({[t for t in TypeAffixes]})")
        else:
            self.type_affix = type_affix

        self.type_affix_sep = type_affix_sep

        self.row_type = row_type
        self.node_type_of = node_type_of
        self.edge_type_of = edge_type_of
        self.properties_of = properties_of
        self.transformers = transformers
        # logging.debug(self.properties_of)
        self.skip_nan = skip_nan

        logging.debug(f"{self.row_type}")
        logging.debug(f"{self.node_type_of}")
        logging.debug(f"{self.edge_type_of}")
        logging.debug(f"{self.properties_of}")

    def source_type(self, row):
        """Accessor to the row type actually used by `run`.

        You may overlad this function if you want
        to make the row type dependant of some column value.

        By default, just return the default row type defined in the constructor,
        without taking the row values into account."""
        return self.row_type

    def source_id(self, i, row):
        # FIXME: allow to configure that within the YAML.
        # One may imagine something like: "{}_{}".format(self.source_type(row).__name__,i)
        return "{}".format(i)

    def properties(self, row, type):
        """Extract properties of each property category for the given node type. If no properties are found, return an empty dictionary."""

        properties = {}

        if type.__name__ in self.properties_of:
            for key, value in self.properties_of[type.__name__].items():
                if self.skip(row[key]):
                    continue
                else:
                    properties[value] = str(row[key]).replace("'",
                                                              "`")  # TODO refine string transformation for Neo4j import

        return properties

    def make_edge_and_target(self, source_id, target_id, c, row, transformer_type=None, log_depth=""):

        if transformer_type is not None:
            if issubclass(transformer_type[c], base.Transformer):
                target_t = transformer_type[c]
                property_t = transformer_type[c].target_type()
                self.nodes_append(self.make_node(target_t, id=target_id,
                                                 properties=self.properties(row, property_t)))

                edge_t = transformer_type[c]
                # TODO check if property_t should change for mapping edge properties in transformers
                self.edges_append(self.make_edge(
                    edge_t, id=None, id_source=source_id, id_target=target_id,
                    properties=self.properties(row, edge_t)))

        else:

            # target
            target_t = self.node_type_of[c]
            # target_id = f"{target_t.__name__}_{target_id}"
            target_id = f"{target_id}"
            # Append one (or several, if the target_t is a transformer) nodes.
            self.nodes_append(self.make_node(
                target_t, id=target_id,
                properties=self.properties(row, target_t)
            ))
            logging.debug(
                f"{log_depth}\t\tto  `{target_t.__name__}` `{target_id}` (prop: `{', `'.join(self.properties(row, target_t).keys())}`)")

            # relation
            edge_t = self.edge_type_of[c]
            self.edges_append(self.make_edge(
                edge_t, id=None, id_source=source_id, id_target=target_id,
                properties=self.properties(row, edge_t)
            ))
            logging.debug(
                f"{log_depth}\t\tvia `{edge_t.__name__}` (prop: `{', `'.join(self.properties(row, edge_t).keys())}`)")

        return target_id

    def make_id(self, entry_name, type):
        """ Create a unique id for the given cell consisting of the entry name and type,
        taking into account affix and separator configuration."""
        id = None

        if self.type_affix == TypeAffixes.prefix:
            id = f'{type}{self.type_affix_sep}{entry_name}'
        elif self.type_affix == TypeAffixes.suffix:
            id = f'{entry_name}{self.type_affix_sep}{type}'
        elif self.type_affix == TypeAffixes.none:
            id = f'{entry_name}'

        if id:
            logging.debug(f"\tID created for cell value `{entry_name}` of type: `{type}`: `{id}`")
            return id
        else:
            raise ValueError(f"Failed to create ID for cell value: `{entry_name}` of type: `{type}`")

    def split_transformer(self, entry_name, transformer):
        """ Split the passed entry name into its components and add affix type according to defined settings.
        Concatenate result into single sequence that will be transformed into individual nodes in base.Transformer. """

        separator = transformer.separator
        items = entry_name.split(separator)
        processed_items = []
        for item in items:
            processed_items.append(self.make_id(item, transformer.target_type().__name__))
        return separator.join(processed_items)

    def run(self):  # populates list of nodes and passes it to Biocypher
        """Actually run the configured extraction.

        If passed, the user-defined type_affix and type_affix_sep variables may override the default configured at instantiation.
        """
        # FIXME: all the raised exceptions here should be specialized and handled in the executable.

        # For all rows in the table.
        for i, row in self.df.iterrows():
            row_type = self.source_type(row)
            logging.debug(f"\tExtracting row {i} of type `{row_type.__name__}`...")
            if self.allows(row_type):
                source_id = self.source_id(self.make_id(i, row_type.__name__), row)
                self.nodes_append(self.make_node(
                    row_type, id=source_id,
                    properties=self.properties(row, row_type))
                )
            else:
                logging.error(f"\tRow type `{row_type.__name__}` not allowed.")

            for c in self.transformers.keys():
                if self.skip(row[c]):
                    continue
                else:
                    self.transformers[c].__call__(source_id=source_id, row=row)

            # For column names.
            for c in self.node_type_of:
                logging.debug(f"\tMapping column `{c}`...")
                if c not in row:
                    raise ValueError(f"Column `{c}` not found in input data.")
                target_id = self.make_id(row[c], self.node_type_of[c].__name__)
                if self.skip(target_id):
                    logging.debug(f"\t\tSkip `{target_id}`")
                    continue

                if self.allows(self.node_type_of[c]):
                    # If the edge is from the row type (i.e. the "source/subject")
                    # then just create it using the source_id.
                    if any(issubclass(row_type, t.source_type()) for t in self.edge_type_of.values()):
                        assert (any(issubclass(row_type, t.source_type()) for t in self.edge_type_of.values()))
                        self.make_edge_and_target(source_id, target_id, c, row)

                    else:  # The edge is from a random column to another (i.e. "from_subject").
                        # Try to handle this column first.
                        subject_type = self.node_type_of[c]
                        logging.debug(f"\t\tfrom `{subject_type.__name__}`")
                        # First, find the column for which
                        # the corresponding target type is defined.
                        matching_columns = []
                        for col_name, col_type in self.node_type_of.items():
                            target_type = col_type
                            if col_name != c and target_type == subject_type:
                                matching_columns.append(col_name)
                        # logging.debug(f"\t\tMatching columns: `{matching_columns}`")

                        if len(matching_columns) == 0:
                            column_types = {k: self.node_type_of[k].__name__ for k in self.node_type_of if k != c}
                            raise ValueError(
                                f"No column providing the type `{subject_type.__name__}` in `{column_types}`")

                        elif len(matching_columns) > 1:
                            msg = ", ".join("`" + mc + "`" for mc in matching_columns)
                            raise ValueError(
                                f"I cannot handle cases when several columns provide the same subject type. Offending columns: {msg}")

                        col_name = matching_columns[0]
                        if self.edge_type_of[col_name].source_type() != row_type:
                            raise ValueError(
                                f"Cannot handle detached columns without a primary link to the default row subject")

                        # We now have a valid column.
                        # Jump to creating the referred subject from the pointed column.
                        other_id = self.make_edge_and_target(source_id, self.make_id(row[col_name], self.node_type_of[
                            col_name].__name__), col_name, row, log_depth="\t")
                        # Then create the additional edge,
                        # this time from the previously created target_id
                        # (i.e. the column's subject).
                        self.make_edge_and_target(other_id, target_id, c, row)

                else:
                    logging.debug(f"\t\tColumn `{c}` with edge of type `{self.edge_type_of[c]}` not allowed.")

        self.end()

    def end(self):
        pass

    # FIXME see how to declare another constructor taking config and module instead of the mapping.


def extract_all(df: pd.DataFrame, config: dict, module=types, affix="suffix", separator=":"):
    """Proxy function for extracting from a table all nodes, edges and properties
    that are defined in a PandasAdapter configuration. """
    mapping = PandasAdapter.configure(config, module)

    allowed_node_types = types.all.nodes()
    logging.debug(f"allowed_node_types: {allowed_node_types}")

    allowed_node_fields = types.all.node_fields()
    logging.debug(f"allowed_node_fields: {allowed_node_fields}")

    allowed_edge_types = types.all.edges()
    logging.debug(f"allowed_edge_types: {allowed_edge_types}")

    allowed_edge_fields = types.all.edge_fields()
    logging.debug(f"allowed_edge_fields: {allowed_edge_fields}")

    # Using empty list or no argument would also select everything,
    # but explicit is better than implicit.
    adapter = PandasAdapter(
        df,
        *mapping,
        allowed_node_types,
        allowed_node_fields,
        allowed_edge_types,
        allowed_edge_fields,
        type_affix=affix,
        type_affix_sep=separator

    )

    adapter.run()

    return adapter


class Declare:

    def __init__(self,
                 module=types,
                 ):

        self.module = module

    def make_node_class(self, name, properties={}, base=base.Node):
        # If type already exists, return it.
        if hasattr(self.module, name):
            cls = getattr(self.module, name)
            logging.debug(
                f"\tNode class `{name}` (prop: `{cls.fields()}`) already exists, I will not create another one.")
            for p in properties.values():
                if p not in cls.fields():
                    logging.warning(f"\t\tProperty `{p}` not found in fields.")
            return cls

        def fields():
            return list(properties.values())

        attrs = {
            "__module__": self.module.__name__,
            "fields": staticmethod(fields),
        }
        t = pytypes.new_class(name, (base,), {}, lambda ns: ns.update(attrs))
        logging.debug(f"Declare Node class `{t}` (prop: `{properties}`).")
        setattr(self.module, t.__name__, t)
        return t

    def make_edge_class(self, name, source_t, target_t, properties={}, base=base.Edge, ):
        # If type already exists, return it.
        if hasattr(self.module, name):
            cls = getattr(self.module, name)
            logging.info(
                f"Edge class `{name}` (prop: `{cls.fields()}`) already exists, I will not create another one.")
            for p in properties:
                if p not in cls.fields():
                    logging.warning(f"\t\tProperty `{p}` not found in fields.")

            tt_list = cls.target_type()

            tt_list.append(target_t)

            def tt():
                return tt_list

            cls.target_type = staticmethod(tt)

            # TODO allow multiple source types for edge

            return cls

        def fields():
            return list(properties.values())

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
        t = pytypes.new_class(name, (base,), {}, lambda ns: ns.update(attrs))
        logging.debug(f"Declare Edge class `{t}` (prop: `{properties}`).")
        setattr(self.module, t.__name__, t)
        return t

    def make_transformer_class(self, transformer_type, node_type, properties, edge=None, columns=None, **kwargs):
        if hasattr(transformer, transformer_type):
            parent_t = getattr(transformer, transformer_type)
            kwargs.setdefault("subclass", parent_t)
            if not issubclass(parent_t, base.Transformer):
                raise TypeError(f"Object `{transformer_type}` is not an existing transformer.")
            else:
                logging.debug(f"Declare transformer type '{transformer_type}' for node type '{node_type}'")
                return parent_t(target=node_type, properties_of=properties, edge=edge, columns=columns,
                                        **kwargs)
        else:
            # logging.debug(dir(generators))
            raise TypeError(f"Cannot find a transformer of name `{transformer_type}`.")




class YamlParser(Declare):
    """Parse a table extraction configuration
    and returns the three objects needed to configure a PandasAdapter.

    The config is a dictionary containing only strings,
    as converted from the following YAML desscription:

    .. code-block:: yaml

        subject: <MY_SUBJECT_TYPE>
        columns:
            <MY_COLUMN_NAME>:
                to_object: <MY_OBJECT_TYPE>
                via_relation: <MY_RELATION_TYPE>
           <MY_OTHER_COLUMN>:
                to_properties:
                    <MY_PROPERTY>:
                        - <MY_OBJECTS_TYPE>

    This maps the table row to a MY_SUBJECT_TYPE node type,
    adding an edge of type MY_RELATION_TYPE,
    between the MY_SUBJECT_TYPE node and another MY_OBJECT_TYPE node.
    The data in MY_OTHER_COLUMN is mapped to the MY_PROPERTY property
    of the MY_OBJECT_TYPE node.
    Note that `to_properties` may effectively map to an edge type or several
    types.

    In order to allow the user to write mappings configurations using their preferred vocabulary, the following keywords are interchangeable:
        - subject = row = entry = line,
        - columns = fields,
        - to_target = to_object = to_node
        - via_edge = via_relation = via_predicate.

    :param dict config: a configuration dictionary.
    :param module: the module in which to insert the types declared by the configuration.
    :return tuple: source_t, node_type_of, edge_type_of, properties_of, as needed by PandasAdapter.
    """

    def __init__(self,
                 config: dict,
                 module=types,
                 ):

        super().__init__(module)
        self.config = config

        logging.debug(f"Classes created in module '{self.module}'")

    def get_not(self, keys, pconfig=None):
        """Get the first dictionary (key,item) not matching any of the passed keys."""
        res = {}
        if not pconfig:
            pconfig = self.config
        for k in pconfig:
            if k not in keys:
                res[k] = pconfig[k]
        return res

    def get(self, keys, pconfig=None):
        """Get a dictionary items matching either of the passed keys."""
        if not pconfig:
            pconfig = self.config
        for k in keys:
            if k in pconfig:
                return pconfig[k]
        return None

    def __call__(self):

        properties_of = {}
        transformers = []

        # Various keys are allowed in the config,
        # to allow the user to use their favorite ontology vocabulary.
        # TODO: Catch wrongly used keywords and output errors.
        k_row = ["row", "entry", "line", "subject", "source"]
        k_subject_type = ["to_subject"]
        k_columns = ["columns", "fields"]
        k_target = ["to_target", "to_object", "to_node"]
        k_subject = ["from_subject", "from_source"]
        k_edge = ["via_edge", "via_relation", "via_predicate"]
        k_properties = ["to_properties", "to_property"]
        k_prop_to_object = ["for_objects"]
        k_transformer = ["transformers"]
        k_split = ["split"]

        transformers_list = self.get(k_transformer)

        # First, parse property mappings.
        # Because we must declare types with every member's fields already ready.

        # TODO if there is a property name with multiple porperty columns, make a list

        for transformer_types in transformers_list:
            for transformer_type, field_dict in transformer_types.items():
                # Check if dictionary has a property key, and map the declared properties for each ontology type.
                if any(field in field_dict.keys() for field in k_properties):
                    object_types = self.get(k_prop_to_object, pconfig=field_dict)
                    property_names = self.get(k_properties, pconfig=field_dict)
                    column_names = self.get(k_columns, pconfig=field_dict)
                    for object_type in object_types:
                        properties_of.setdefault(object_type, {})
                        for column_name in column_names:
                            for property_name in property_names:
                                properties_of[object_type].setdefault(column_name, property_name)
                        logging.debug(f"\t\t\t\tDeclare property mapping for `{object_type}`: {properties_of[object_type]}")



        subject_dict = self.get(k_row)
        subject_transformer_class = list(subject_dict.keys())[0]
        subject_type = self.get(k_subject_type, subject_dict[subject_transformer_class])
        subject_kwargs = self.get_not(k_subject_type + k_columns, subject_dict[subject_transformer_class])
        subject_columns = self.get(k_columns, subject_dict[subject_transformer_class])
        logging.debug(f"Declare subject type '{subject_type}', subject transformer '{subject_transformer_class}', subject kwargs '{subject_kwargs}', subject columns '{subject_columns}")

        # import Transformer / for e in transformer_dict if issubclass e base.trasn and e_name == subj trasn
        source_t = self.make_node_class(subject_type, properties_of.get(subject_type, {}))
        subject_transformer = self.make_transformer_class(columns=subject_columns, transformer_type=subject_transformer_class, node_type=source_t, properties=properties_of.get(subject_type, {}), **subject_kwargs)



        # Then, declare types.
        for transformer_types in transformers_list:
            for transformer_type, field_dict in transformer_types.items():
                # Only take into consideration fields that are not property mappings.
                if any(field in field_dict.keys() for field in k_properties):
                    if any(field in field_dict.keys() for field in k_target):
                        prop = self.get(k_properties, field_dict)
                        target = self.get(k_target, field_dict)
                        logging.error(f"ERROR in transformer '{transformer_type}': one cannot declare a mapping to both properties '{prop}' and object type '{target}'.")
                    continue
                else:
                    columns = self.get(k_columns, pconfig=field_dict)
                    target = self.get(k_target, pconfig=field_dict)
                    subject = self.get(k_subject, pconfig=field_dict)
                    edge = self.get(k_edge, pconfig=field_dict)
                    gen_data = self.get_not(k_target + k_edge + k_columns, pconfig=field_dict)

                    if target and edge:
                        target_t = self.make_node_class(target, properties_of.get(target, {}))
                        logging.debug(f"\t\t\t\tDeclare target for `{target}`: {target_t}")
                        if subject:
                            subject_t = self.make_node_class(subject, properties_of.get(subject, {}))
                            edge_t = self.make_edge_class(edge, subject_t, target_t, properties_of.get(edge, {}))
                        else:
                            edge_t = self.make_edge_class(edge, source_t, target_t, properties_of.get(edge, {}))
                        # FIXME: Instantiate a specific transformer instead of base.Transformer
                        transformers.append(self.make_transformer_class(transformer_type=transformer_type, node_type=target_t, properties=properties_of.get(target, {}), edge=edge_t, columns=columns, **gen_data))
                        logging.debug(f"\t\t\t\tDeclare mapping `{columns}` => `{edge_t.__name__}`")
                    elif (target and not edge) or (edge and not target):
                        logging.error(f"\t\t\t\tCannot declare the mapping  `{columns}` => `{edge}` (target: `{target}`)")


        logging.debug(f"source class: {source_t}")
        logging.debug(f"properties_of: {properties_of}")
        logging.debug(f"transformers: {transformers}")
        return subject_transformer, transformers
