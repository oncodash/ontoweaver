from typing import Tuple
from pathlib import Path
from alive_progress import alive_bar
from abc import ABCMeta as ABSTRACT, abstractmethod

import yaml
import rdflib
import logging
import logging
import pathlib
import biocypher

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
from . import owl_to_biocypher
from . import biocypher_to_owl
from . import make_value
from . import make_labels

logger = logging.getLogger("ontoweaver")

__all__ = ['Node', 'Edge', 'Transformer', 'Adapter', 'All', 'tabular', 'types', 'transformer', 'serialize', 'congregate',
           'merge', 'fuse', 'fusion', 'exceptions', 'logger', 'owl_to_biocypher', 'biocypher_to_owl', 'make_value', "make_labels"]

class Loader(metaclass = ABSTRACT):
    def __call__(self, data, **kwargs):
        if self.allows(data):
            return self.load(data, **kwargs)

    @abstractmethod
    def allows(self, data):
        raise NotImplementedError()

    @abstractmethod
    def load(self, data, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def adapter(self):
        return NotImplementedError()


class LoadPandasDataframe(Loader):
    def allows(self, data):
        return type(data) == pd.DataFrame

    def load(self, df, **kwargs):
        return df

    def adapter(self):
        return PandasAdapter

class LoadPandasFile(Loader):
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

    def __init__(self):
        self.read_funcs = {
        '.csv'    : pd.read_csv,
        '.tsv'    : pd.read_csv,
        '.txt'    : pd.read_csv,

        '.xls'    : pd.read_excel,
        '.xlsx'   : pd.read_excel,
        '.xlsm'   : pd.read_excel,
        '.xlsb'   : pd.read_excel,
        '.odf'    : pd.read_excel,
        '.ods'    : pd.read_excel,
        '.odt'    : pd.read_excel,

        '.json'   : pd.read_json,
        '.html'   : pd.read_html,
        '.xml'    : pd.read_xml,
        '.hdf'    : pd.read_hdf,
        '.feather': pd.read_feather,
        '.parquet': pd.read_parquet,
        '.pickle' : pd.read_pickle,
        '.orc'    : pd.read_orc,
        '.sas'    : pd.read_sas,
        '.spss'   : pd.read_spss,
        '.stata'  : pd.read_stata,
    }

    def allows(self, filename):
        ext = pathlib.Path(filename).suffix 
        if type(filename) == str or type(filename) == pathlib.Path:
            if ext in self.read_funcs:
                return True

        return False


    def load(self, filename, **kwargs):
        ext = pathlib.Path(filename).suffix
        if not self.allows(filename):
            msg = f"File format '{ext}' of file '{filename}' is not supported (I can only read one of: {' ,'.join(self.read_funcs.keys())})"
            logger.error(msg)
            raise exceptions.FeatureError(msg)

        if not kwargs:
            # We probably don't want NaN as a default,
            # since they tend to end up in a label.
            kwargs.update({'na_filter': True,
                        'engine': 'python'}) #'c' engine does not support regex separators (separators > 1 char and different
                                          # from '\s+' are interpreted as regex) which results in an error.

        return self.read_funcs[ext](filename, **kwargs)


    def adapter(self):
        return tabular.PandasAdapter


class LoadRDFGraph(Loader):
    def allows(self, data):
        return type(data) == rdflib.Graph

    def load(self, g, **kwargs):
        return g

    def adapter(self):
        return tabular.RDFAutoAdapter


class LoadRDFFile(Loader):
    def __init__(self):
        self.allowed = [".owl", ".xml", ".n3", ".turtle", ".ttl", ".nt", ".trig", ".trix", ".json-ld"]

    def allows(self, filename):
        ext = pathlib.Path(filename).suffix

        if type(filename) == str or type(filename) == pathlib.Path:
            if ext in self.allowed:
                return True

        msg = f"File format '{ext}' of file '{filename}' is not supported (I can only read one of: {', '.join(self.allowed)})"
        logger.warning(msg)
        return False


    def load(self, filename, **kwargs):
        ext = pathlib.Path(filename).suffix
        if not self.allows(filename):
            msg = f"File format '{ext}' of file '{filename}' is not supported (I can only read one of: {' ,'.join(self.allowed)})"
            logger.error(msg)
            raise exceptions.FeatureError(msg)

        g = rdflib.Graph()

        if ext == ".owl":
            g.parse(filename, format = "xml")
        else:
            g.parse(filename) # Guess the format based on extension.

        return g


    def adapter(self):
        return tabular.OWLAutoAdapter


def weave(biocypher_config_path, schema_path, filename_to_mapping, parallel_mapping = 0, separator = None, affix = "none", type_affix_sep = ":", validate_output = False, raise_errors = True, **kwargs):
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

    import_file = reconciliate_write(nodes, edges, biocypher_config_path, schema_path, separator, raise_errors)

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

    lpf = LoadPandasFile()
    data = lpf.load(filename, **kwargs)
    return data


def extract_reconciliate_write(biocypher_config_path, schema_path, data_to_mapping, parallel_mapping = 0, separator = None, affix = "none", affix_separator = ":", validate_output = False, raise_errors = True, **kwargs):
    logger.warning("The `extract_reconciliate_write` function is deprecated and will be removed in the next version, use `weave` instead.")
    return weave(biocypher_config_path, schema_path, data_to_mapping, parallel_mapping, separator, affix, affix_separator, validate_output, raise_errors, **kwargs)


def extract(data_to_mapping, parallel_mapping = 0, affix="none", type_affix_sep=":", validate_output = False, raise_errors = True, **kwargs) -> Tuple[list[Tuple], list[Tuple]]:
    """
    Extracts nodes and edges from tabular data files based on provided mappings.

    Args:
        filename_to_mapping (dict): A dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them.
        dataframe_to_mapping (tuple): Tuple containing pairs of loaded Pandas DataFrames and their corresponding loaded YAML mappings.
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

    lpf = LoadPandasFile()
    lpd = LoadPandasDataframe()
    lrf = LoadRDFFile()
    lrg = LoadRDFGraph()

    for data, mapping in data_to_mapping.items():
        found_loader = False
        for loader in [lpf, lpd, lrf, lrg]:
            if loader.allows(data):
                found_loader = True
                logger.info(f"Use loader `{loader.__class__.__name__}` to load `{data}`")
                data = loader(data, **kwargs)

                if mapping == "automap":
                    logger.debug("\twith auto mapping")
                    mapping = {}
                else:
                    logger.debug(f"\twith user mapping: `{mapping}`")
                    with open(mapping) as fd:
                        config = yaml.full_load(fd)
                        parser = tabular.YamlParser(
                            config,
                            validate_output=validate_output,
                            raise_errors = raise_errors,
                        )
                        mapping = parser()

                logger.debug(f"Run the adapter...")
                adapter = loader.adapter()(
                    data,
                    *mapping,
                    type_affix=affix,
                    type_affix_sep=type_affix_sep,
                    parallel_mapping=parallel_mapping,
                    raise_errors = raise_errors,
                )
                if parallel_mapping > 0:
                    adapter()
                    nodes += list(adapter.nodes)
                    edges += list(adapter.edges)
                else:
                    for n,e in adapter():
                        nodes.append(n)
                        edges.append(e)
                logger.debug(f"OK — adapter ran.")
                break

        if not found_loader:
            msg = f"I found no loader able to load `{data_file}`"
            logger.error(msg)
            raise exceptions.FeatureError(msg)

        logger.debug(f"Currently {len(nodes)} nodes and {len(edges)} edges")

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

        FIXME: The raise_errors parameter is currently not used downstream because the fusion classes are to be refactored with error management.
        raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.

    Returns:
        str: The path to the import file.
    """

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
        except pa.errors.SchemaErrors as exc:
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
    except pa.errors.SchemaErrors as exc:
        logger.error(f"Validation failed for {exc.failure_cases}.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False

