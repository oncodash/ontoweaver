from typing import Tuple
from pathlib import Path
from abc import ABCMeta as ABSTRACT, abstractmethod

import os
import yaml
import copy
import rdflib
import logging
import pathlib
import warnings

import biocypher

import pandas as pd
from pandera.pandas import errors

from . import base
from . import transformer
Node = base.Node
Edge = base.Edge
Transformer = base.Transformer
Adapter = base.Adapter
All = base.All

from . import base
from . import types
from . import tabular
from . import serialize
from . import congregate
from . import merge
from . import fuse
from . import fusion
from . import exceptions
from . import make_value
from . import make_labels
from . import loader
from . import errormanager
from . import iterative
from . import xml
from . import owl
from . import mapping

logger = logging.getLogger("ontoweaver")

__all__ = ['tabular',
           'types', 'transformer', 'serialize', 'congregate',
           'merge', 'fuse', 'fusion', 'exceptions', 'logger', 'loader', 'make_value', 'make_labels', 'iterative', 'xml',
           'owl', 'mapping', 'base']

def autoschema(filename_to_mappings, existing_schema = {}, extended_schema_filename = "extended_schema.yaml", validate_output = False, raise_errors = True, overwrite = False):

    logger.info("Automatically generating a BioCypher schema based on the mappings...")
    supported = []
    for f2m in filename_to_mappings:
        _,with_mapping = f2m.split(':')
        if with_mapping == "automap":
            msg = "As of now, I don't know how to handle `automap` with `autoschema`."
            logger.error(msg)
            raise exceptions.ConfigError(msg)
        else:
            supported.append(with_mapping)

    vocab = base.MappingParser
    auto_schema = copy.deepcopy(existing_schema)
    for with_mapping in supported:
        logger.debug(f"\twith user file with_mapping: `{with_mapping}`")
        if '"' in with_mapping:
            with_mapping = with_mapping.strip('"')
        with open(with_mapping, 'r') as fd:
            config = yaml.full_load(fd)
            assert config, "I must have a YAML config."

        parser = mapping.YamlParser(
            config,
            validate_output=validate_output,
            raise_errors = raise_errors,
        )
        try:
            _ = parser()
        except Exception as err:
            logger.error(f"While parsing mapping: `{with_mapping}`.")
            raise err

        logger.debug(f"Serializing schema from mapping computed from `{with_mapping}`")
        for item in parser.declared:
            logger.debug(f"\tResolve: {item}")
            if isinstance(item, base.Transformer):
                if item.multi_type_dict:
                    # This is a type/match mapping.
                    for colval,section in item.multi_type_dict.items():
                        for pred,ptype in section.items():
                            if ptype:
                                t = ptype.__name__
                                logger.debug(f"\t\tseen type: {t}")
                                if pred in vocab.k_target \
                                         + vocab.k_subject_type \
                                         + vocab.k_final_type \
                                         + vocab.k_reverse_edge:
                                    auto_schema[t] = auto_schema.get(t, {})

                                if pred in vocab.k_properties:
                                    st = auto_schema.get(t, {})
                                    st["properties"] = st.get("properties", {})
                                    for p,v in st["properties"]:
                                        st["properties"][p] = v

                elif hasattr(item, "to_property"):
                    # This is a mono-property mapping.
                    t = item.for_object
                    logger.debug(f"\t\tproperty: {t}")
                    st = auto_schema.get(t, {})
                    st["properties"] = st.get("properties", {})
                    st["properties"][item.to_property] = "str"

                elif hasattr(item, "to_properties"):
                    # This is a multi-properties mapping.
                    # logger.debug(dir(item))
                    # logger.debug(item.to_properties)
                    # logger.debug(item.for_object)
                    t = item.for_object
                    st = auto_schema.get(t, {})
                    st["properties"] = st.get("properties", {})
                    for p in item.to_properties:
                        logger.debug(f"\t\tproperty: {p}")
                        st["properties"][p] = "str"

            elif issubclass(item, base.Node):
                t = item.__name__
                logger.debug(f"\t\tnode type: {t}")
                auto_schema[t] = auto_schema.get(t, {})
                auto_schema[t]["represented_as"] = "node"
                auto_schema[t]["label_in_input"] = t
                auto_schema[t]["properties"] = auto_schema[t].get("properties", {})
                for p in item.fields():
                    if p not in auto_schema[t]["properties"]:
                        auto_schema[t]["properties"][p] = "str"
                        logger.debug(f"\t\t\tproperty: {p}")

            elif issubclass(item, base.Edge):
                t = item.__name__
                logger.debug(f"\t\tedge type: {t}")
                auto_schema[t] = auto_schema.get(t, {})
                auto_schema[t]["represented_as"] = "edge"
                auto_schema[t]["label_in_input"] = t

                if item.source_type(): # FIXME no source for edges in extended schema.
                    auto_schema[t]["source"] = item.source_type().__name__

                auto_schema[t]["target"] = []
                for target in item.target_type():
                    auto_schema[t]["target"].append(target.__name__)

                auto_schema[t]["properties"] = auto_schema[t].get("properties", {})
                for p in item.fields():
                    if p not in auto_schema[t]["properties"]:
                        # FIXME properties does not seem to be attached to edges.
                        # if isinstance(p, base.Transformer):
                        #    p = p.properties_of[t]
                        # auto_schema[t]["properties"][p] = "str"
                        # logger.debug(f"\t\t\tproperty: {p}")
                        pass

            else:
                logger.warning(f"\t\tUnknown type `{item}`, I'll just ignore it, but you may want to double-check.")

    # def prettyprint(d, indent=2):
    #    for key, value in d.items():
    #       print('\t' * indent + str(key))
    #       if isinstance(value, dict):
    #          prettyprint(value, indent+1)
    #       else:
    #          print('\t' * (indent+1) + str(value))
    # prettyprint(auto_schema)

    # Filter out empty keys.
    logger.debug(f"Filtering out empty keys")
    sch = copy.deepcopy(auto_schema)
    for t,section in sch.items():
        if not section:
            msg = "I cannot find the information related to type `{t}`, your mapping has an error."
            logger.error(msg)
            raise exceptions.ConfigError(msg)

        for pred,val in section.items():
            if pred == "properties" and val == {}:
                del auto_schema[t][pred]
            # if not val:
            #     del auto_schema[t][pred]

    logger.debug("Collapse target multi-types into their common super-type...")
    sch = copy.deepcopy(auto_schema)
    for t,section in sch.items():
        for pred,val in section.items():
            # logger.debug(f"{pred}: {val} {type(val)}")
            if pred != "target":
                continue
            else:
                if not val:
                    logger.error(f"\tEmpty {pred}: {val}")

                elif not isinstance(val, list):
                    logger.debug(f"\tTarget already set in previous schema with value: `{val}`, skipping.")

                else:
                    assert len(val) > 0
                    # logger.debug(f"{len(val)} : {val}")
                    if len(val) == 1:
                        logger.debug(f"\tThere is only one {pred}:{val}, collapsing.")
                        auto_schema[t][pred] = val[0]
                    else:
                        msg =f"\tI don't know how to make an autoschema with" \
                             f" multiple target types like: {', '.join(val)}." \
                             " Try mapping them all to their common ancestor."
                        logger.error(msg)
                        raise exceptions.AutoSchemaError(msg)

    logger.debug("Save the extended automatic schema in YAML...")
    file_exists = os.path.isfile(extended_schema_filename)
    file_writable = os.access(extended_schema_filename, os.W_OK)

    if file_exists and not file_writable:
        msg = f"Cannot write into file `{extended_schema_filename}`."
        raise exceptions.FileAccessError(msg)

    elif (file_exists and overwrite and file_writable) or (not file_exists):
        with open(extended_schema_filename, 'w') as fd:
            fd.write(yaml.dump(auto_schema))

    elif file_exists and not overwrite:
        msg = f"You asked not to overwrite `{extended_schema_filename}`, but this file exists."
        raise exceptions.FileOverwriteError(msg)

    logger.debug("Done auto schema.")
    return extended_schema_filename


