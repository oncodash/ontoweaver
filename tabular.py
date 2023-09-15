import types as pytypes
import logging
from typing import Optional
from collections.abc import Iterable

import pandas as pd

from . import base
from . import types

class PandasAdapter(base.Adapter):

    def __init__(self,
        df: pd.DataFrame,
        row_type: base.Node,
        type_of: dict[str, base.Edge],
        properties_of: dict[base.Node, dict[str,str]],
        node_types : Optional[Iterable[base.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[base.Edge]] = None,
        edge_fields: Optional[list[str]] = None,
    ):
        super().__init__(node_types, node_fields, edge_types, edge_fields)
        print(self._nodes)

        logging.info(df.info())
        logging.info("\n"+str(df))
        self.df = df

        self.row_type = row_type
        self.type_of = type_of
        self.properties_of = properties_of


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
            raise TypeError(f"Type `{type.__name__}` has no parent in properties mapping.")

        # Exctract and map the values.
        for in_prop in self.properties_of[matching_class]:
            out_prop = self.properties_of[type][in_prop]
            properties[out_prop] = row[in_prop]

        return properties


    def run(self):
        for i,row in self.df.iterrows():
            logging.debug(f"Extracting row {i}...")
            if self.allows( self.row_type ):
                target_id = f"{self.row_type.__name__}_{i}"
                self.nodes_append( self.make(
                    self.row_type, id=target_id,
                    properties=self.properties(row,self.row_type)
                ))

            for c in self.type_of:
                logging.debug(f"Mapping column `{c}`...")
                if c not in row:
                    raise ValueError(f"Column `{c}` not found in input data.")
                val = row[c]
                if self.allows( self.type_of[c] ):
                    # target should always be the target above.
                    assert(issubclass(self.type_of[c].target_type(), self.row_type))
                    # source
                    st = self.type_of[c].source_type()
                    source_id = f"{st.__name__}_{val}"
                    self.nodes_append( self.make(
                        st, id=source_id,
                        properties=self.properties(row,st)
                    ))
                    # relation
                    et = self.type_of[c]
                    self.edges_append( self.make(
                        et, id=None, id_source=source_id, id_target=target_id,
                        properties=self.properties(row,et)
                    ))
                    logging.debug(f"Append `{st}` via `{et}`")
                else:
                    logging.debug(f"Column `{c}` not allowed.")


class Configure:
    def __init__(self,
        config: dict,
        module,
    ):

        self.config = config
        self.module = module

        source_t, type_of, properties_of = self.parse()
        logging.debug(f"Source class: {source_t}")
        logging.debug(f"Type_of: {type_of}")
        logging.debug(f"Properties_of: {properties_of}")

    def get(self, key, config=None):
        if not config:
            config = self.config
        for k in key:
            if k in config:
                return config[k]
        return None

    def make_node(self, name, base = base.Node):
        t = type(name, (base,), {"__module__": self.module.__name__})
        def empty_fields(cls):
            return []
        t.fields = staticmethod(pytypes.MethodType(empty_fields, t))
        logging.debug(f"Declare Node class `{t}`.")
        setattr(self.module, t.__name__, t)
        return t

    def make_edge(self, name, source_t, target_t, base = base.Edge):
        t = type(name, (base,), {"__module__": self.module.__name__})
        def empty_fields(cls):
            return []
        t.fields = staticmethod(pytypes.MethodType(empty_fields, t))
        def st(cls):
            return source_t
        def tt(cls):
            return target_t
        t.source_type = staticmethod(pytypes.MethodType(st, t))
        t.target_type = staticmethod(pytypes.MethodType(tt, t))
        logging.debug(f"Declare Edge class `{t}`.")
        setattr(self.module, t.__name__, t)
        return t

    def parse(self):
        type_of = {}
        properties_of = {}

        k_row = ["row", "entry", "line"]
        k_columns = ["columns", "fields"]
        k_target = ["to_target", "to_object", "to_node"]
        k_edge = ["via_edge", "via_relation", "via_predicate"]
        k_properties = ["to_properties"]

        source_t = self.make_node( self.get(k_row) )

        columns = self.get(k_columns)
        for col_name in columns:
            column = columns[col_name]
            target     = self.get(k_target, column)
            edge       = self.get(k_edge, column)
            properties = self.get(k_properties, column)

            if target and edge:
                target_t = self.make_node( target )
                edge_t   = self.make_edge( edge, source_t, target_t )
                type_of[col_name] = edge_t # Embeds source and target types.

            if properties:
                for prop_name in properties:
                    types = properties[prop_name]
                    for t in types:
                        properties_of[t] = properties.get(t, {})
                        properties_of[t][col_name] = prop_name

        return source_t, type_of, properties_of

