from typing import Tuple
from pathlib import Path
from abc import ABCMeta as ABSTRACT, abstractmethod

import yaml
import rdflib
import logging
import pathlib
import biocypher

import pandas as pd
from pandera.pandas import errors

from . import base
from . import transformer
Node = base.Node
Edge = base.Edge
Transformer = transformer.Transformer
Adapter = base.Adapter
All = base.All

from . import types
from . import tabular
from . import serialize
from . import congregate
from . import merge
from . import fuse
from . import fusion
from . import exceptions
from . import owl_to_biocypher
from . import biocypher_to_owl
from . import make_value
from . import make_labels
from . import loader

logger = logging.getLogger("ontoweaver")

__all__ = ['Node', 'Edge', 'Transformer', 'Adapter', 'All', 'tabular', 'types', 'transformer', 'serialize', 'congregate',
           'merge', 'fuse', 'fusion', 'exceptions', 'logger', 'owl_to_biocypher', 'biocypher_to_owl', 'make_value', "make_labels"]

def weave(biocypher_config_path, schema_path, filename_to_mapping, parallel_mapping = 0, separator = ",", affix = "none", type_affix_sep = ":", validate_output = False, raise_errors = True, **kwargs):
    """Calls several mappings, each on the related Pandas-readable tabular data file,
       then reconciliate duplicated nodes and edges (on nodes' IDs, merging properties in lists),
       then export everything with BioCypher.
       Returns the path to the resulting import file.

       Args:
           biocypher_config_path: the BioCypher configuration file.
           schema_path: the assembling schema file.
           filename_to_mapping: a dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them.
           parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
           separator (str, optional): The separator to use for combining values in reconciliation. Defaults to None.
           affix (str, optional): The affix to use for type inclusion. Defaults to "none".
           affix_separator: The character(s) separating the label from its type affix. Defaults to ":".
           validate_output: Whether to validate the output of the transformers. Defaults to False.
           raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.
           kwargs: A dictionary of arguments to pass to pandas.read_* functions.

       Returns:
           The path to the import file.
   """

    nodes, edges = extract(filename_to_mapping, parallel_mapping, affix, type_affix_sep, validate_output, raise_errors, **kwargs)

    # The fusion module is independant from OntoWeaver,
    # and thus operates on BioCypher's tuples.
    bc_nodes = ow2bc(nodes)
    bc_edges = ow2bc(edges)
    import_file = reconciliate_write(bc_nodes, bc_edges, biocypher_config_path, schema_path, separator, raise_errors)

    return import_file


def read_table_file(filename, **kwargs):
    """Read a file with Pandas, using its extension to guess its format.

    If no additional arguments are passed, it will call the
    Pandas `read_*` function with `filter_na = False`, which makes empty cell
    values to be loaded as empty strings instead of NaN values.

    Args:
        filename: The name of the data file the user wants to map.
        separator (str, optional): The separator used in the data file. Defaults to None.
        kwargs: A dictionary of arguments to pass to pandas.read_* functions.

    Raises:
        exception.FeatureError: if the extension is unknown.

    Returns:
        A Pandas DataFrame.
    """

    lpf = load.LoadPandasFile()
    data = lpf.load(filename, **kwargs)
    return data


def extract_reconciliate_write(biocypher_config_path, schema_path, data_to_mapping, parallel_mapping = 0, separator = ",", affix = "none", affix_separator = ":", validate_output = False, raise_errors = True, **kwargs):
    logger.warning("The `extract_reconciliate_write` function is deprecated and will be removed in the next version, use `weave` instead.")
    return weave(biocypher_config_path, schema_path, data_to_mapping, parallel_mapping, separator, affix, affix_separator, validate_output, raise_errors, **kwargs)


