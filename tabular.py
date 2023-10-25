import sys
import math
import types as pytypes
import logging
from typing import Optional
from collections.abc import Iterable

import pandas as pd

from . import base
from . import types
from . import generators


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
        type_of: dict[str, base.Edge],
        properties_of: dict[str, dict[str,str]],
        node_types : Optional[Iterable[base.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[base.Edge]] = None,
        edge_fields: Optional[list[str]] = None,
        skip_nan = True
    ):
        """
        Instantiate the adapter.

        :param pandas.Dataframe df: the table containing the input data.
        :param ontoweaver.base.Node row_type: the source node (or subject, depending on your vocabulary reference) type, mapped for each row.
        :param dict[str, base.Edge] type_of: a dictionary mapping each column (or field) name to the type of the edge (or relation, predicate).
        :param dict[base.Node, dict[str,str]] properties_of: a dictionary mapping each element (both node or edge) type to a dictionary listing which column is extracted to which property.
        :param Iterable[Node] node_types: Allowed Node subclasses.
        :param list[str] node_fields: Allowed property fields for the Node subclasses.
        :param Iterable[Edge] edge_types: Allowed Edge subclasses.
        :param list[str] edge_fields: Allowed property fields for the Edge subclasses.
        """
        super().__init__(node_types, node_fields, edge_types, edge_fields)

        logging.info("DataFrame info:")
        # logging.info(df.info()) # FIXME is displayed on stdout after all calls, use a stream with the buf arg here.
        logging.debug("Columns:")
        for c in df.columns:
            logging.debug(f"\t`{c}`")
        logging.info("\n"+str(df))
        self.df = df

        self.row_type = row_type
        self.type_of = type_of
        self.properties_of = properties_of
        # logging.debug(self.properties_of)
        self.skip_nan = skip_nan


    def source_type(self, row):
        """Accessor to the row type actually used by `run`.

        You may overlad this function if you want
        to make the row type dependant of some column value.

        By default, just return the default row type defined in the constructor,
        without taking the row values into account."""
        return self.row_type


    def properties(self, row, type):
        """Extract properties of `type` from `row`."""
        properties = {}

        # Find first matching parent class.
        matching_class = None
        for parent in type.mro(): # mro is guaranted in resolution order.
            if parent in self.properties_of:
                matching_class = parent
                break
        if not matching_class:
            return {} # Defaults to no property.

        # Extract and map the values.
        for in_prop in self.properties_of[matching_class]:
            out_prop = self.properties_of[type.__name__][in_prop]
            properties[out_prop] = row[in_prop]

        return properties


    def skip(self, val):
        if self.skip_nan:
            if pd.api.types.is_numeric_dtype(val) and (math.isnan(val) or val == float("nan")):
                return True
            elif str(val) == "nan": # Conversion from Pandas' `object` needs to be explicit.
                return True
        return False


    def make_edge_and_target(self, source_id, target_id, c, row, log_depth = ""):

        # target
        target_t = self.type_of[c].target_type()
        # target_id = f"{target_t.__name__}_{target_id}"
        target_id = f"{target_id}"
        # Append one (or several, if the target_t is a generator) nodes.
        self.nodes_append( self.make_node(
            target_t, id=target_id,
            properties=self.properties(row,target_t)
        ))
        logging.debug(f"{log_depth}\t\tto  `{target_t.__name__}` `{target_id}` (prop: `{', `'.join(self.properties(row,target_t).keys())}`)")

        # relation
        edge_t = self.type_of[c]
        self.edges_append( self.make_edge(
            edge_t, id=None, id_source=source_id, id_target=target_id,
            properties=self.properties(row,edge_t)
        ))
        logging.debug(f"{log_depth}\t\tvia `{edge_t.__name__}` (prop: `{', `'.join(self.properties(row,edge_t).keys())}`)")

        return target_id


    def run(self):
        """Actually run the configured extraction."""

        # FIXME: all the raised exceptions here should be specialized and handled in the executable.

        for i,row in self.df.iterrows():
            row_type = self.source_type(row)
            logging.debug(f"Extracting row {i} of type `{row_type.__name__}`...")
            if self.allows( row_type ):
                # source_id = f"{row_type.__name__}_{i}"
                source_id = f"{i}"
                self.nodes_append( self.make_node(
                    row_type, id=source_id,
                    properties=self.properties(row,row_type)
                ))
            else:
                logging.error(f"Row type `{row_type.__name__}` not allowed.")

            for c in self.type_of:
                logging.debug(f"\tMapping column `{c}`...")
                if c not in row:
                    raise ValueError(f"Column `{c}` not found in input data.")
                target_id = row[c]
                if self.skip(target_id):
                    logging.debug(f"\t\tSkip `{target_id}`")
                    continue

                if self.allows( self.type_of[c] ):
                    # If the edge is from the row type (i.e. the "source")
                    # then just create it using the source_id.
                    if issubclass(row_type, self.type_of[c].source_type()):
                        self.make_edge_and_target(source_id, target_id, c, row)

                    else: # The edge is from a random column to another.
                        # Try to handle this column first.
                        subject_type = self.type_of[c].source_type()
                        logging.debug(f"\t\tfrom `{subject_type.__name__}`")
                        # First, find the column for which
                        # the corresponding target type is defined.
                        matching_columns = []
                        for col_name, col_type in self.type_of.items():
                            target_type = col_type.target_type()
                            if col_name != c and target_type == subject_type:
                                matching_columns.append(col_name)
                        # logging.debug(f"\t\tMatching columns: `{matching_columns}`")

                        if len(matching_columns) == 0:
                            column_types = {k:self.type_of[k].target_type().__name__ for k in self.type_of if k != c}
                            raise ValueError(f"No column providing the type `{subject_type.__name__}` in `{column_types}`")

                        elif len(matching_columns) > 1:
                            msg = ", ".join("`"+mc+"`" for mc in matching_columns)
                            raise ValueError(f"I cannot handle cases when several columns provide the same subject type. Offending columns: {msg}")

                        col_name = matching_columns[0]
                        if self.type_of[col_name].source_type() != row_type:
                            raise ValueError(f"Cannot handle detached columns without a primary link to the default row subject")

                        # We now have a valid column.
                        # Jump to creating the referred subject from the pointed column.
                        other_id = self.make_edge_and_target(source_id, row[col_name], col_name, row, log_depth="\t")
                        # Then create the additional edge,
                        # this time from the previously created target_id
                        # (i.e. the column's subject).
                        self.make_edge_and_target(other_id, target_id, c, row)

                else:
                    logging.debug(f"\t\tColumn `{c}` with edge of type `{self.type_of[c]}` not allowed.")


    # FIXME see how to declare another constructor taking config and module instead of the mapping.
    @staticmethod
    def configure(config: dict, module = types):
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
        Note that `to_properties` may effectively maps to an edge type or several
        types.

        In order to allow the user to write mappings configurations using their preferred vocabulary, the following keywords are interchangeable:
            - subject = row = entry = line,
            - columns = fields,
            - to_target = to_object = to_node
            - via_edge = via_relation = via_predicate.

        :param dict config: a configuration dictionary.
        :param module: the module in which to insert the types declared by the configuration.
        :return tuple: source_t, type_of, properties_of, as needed by PandasAdapter.
        """
        def get_not(keys, pconfig=None):
            """Get the first dictionary (key,item) not matching any of the passed keys."""
            if not pconfig:
                pconfig = config
            for k in pconfig:
                if k not in keys:
                    return k,pconfig[k]

        def get(keys, pconfig=None):
            """Get a dictionary items matching either of the passed keys."""
            if not pconfig:
                pconfig = config
            for k in keys:
                if k in pconfig:
                    return pconfig[k]
            return None

        def make_node_class(name, properties = [], base = base.Node):
            # If type already exists, return it.
            if hasattr(module, name):
                logging.warning(f"Node class `{name}` already exists, I will not create another one.")
                return getattr(module, name)

            def fields():
                return list(properties.values())
            attrs = {
                "__module__": module.__name__,
                "fields": staticmethod(fields),
            }
            t = pytypes.new_class(name, (base,), {}, lambda ns: ns.update(attrs))
            logging.debug(f"Declare Node class `{t}`.")
            setattr(module, t.__name__, t)
            return t

        def make_edge_class(name, source_t, target_t, properties = [], base = base.Edge):
            # If type already exists, return it.
            if hasattr(module, name):
                logging.warning(f"Edge class `{name}` already exists, I will not create another one.")
                return getattr(module, name)

            def fields():
                return list(properties.values())
            def st():
                return source_t
            def tt():
                return target_t
            attrs = {
                "__module__": module.__name__,
                "fields":      staticmethod(fields),
                "source_type": staticmethod(st),
                "target_type": staticmethod(tt),
            }
            t = pytypes.new_class(name, (base,), {}, lambda ns: ns.update(attrs))
            logging.debug(f"Declare Edge class `{t}`.")
            setattr(module, t.__name__, t)
            return t

        def make_gen_class(name, parent, edge_t, **kwargs):
            if hasattr(generators, parent):
                parent_t = getattr(generators, parent)
                if not issubclass(parent_t, base.EdgeGenerator):
                    logging.error(f"{parent_t} {parent_t.mro()}")
                    raise TypeError(f"Object `{parent}` is not an existing generator.")
            else:
                # logging.debug(dir(generators))
                raise TypeError(f"Cannot find a generator of name `{parent}`.")

            def et():
                return edge_t
            attrs = {
                "__module__": module.__name__,
                "edge_type": staticmethod(et),
            }
            attrs.update(kwargs) # Add all passed string arguments as members.
            t = pytypes.new_class(name, (parent_t,), {}, lambda ns: ns.update(attrs))
            logging.debug(f"Declare EdgeGenerator class `{t}`.")
            setattr(module, t.__name__, t)
            return t

        type_of = {}
        properties_of = {}

        # Various keys are allowed in the config,
        # to allow the user to use their favorite ontology vocabulary.
        k_row = ["row", "entry", "line", "subject", "source"]
        k_columns = ["columns", "fields"]
        k_target = ["to_target", "to_object", "to_node"]
        k_subject = ["from_subject", "from_source"]
        k_edge = ["via_edge", "via_relation", "via_predicate"]
        k_properties = ["to_properties", "to_property"]
        k_generator = ["into_generator", "into_gen", "into_transformer", "into_trans"]

        columns = get(k_columns)

        # First, parse property mappings.
        # Because we must declare types with every members already ready.
        for col_name in columns:
            column = columns[col_name]
            properties = get(k_properties, column)

            if properties:
                for prop_name in properties:
                    classes = properties[prop_name]
                    for c in classes:
                        properties_of[c] = properties.get(c, {})
                        properties_of[c][col_name] = prop_name
                        logging.debug(f"Declare properties mapping for `{c}`: {properties_of[c]}")


        source_t = make_node_class( get(k_row), properties_of.get(get(k_row), []) )

        # Then, declare types.
        for col_name in columns:
            column = columns[col_name]
            target     = get(k_target, column)
            subject    = get(k_subject, column)
            edge       = get(k_edge, column)
            generator  = get(k_generator, column)

            if target and edge:
                target_t = make_node_class( target, properties_of.get(target, {}) )
                if subject:
                    subject_t = make_node_class( subject, properties_of.get(subject, {}) )
                    edge_t   = make_edge_class( edge, subject_t, target_t, properties_of.get(edge, {}) )
                else:
                    edge_t   = make_edge_class( edge, source_t, target_t, properties_of.get(edge, {}) )
                type_of[col_name] = edge_t # Embeds source and target types.
                logging.debug(f"Declare mapping `{col_name}` => `{edge_t.__name__}`")
            elif (target and not edge) or (edge and not target):
                logging.error(f"Cannot declare the mapping  `{col_name}` => `{edge}` (`{target}`)")

            elif generator:
                target = get(k_target, generator)
                edge   = get(k_edge, generator)
                gen_name,gen_args = get_not(k_target + k_edge, generator)
                # logging.debug(f"##### {gen_name}: {gen_args} {type(gen_args)}")

                if target and edge:
                    target_t = make_node_class( target, properties_of.get(target, {}) )
                    edge_t   = make_edge_class( edge, source_t, target_t, properties_of.get(edge, {}) )
                    gen_t    = make_gen_class( f"{gen_name}_{col_name}", gen_name, edge_t, **gen_args )
                    type_of[col_name] = gen_t
                    logging.debug(f"Declare generator `{col_name}` => `{gen_t.__name__}`(`{edge_t.__name__}`(`{target_t.__name__}`))")
                else:
                    logging.error(f"Cannot create a generator without an object and a relation.")

        logging.debug(f"Source class: {source_t}")
        logging.debug(f"Type_of: {type_of}")
        logging.debug(f"Properties_of: {properties_of}")
        return source_t, type_of, properties_of


def extract_all(df: pd.DataFrame, config: dict, module = types):
    """Proxy function for extracting from a table all nodes, edges and properties
    that are defined in a PandasAdapter configuration."""
    mapping = PandasAdapter.configure(config, module)

    allowed_node_types  = types.all.nodes()
    logging.debug(f"allowed_node_types: {allowed_node_types}")

    allowed_node_fields = types.all.node_fields()
    logging.debug(f"allowed_node_fields: {allowed_node_fields}")

    allowed_edge_types  = types.all.edges()
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
    )

    adapter.run()

    return adapter

