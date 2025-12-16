import logging

import pandas as pd
from typing import Optional
from collections.abc import Iterable
from enum import Enum, EnumMeta

from . import base
from . import transformer
from . import exceptions
from . import iterative
from . import validate

logger = logging.getLogger("ontoweaver")


class PandasAdapter(iterative.IterativeAdapter):
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
            subject_transformer: transformer.Transformer,
            transformers: Iterable[transformer.Transformer],
            metadata: Optional[dict] = None,
            validator: Optional[validate.InputValidator] = None,
            type_affix: Optional[base.TypeAffixes] = base.TypeAffixes.suffix,
            type_affix_sep: Optional[str] = ":",
            parallel_mapping: int = 0,
            raise_errors = True,
        ):

        super().__init__(
            subject_transformer,
            transformers,
            metadata,
            validator,
            type_affix,
            type_affix_sep,
            parallel_mapping,
            raise_errors
        )

        # logger.info("DataFrame info:")
        # logger.info(df.info())
        logger.debug("Columns:")
        for c in df.columns:
            logger.debug(f"\t`{c}`")
        # pd.set_option('display.max_rows', 30)
        # pd.set_option('display.max_columns', 30)
        # pd.set_option('display.width', 150)
        # logger.info("\n" + str(df))
        self.df = df


    def iterate(self):
        return self.df.iterrows()