def load_extract(data, mapping, loader, parallel_mapping = 0, affix="none", type_affix_sep=":", validate_output = False, raise_errors = True, **kwargs) -> Tuple[list[Tuple], list[Tuple]]:
    logger.info(f"Use loader `{loader.__class__.__name__}` to load `{data}`")

    assert loader.allows(data), "This loader cannot handle this data"
    nodes = []
    edges = []

    data = loader(data, **kwargs)

    if mapping == "automap":
        logger.debug("\twith auto mapping")
        mapper = {}
    else:
        if type(mapping) == dict:
            logger.debug(f"\twith explicit user mapping: `{mapping}`")
            config = mapping
        else:
            assert type(mapping) == str, "I was expecting a file name as value for the data in the data_to_mapping dictionary"
            logger.debug(f"\twith user file mapping: `{mapping}`")
            with open(mapping) as fd:
                config = yaml.full_load(fd)

        parser = tabular.YamlParser(
            config,
            validate_output=validate_output,
            raise_errors = raise_errors,
        )
        mapper = parser()

    logger.debug(f"Instantiate the adapter...")
    adapter = loader.adapter()(
        data,
        *mapper,
        type_affix=affix,
        type_affix_sep=type_affix_sep,
        parallel_mapping=parallel_mapping,
        raise_errors = raise_errors,
    )
    logger.info(f"Run {type(adapter).__name__}...")
    if parallel_mapping > 0:
        logger.debug(f"\tin parallel over {parallel_mapping} cores")
        adapter.__call__()
        nodes += list(adapter.nodes)
        edges += list(adapter.edges)
    else:
        logger.debug("\tsequentially")
        for ln,le in adapter():
            nodes += ln
            edges += le
    logger.debug(f"OK — adapter ran.")

    return nodes, edges


def extract(data_to_mapping, parallel_mapping = 0, affix="none", type_affix_sep=":", validate_output = False, raise_errors = True, **kwargs) -> Tuple[list[Tuple], list[Tuple]]:
    """
    Extracts nodes and edges from tabular data files based on provided mappings.

    Args:
        filename_to_mapping (dict): A dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them.
        data_to_mapping (tuple): Tuple containing pairs of loaded Pandas DataFrames and their corresponding loaded YAML mappings.
        parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
        affix (str, optional): The affix to use for type inclusion. Defaults to "none".
        affix_sep: The character(s) separating the label from its type affix. Defaults to ":".
        validate_output: Whether to validate the output of the transformers. Defaults to False.
        raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.
        kwargs: A dictionary of arguments to pass to pandas.read_* functions.

    Returns:
        tuple: Two lists of tuples containing nodes and edges.
    """

    nodes = []
    edges = []

    lpf = loader.LoadPandasFile()
    lpd = loader.LoadPandasDataframe()
    lrf = loader.LoadRDFFile()
    lrg = loader.LoadRDFGraph()

    def pairs(iterable):
        if type(iterable) == dict:
            return iterable.items()
        else:
            return iterable

    for d2m in pairs(data_to_mapping):
        data, mapping = d2m
        found_loader = False
        for loader in [lpf, lpd, lrf, lrg]:
            if loader.allows(data):
                found_loader = True
                ln,le = load_extract(data, mapping, loader, parallel_mapping, affix, type_affix_sep, validate_output, raise_errors, **kwargs)
                nodes += ln
                edges += le
                break

        if not found_loader:
            msg = f"I found no loader able to load `{data_file}`"
            logger.error(msg)
            raise exceptions.FeatureError(msg)

        logger.debug(f"Currently {len(nodes)} nodes and {len(edges)} edges")

    return nodes, edges


def extract_table(df: pd.DataFrame, config: dict, parallel_mapping = 0, affix = "suffix", type_affix_sep = ":", validate_output = False, raise_errors = True):
    """
    Proxy function for extracting from a table all nodes, edges and properties
    that are defined in a PandasAdapter configuration.

    Args:
        df (pd.DataFrame): The DataFrame containing the input data.
        config (dict): The configuration dictionary.
        parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
        module: The module in which to insert the types declared by the configuration.
        affix (str): The type affix to use (default is "suffix").
        type_affix_sep (str): The type_affix_sep to use between labels and type annotations (default is ":").
        validate_output: Whether to validate the output of the transformers. Defaults to False.
        raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.

    Returns:
        PandasAdapter: The configured adapter.
    """
    return extract(
        [(df,config)],
        parallel_mapping,
        affix,
        type_affix_sep,
        validate_output,
        raise_errors
    )


