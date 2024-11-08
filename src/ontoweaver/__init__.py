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


def extract_reconciliate_write(biocypher_config_path, schema_path, data_mappings):
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

    fnodes, fedges = fusion.reconciliate(nodes, edges)

    bc = biocypher.BioCypher(
        biocypher_config_path = biocypher_config_path,
        schema_config_path = schema_path
    )

    bc.write_nodes(fnodes)
    bc.write_edges(fedges)
    import_file = bc.write_import_call()

    return import_file

