import logging

import pandas as pd

from lxml import etree
from typing import Optional
from itertools import chain
from enum import Enum, EnumMeta
from collections.abc import Iterable

from . import base
from . import transformer
from . import exceptions
from . import iterative
from . import validate

logger = logging.getLogger("ontoweaver")


class XMLAdapter(iterative.IterativeAdapter):
    def __init__(self,
            xml: str,
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

        self.xml = etree.XML(xml)
        self.df = pd.DataFrame()

        columns = list(chain.from_iterable(
            [subject_transformer.columns]
            + [t.columns for t in transformers]
            + [k.columns for t in transformers for k in t.properties_of]
        ))

        logger.debug("XPath queries:")
        for c in columns:
            logger.debug(f"\t{c}")
        self.parse(columns)


    def parse(self, queries):
        assert len(queries) > 0, "No query"

        for q in queries:
            xpath = etree.ETXPath(q)
            self.df.insert(loc=0, column=q, value=[e.text for e in xpath(self.xml)])

        logger.debug(f"XPath-queried DataFrame:\n{self.df}")


    def iterate(self):
        return self.df.iterrows()
