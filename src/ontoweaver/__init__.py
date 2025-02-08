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

logger = logging.getLogger("ontoweaver")

__all__ = ['Node', 'Edge', 'Transformer', 'Adapter', 'All', 'tabular', 'types', 'transformer', 'serialize', 'congregate', 'merge', 'fuse', 'fusion', 'exceptions', 'logger']


def extract_reconciliate_write(biocypher_config_path, schema_path, filename_to_mapping = None, dataframe_to_mapping = None, parallel_mapping = 0, separator = None, affix = "none", affix_separator = ":", raise_errors = True):
    """Calls several mappings, each on the related Pandas-readable tabular data file,
       then reconciliate duplicated nodes and edges (on nodes' IDs, merging properties in lists),
       then export everything with BioCypher.
       Returns the path to the resulting import file.

       Args:
           biocypher_config_path: the BioCypher configuration file.
           schema_path: the assembling schema file.
           filename_to_mapping: a dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them.
           dataframe_to_mapping: a dictionary mapping loaded Pandas data frame to the loaded yaml mapping object.
           parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
           separator (str, optional): The separator to use for combining values in reconciliation. Defaults to None.
           affix (str, optional): The affix to use for type inclusion. Defaults to "none".
           affix_separator: The character(s) separating the label from its type affix. Defaults to ":".

       Returns:
           The path to the import file.
   """
    nodes = []
    edges = []

    if filename_to_mapping:

        assert(type(filename_to_mapping) == dict) # data_file => mapping_file

        for data_file, mapping_file in filename_to_mapping.items():
            table = pd.read_csv(data_file)

            with open(mapping_file) as fd:
                mapping = yaml.full_load(fd)

            adapter = tabular.extract_table(
                table,
                mapping,
                parallel_mapping=parallel_mapping,
                affix=affix,
                separator=affix_separator,
                raise_errors = raise_errors,
            )

            nodes += adapter.nodes
            edges += adapter.edges

    if dataframe_to_mapping:

        assert(type(dataframe_to_mapping) == dict) # data_frame => yaml_object

        for data_frame, yaml_object in dataframe_to_mapping.items():

            adapter = tabular.extract_table(
                data_frame,
                yaml_object,
                parallel_mapping=parallel_mapping,
                affix=affix,
                separator=affix_separator,
                raise_errors = raise_errors,
            )

            nodes += adapter.nodes
            edges += adapter.edges

    fnodes, fedges = fusion.reconciliate(nodes, edges, separator = separator)

    bc = biocypher.BioCypher(    # fixme change constructor to take contents of paths instead of reading path.
        biocypher_config_path = biocypher_config_path,
        schema_config_path = schema_path
    )

    if fnodes:
        bc.write_nodes(fnodes)
    if fedges:
        bc.write_edges(fedges)
    import_file = bc.write_import_call()

    return import_file


def extract(filename_to_mapping = None, dataframe_to_mapping = None, parallel_mapping = 0, affix="none", affix_separator=":", raise_errors = True) -> Tuple[list[Tuple], list[Tuple]]:
    """
    Extracts nodes and edges from tabular data files based on provided mappings.

    Args:
        filename_to_mapping (dict): a dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them.
        dataframe_to_mapping: a dictionary mapping loaded Pandas data frame to the loaded yaml mapping object.
        parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
        affix (str, optional): The affix to use for type inclusion. Defaults to "none".
        affix_separator: The character(s) separating the label from its type affix. Defaults to ":".

    Returns:
        tuple: Two lists of tuples containing nodes and edges.
    """

    nodes = []
    edges = []

    if filename_to_mapping:

        assert(type(filename_to_mapping) == dict) # data_file => mapping_file

        for data_file, mapping_file in filename_to_mapping.items():
            table = pd.read_csv(data_file)

            with open(mapping_file) as fd:
                mapping = yaml.full_load(fd)

            adapter = tabular.extract_table(
                table,
                mapping,
                parallel_mapping=parallel_mapping,
                affix=affix,
                separator=affix_separator,
                raise_errors = raise_errors,
            )

            nodes += adapter.nodes
            edges += adapter.edges


    if dataframe_to_mapping:

        assert(type(dataframe_to_mapping) == dict) # data_frame => yaml_object

        for data_frame, yaml_object in dataframe_to_mapping.items():

            adapter = tabular.extract_table(
                data_frame,
                yaml_object,
                parallel_mapping=parallel_mapping,
                affix=affix,
                separator=affix_separator,
                raise_errors = raise_errors,
            )

            nodes += adapter.nodes
            edges += adapter.edges

    return nodes, edges


def reconciliate_write(nodes: list[Tuple], edges: list[Tuple], biocypher_config_path: str, schema_path: str, separator: str = None, raise_errors = True) -> str:
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

def validate_input_data(filename_to_mapping: dict, raise_errors = True):
    """
    Validates the data files based on provided rules in configuration.

    Args:
        filename_to_mapping (dict): a dictionary mapping data file path to the OntoWeaver mapping yaml file.

    Returns:
        bool: True if the data is valid, False otherwise.
    """

    assert(type(filename_to_mapping) == dict) # data_file => mapping_file

    for data_file, mapping_file in filename_to_mapping.items():
        table = pd.read_csv(data_file)

        with open(mapping_file) as fd:
            yaml_mapping = yaml.full_load(fd)

        parser = tabular.YamlParser(yaml_mapping, types, raise_errors = raise_errors)
        mapping = parser()

        adapter = tabular.PandasAdapter(
            table,
            *mapping,
            raise_errors = raise_errors,
        )

        try:
            adapter.validator(table)
            return True
        except pa.errors.SchemaErrors as exc:
            logger.error(f"Validation failed for {exc.failure_cases}.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return False


def validate_input_data_loaded(dataframe_to_mapping: dict, raise_errors = True):
    """
    Validates the data files based on provided rules in configuration.

    Args:
         dataframe_to_mapping (dict): a dictionary mapping data frame to the OntoWeaver mapping yaml file.

    Returns:
        bool: True if the data is valid, False otherwise.
    """


    assert (type(dataframe_to_mapping) == dict)  # data_frame => yaml_object

    for data_frame, yaml_object in dataframe_to_mapping.items():

        parser = tabular.YamlParser(yaml_object, types)
        mapping = parser()

        adapter = tabular.PandasAdapter(
            data_frame,
            *mapping,
            raise_errors = raise_errors,
        )

        try:
            adapter.validator(data_frame)
            return True
        except pa.errors.SchemaErrors as exc:
            logger.error(f"Validation failed for {exc.failure_cases}.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return False