def extract_OWL(graph: rdflib.Graph, config: dict, parallel_mapping = 0, affix = "suffix", type_affix_sep = ":", validate_output = False, raise_errors = True):
    """
    Proxy function for extracting from a table all nodes, edges and properties
    that are defined in a PandasAdapter configuration.

    Args:
        graph (rdflib.Graph): The RDF graph containing the input data.
        config (dict): The configuration dictionary.
        parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
        module: The module in which to insert the types declared by the configuration.
        affix (str): The type affix to use (default is "suffix").
        type_affix_sep (str): The type_affix_sep to use between labels and type annotations (default is ":").
        validate_output: Whether to validate the output of the transformers. Defaults to False.
        raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.

    Returns:
        OWLAdapter: The configured adapter.
    """
    return extract(
        [(graph,config)],
        parallel_mapping,
        affix,
        type_affix_sep,
        validate_output,
        raise_errors
    )


def reconciliate_write(nodes: list[Tuple], edges: list[Tuple], biocypher_config_path: str, schema_path: str, separator: str = None, raise_errors = True) -> str:
    """
    Reconciliates duplicated nodes and edges, then writes them using BioCypher.

    Args:
        nodes (list): A list of nodes to be reconciliated and written.
        edges (list): A list of edges to be reconciliated and written.
        biocypher_config_path (str): the BioCypher configuration file.
        schema_path (str): the assembling schema file
        separator (str, optional): The separator to use for combining values in reconciliation. Defaults to None.

        FIXME: The raise_errors parameter is currently not used downstream because the fusion classes are to be refactored with error management.
        raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.

    Returns:
        str: The path to the import file.
    """
    assert all(type(n) == tuple for n in nodes), "I can only reconciliate BioCypher's tuples"
    assert all(len(n) == 3 for n in nodes), "This does not seem to be BioCypher's tuples"

    assert all(type(e) == tuple for e in edges), "I can only reconciliate BioCypher's tuples"
    assert all(len(e) == 5 for e in edges), "This does not seem to be BioCypher's tuples"

    logging.info("Fuse duplicated nodes and edges...")
    fnodes, fedges = fusion.reconciliate(nodes, edges, separator = separator)
    logger.debug(f"OK, {len(fnodes)} nodes and {len(fedges)} edges after fusion")

    logging.info("Export the graph...")
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
    logging.info("OK")

    return import_file


def validate_input_data(filename_to_mapping: dict, raise_errors = True, **kwargs) -> bool:
    """
    Validates the data files based on provided rules in configuration.

    Args:
        filename_to_mapping (dict): a dictionary mapping data file path to the OntoWeaver mapping yaml file.
        raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.
        kwargs: A dictionary of arguments to pass to pandas.read_* functions.

    Returns:
        bool: True if the data is valid, False otherwise.
    """

    assert(type(filename_to_mapping) == dict) # data_file => mapping_file

    for data_file, mapping_file in filename_to_mapping.items():
        table = read_table_file(data_file, **kwargs)

        with open(mapping_file) as fd:
            yaml_mapping = yaml.full_load(fd)

        validator = tabular.YamlParser(yaml_mapping, types, raise_errors=raise_errors)._get_input_validation_rules()

        try:
            validator(table)
            return True
        except errors.SchemaErrors as exc:
            logger.error(f"Validation failed for {exc.failure_cases}.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return False


def validate_input_data_loaded(dataframe, loaded_mapping, raise_errors = True) -> bool:
    """
    Validates the data files based on provided rules in configuration.

    Args:
         dataframe: The loaded pandas DataFrame to validate.
         loaded_mapping: The mapping object to use for validation.
         raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.

    Returns:
        bool: True if the data is valid, False otherwise.
    """

    validator = tabular.YamlParser(loaded_mapping, types, raise_errors=raise_errors)._get_input_validation_rules()

    try:
        validator(dataframe)
        return True
    except errors.SchemaErrors as exc:
        logger.error(f"Validation failed for {exc.failure_cases}.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False


def ow2bc(ow_elements):
    return [e.as_tuple() for e in ow_elements]

