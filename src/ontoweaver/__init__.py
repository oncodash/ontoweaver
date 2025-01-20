import logging
from typing import Tuple

import biocypher
import yaml
import pandas as pd
import pandera as pa

from . import base
Node = base.Node
Edge = base.Edge
Transformer = base.Transformer
Adapter = base.Adapter
All = base.All

from . import types
from . import transformer
from . import tabular
from . import serialize
from . import congregate
from . import merge
from . import fuse
from . import fusion
from . import exceptions

__all__ = ['Node', 'Edge', 'Transformer', 'Adapter', 'All', 'tabular', 'types', 'transformer', 'serialize', 'congregate', 'merge', 'fuse', 'fusion', 'exceptions']


def extract_reconciliate_write(biocypher_config_path, schema_path, data_mappings, parallel_mapping = 0, separator = None, affix = "none", affix_separator = ":"):
    """Calls several mappings, each on the related Pandas-redable tabular data file,
       then reconciliate duplicated nodes and edges (on nodes' IDs, merging properties in lists),
       then export everything with BioCypher.
       Returns the path to the resulting import file.

       Args:
           biocypher_config_path: the BioCypher configuration file
           schema_path: the assembling schema file
           data_mappings: a dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them
           parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
           separator (str, optional): The separator to use for combining values in reconciliation. Defaults to None.
           affix (str, optional): The affix to use for type inclusion. Defaults to "none".
           affix_separator: The character(s) separating the label from its type affix. Defaults to ":".

       Returns:
           The path to the import file.
   """

    assert(type(data_mappings) == dict) # data_file => mapping_file

    nodes = []
    edges = []

    for data_file, mapping_file in data_mappings.items():
        table = pd.read_csv(data_file)

        with open(mapping_file) as fd:
            mapping = yaml.full_load(fd)

        adapter = tabular.extract_all(table, mapping, parallel_mapping = parallel_mapping, affix = affix, separator = affix_separator)

        nodes += adapter.nodes
        edges += adapter.edges

    fnodes, fedges = fusion.reconciliate(nodes, edges, separator = separator)

    bc = biocypher.BioCypher(    # fixme change constructor to take contents of paths instead of reading path.
        biocypher_config_path = biocypher_config_path,
        schema_config_path = schema_path
    )

    bc.write_nodes(fnodes)
    bc.write_edges(fedges)
    import_file = bc.write_import_call()

    return import_file


def extract(data_mappings: dict, parallel_mapping = 0, affix="none", separator=":") -> Tuple[list[Tuple], list[Tuple]]:
    """
    Extracts nodes and edges from tabular data files based on provided mappings.

    Args:
        data_mappings (dict): a dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them
        parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
        separator (str, optional): The separator to use for splitting ID and type. Defaults to None.
        affix (str, optional): The affix to use for type inclusion. Defaults to "none".
        affix_separator: The character(s) separating the label from its type affix. Defaults to ":".

    Returns:
        tuple: Two lists of tuples containing nodes and edges.
    """

    assert(type(data_mappings) == dict) # data_file => mapping_file

    nodes = []
    edges = []

    for data_file, mapping_file in data_mappings.items():
        table = pd.read_csv(data_file, sep = None)

        with open(mapping_file) as fd:
            mapping = yaml.full_load(fd)

        adapter = tabular.extract_all(table, mapping, parallel_mapping=parallel_mapping, affix=affix, separator=separator)

        nodes += adapter.nodes
        edges += adapter.edges

    return nodes, edges


def reconciliate_write(nodes: list[Tuple], edges: list[Tuple], biocypher_config_path: str, schema_path: str, separator: str = None) -> str:
    """
    Reconciliates duplicated nodes and edges, then writes them using BioCypher.

    Args:
        nodes (list): A list of nodes to be reconciliated and written.
        edges (list): A list of edges to be reconciliated and written.
        biocypher_config_path (str): the BioCypher configuration file.
        schema_path (str): the assembling schema file
        separator (str, optional): The separator to use for combining values in reconciliation. Defaults to None.

    Returns:
        str: The path to the import file.
    """
    fnodes, fedges = fusion.reconciliate(nodes, edges, separator = separator)

    bc = biocypher.BioCypher(
        biocypher_config_path = biocypher_config_path,
        schema_config_path = schema_path
    )

    if fnodes:
        bc.write_nodes(fnodes)
    if fedges:
        bc.write_edges(fedges)
    #bc.summary()
    import_file = bc.write_import_call()

    return import_file

def validate_only(data_mappings: dict):
    """
    Validates the data files based on provided mapping configuration.

    Args:
        data_mappings (dict): a dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them

    Returns:
        bool: True if the data is valid, False otherwise.
    """

    for data_file, mapping_file in data_mappings.items():
        table = pd.read_csv(data_file)

        with open(mapping_file) as fd:
            yaml_mapping = yaml.full_load(fd)

        parser = tabular.YamlParser(yaml_mapping, types)
        mapping = parser()

        adapter = tabular.PandasAdapter(
            table,
            *mapping,
        )

        if adapter:
            try:
                adapter.validator(table)
                return True
            except pa.errors.SchemaErrors as exc:
                logging.info(exc.failure_cases)
                return False

