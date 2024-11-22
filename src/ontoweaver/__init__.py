import biocypher
import yaml
import pandas as pd

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

__all__ = ['Node', 'Edge', 'Transformer', 'Adapter', 'All', 'tabular', 'types', 'transformer', 'serialize', 'congregate', 'merge', 'fuse', 'fusion']


def extract_reconciliate_write(biocypher_config_path, schema_path, data_mappings, separator = None):
    """Calls several mappings, each on the related Pandas-redable tabular data file,
       then reconciliate duplicated nodes and edges (on nodes' IDs, merging properties in lists),
       then export everything with BioCypher.
       Returns the path to the resulting import file.

       Args:
           biocypher_config_path: the BioCypher configuration file
           schema_path: the assembling schema file
           data_mappings: a dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them

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

        adapter = tabular.extract_all(table, mapping, affix="none")

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

def extract(data_mappings, separator = None, affix = "none"):
    assert(type(data_mappings) == dict) # data_file => mapping_file

    nodes = []
    edges = []

    for data_file, mapping_file in data_mappings.items():
        table = pd.read_csv(data_file, sep = None)

        with open(mapping_file) as fd:
            mapping = yaml.full_load(fd)

        adapter = tabular.extract_all(table, mapping, affix=affix, separator=separator)

        nodes += adapter.nodes
        edges += adapter.edges

    return nodes, edges

def reconciliate_write(nodes, edges, biocypher_config_path, schema_path, separator = None):

    fnodes, fedges = fusion.reconciliate(nodes, edges, separator = separator)

    bc = biocypher.BioCypher(    # fixme change constructor to take contents of paths instead of reading path.
        biocypher_config_path = biocypher_config_path,
        schema_config_path = schema_path
    )

    bc.write_nodes(fnodes)
    bc.write_edges(fedges)
    #bc.summary()
    import_file = bc.write_import_call()

    return import_file