def weave(biocypher_config_path, schema_path, filename_to_mapping, parallel_mapping = 0, reconciliate_sep = "|", affix = "none", type_affix_sep = ":", validate_output = False, sort_key = None, raise_errors = True, **kwargs):
    """Calls several mappings, each on the related Pandas-readable tabular data file,
       then reconciliate duplicated nodes and edges (on nodes' IDs, merging properties in lists),
       then export everything with BioCypher.
       Returns the path to the resulting import file.

       Args:
           biocypher_config_path: the BioCypher configuration file.
           schema_path: the assembling schema file.
           filename_to_mapping: a dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them.
           parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
           reconciliate_sep (str, optional): The separator to use for combining values in reconciliation. Defaults to None.
           affix (str, optional): The affix to use for type inclusion. Defaults to "none".
           type_affix_sep: The character(s) separating the label from its type affix. Defaults to ":".
           validate_output: Whether to validate the output of the transformers. Defaults to False.
           raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.
           kwargs: A dictionary of arguments to pass to pandas.read_* functions.

       Returns:
           The path to the import file.
   """
    assert sort_key == None or callable(sort_key)

    logger.info("\tExtracting data...")
    nodes, edges = extract(filename_to_mapping, parallel_mapping, affix, type_affix_sep, validate_output, raise_errors, **kwargs)

    # The fusion module is independant from OntoWeaver,
    # and thus operates on BioCypher's tuples.
    logger.debug("Convert OntoWeaver elements to BioCypher tuples.")
    bc_nodes = ow2bc(nodes)
    bc_edges = ow2bc(edges)

    logger.info("\tFusing data...")
    fnodes, fedges = reconciliate(bc_nodes, bc_edges, reconciliate_sep, raise_errors)

    if sort_key:
        logger.info(f"Sort elements on: {sort_key}.")
        snodes = sorted(fnodes, key = sort_key)
        sedges = sorted(fedges, key = sort_key)
    else:
        logger.debug("Do not sort elements.")
        snodes = fnodes
        sedges = fedges

    import_file = write(snodes, sedges, biocypher_config_path, schema_path, raise_errors)

    return import_file


