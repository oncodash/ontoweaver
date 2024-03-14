import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable

import pandas as pd



class OncoKB(ontoweaver.tabular.PandasAdapter):

    def __init__(self,
        df: pd.DataFrame,
        config: dict,
        node_types : Optional[Iterable[ontoweaver.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[ontoweaver.Edge]] = None,
        edge_fields: Optional[list[str]] = None,
    ):
        # Default mapping as a simple config.
        from . import types
        mapping = self.configure(config, types)

        if not node_types:
            node_types  = types.all.nodes()
            logging.debug(f"node_types: {node_types}")

        if not node_fields:
            node_fields = types.all.node_fields()
            logging.debug(f"node_fields: {node_fields}")

        if not edge_types:
            edge_types  = types.all.edges()
            logging.debug(f"edge_types: {edge_types}")

        if not edge_fields:
            edge_fields = types.all.edge_fields()
            logging.debug(f"edge_fields: {edge_fields}")

        # Declare types defined in the config.
        super().__init__(
            df,
            *mapping,
            node_types,
            node_fields,
            edge_types,
            edge_fields,
        )



    def end(self):
        from . import types
        # Manual extraction of an additional edge between sample and patient.
        # Because so far the PandasAdapter only allow to declare one mapping for each column.
        for i,row in self.df.iterrows():
            sid = row["sample_id"]
            pid = row["patient_id"]
            logging.debug(f"Add a `sample_to_patient` edge between `{sid}` and `{pid}`")
            self.edges_append( self.make_edge(
                types.sample_to_patient, id=None,
                id_source=sid, id_target=pid
            ))