def read_table_file(filename, **kwargs):
    """Read a file with Pandas, using its extension to guess its format.

    If no additional arguments are passed, it will call the
    Pandas `read_*` function with `filter_na = False`, which makes empty cell
    values to be loaded as empty strings instead of NaN values.

    Args:
        filename: The name of the data file the user wants to map.
        kwargs: A dictionary of arguments to pass to pandas.read_* functions.

    Raises:
        exception.FeatureError: if the extension is unknown.

    Returns:
        A Pandas DataFrame.
    """

    lpf = loader.LoadPandasFile()
    data = lpf.load([filename], **kwargs)
    return data


def extract_reconciliate_write(biocypher_config_path, schema_path, data_to_mapping, parallel_mapping = 0, reconciliate_sep = "|", affix = "none", type_affix_sep = ":", validate_output = False, sort_key = None, raise_errors = True, **kwargs):
    logger.warning("The `extract_reconciliate_write` function is deprecated and will be removed in the next version, use `weave` instead.")
    return weave(biocypher_config_path, schema_path, data_to_mapping, parallel_mapping, reconciliate_sep, affix, type_affix_sep, validate_output, sort_key, raise_errors, **kwargs)


def load_extract(data, with_mapping, with_loader, parallel_mapping = 0, affix="none", type_affix_sep=":", validate_output = False, raise_errors = True, **kwargs) -> Tuple[list[Tuple], list[Tuple]]:
    logger.info(f"Use with_loader `{with_loader.__class__.__name__}` to load `{data}`")

    assert with_loader.allows([data]), "This loader cannot handle this data"
    nodes = []
    edges = []

    data = with_loader([data], **kwargs)
    mapping_options = {}

    if with_mapping == "automap":
        logger.debug("\twith auto mapping")
        mapper = {}
        mapping_options = {"automap": True}
    else:
        if isinstance(with_mapping, dict):
            logger.debug(f"\twith explicit user mapping: `{with_mapping}`")
            config = with_mapping
        else:
            assert isinstance(with_mapping, str), "I was expecting a file name as value for the data in the data_to_mapping dictionary"
            logger.debug(f"\twith user file mapping: `{with_mapping}`")
            with open(with_mapping, 'r') as fd:
                config = yaml.full_load(fd)

        parser = mapping.YamlParser(
            config,
            validate_output=validate_output,
            raise_errors = raise_errors,
        )
        mapper = parser()

    logger.debug("Instantiate the adapter...")
    adapter = with_loader.adapter(**mapping_options)(
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
    logger.debug("OK — adapter ran.")

    return nodes, edges


def extract(data_to_mapping, parallel_mapping = 0, affix="none", type_affix_sep=":", validate_output = False, raise_errors = True, **kwargs) -> Tuple[list[Tuple], list[Tuple]]:
    """
    Extracts nodes and edges from tabular data files based on provided mappings.

    Args:
        filename_to_mapping (dict): A dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them.
        data_to_mapping (tuple): Tuple containing pairs of loaded Pandas DataFrames and their corresponding loaded YAML mappings.
        parallel_mapping (int): Number of workers to use in parallel mapping. Defaults to 0 for sequential processing.
        affix (str, optional): The affix to use for type inclusion. Defaults to "none".
        type_affix_sep: The character(s) separating the label from its type affix. Defaults to ":".
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
    lrf = loader.LoadOWLFile()
    lrg = loader.LoadOWLGraph()

    def pairs(iterable):
        if isinstance(iterable, dict):
            return iterable.items()
        else:
            return iterable

    for d2m in pairs(data_to_mapping):
        data, mapping = d2m
        found_loader = False
        for with_loader in [lpf, lpd, lrf, lrg]:
            logger.debug(f"Trying loader: {type(with_loader).__name__}")
            if with_loader.allows([data]):
                logger.debug("  Loader allows this data type")
                found_loader = True
                try:
                    ln,le = load_extract(data, mapping, with_loader, parallel_mapping, affix, type_affix_sep, validate_output, raise_errors, **kwargs)
                except Exception as e:
                    logger.error(f"While loading `{data}` and mapping with `{mapping}`.")
                    raise e
                nodes += ln
                edges += le
                break
            else:
                logger.debug("  Loader does not allow this data type")

        if not found_loader:
            msg = f"I found no loader able to load `{data}`"
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


def reconciliate_write(nodes: list[Tuple], edges: list[Tuple], biocypher_config_path: str, schema_path: str, reconciliate_sep: str = None, raise_errors = True) -> str:
    """
    Reconciliates duplicated nodes and edges, then writes them using BioCypher.

    Args:
        nodes (list): A list of nodes to be reconciliated and written.
        edges (list): A list of edges to be reconciliated and written.
        biocypher_config_path (str): the BioCypher configuration file.
        schema_path (str): the assembling schema file
        reconciliate_sep (str, optional): The separator to use for combining values in reconciliation. Defaults to None.

        FIXME: The raise_errors parameter is currently not used downstream because the fusion classes are to be refactored with error management.
        raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.

    Returns:
        str: The path to the import file.
    """
    fnodes, fedges = reconciliate(nodes, edges, reconciliate_sep, raise_errors)

    import_file = write(fnodes, fedges, biocypher_config_path, schema_path, raise_errors)

    return import_file


def reconciliate(nodes: list[Tuple], edges: list[Tuple], reconciliate_sep: str = "|", raise_errors = True) -> Tuple[str]:
    """
    Reconciliates duplicated nodes and edges, then writes them using BioCypher.

    Args:
        nodes (list): A list of nodes to be reconciliated and written.
        edges (list): A list of edges to be reconciliated and written.
        reconciliate_sep (str, optional): The separator to use for combining values in reconciliation. Defaults to None.
        raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.

    Returns:
        str: The path to the import file.
    """
    assert all(isinstance(n, tuple) for n in nodes), "I can only reconciliate BioCypher's tuples"
    assert all(len(n) == 3 for n in nodes), "This does not seem to be BioCypher's tuples"

    assert all(isinstance(e, tuple) for e in edges), "I can only reconciliate BioCypher's tuples"
    assert all(len(e) == 5 for e in edges), "This does not seem to be BioCypher's tuples"

    logging.info("Fuse duplicated nodes and edges...")
    fnodes, fedges = fusion.reconciliate(nodes, edges, reconciliate_sep = reconciliate_sep, raise_errors = raise_errors)
    logger.debug(f"OK, {len(fnodes)} nodes and {len(fedges)} edges after fusion")

    return fnodes,fedges


def write(nodes: list[Tuple], edges: list[Tuple], biocypher_config_path: str, schema_path: str, raise_errors = True) -> str:
    """
    Reconciliates duplicated nodes and edges, then writes them using BioCypher.

    Args:
        nodes (list): A list of nodes to be reconciliated and written.
        edges (list): A list of edges to be reconciliated and written.
        biocypher_config_path (str): the BioCypher configuration file.
        schema_path (str): the assembling schema file
        raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.

    Returns:
        str: The path to the import file.
    """
    if not nodes and not edges:
        msg = "There is no node or edge to write."
        logger.warning(msg)
        raise RuntimeError(msg)
    else:
        logging.info("Export the graph...")
        bc = biocypher.BioCypher(
            biocypher_config_path = biocypher_config_path,
            schema_config_path = schema_path
        )

        if nodes:
            bc.write_nodes(nodes)
        if edges:
            bc.write_edges(edges)
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

    assert isinstance(filename_to_mapping, dict) # data_file => mapping_file

    for data_file, mapping_file in filename_to_mapping.items():
        table = read_table_file(data_file, **kwargs)

        with open(mapping_file, 'r') as fd:
            yaml_mapping = yaml.full_load(fd)

        validator = mapping.YamlParser(
            yaml_mapping, types,
            raise_errors=raise_errors
        )._get_input_validation_rules()

        return validate_input_data_loaded(table, validator)


def validate_input_data_loaded(dataframe, validator, raise_errors = True) -> bool:
    """
    Validates the data files based on provided rules in configuration.

    Args:
         dataframe: The loaded pandas DataFrame to validate.
         validator: The mapping object to use for validation.
         raise_errors: Whether to raise errors encountered during the mapping, and stop the mapping process. Defaults to True.

    Returns:
        bool: True if the data is valid, False otherwise.
    """

    # try:
    #     validator(dataframe)
    #     return True
    # except errors.SchemaErrors as exc:
    #     logger.error(f"Validation failed for {exc.failure_cases}.")
    #     return False
    # except Exception as e:
    #     logger.error(f"An unexpected error occurred: {e}")
    #     return False
    validator.make_raise_warnings()
    mgr = errormanager.ErrorManager(raise_errors)

    return validator(dataframe)


def ow2bc(ow_elements):
    return [e.as_tuple() for e in ow_elements]

