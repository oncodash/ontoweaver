from . import testing_functions
import logging
from src import ontoweaver

def test_final_type():

    logging.basicConfig(level=logging.DEBUG)

    assert_nodes = [('Q03135:protein', 'protein', {'genesymbol': 'CAV1', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('Q14573:protein', 'protein', {'genesymbol': 'ITPR3', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('Q86YM7:protein', 'protein', {'genesymbol': 'HOMER1', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('P48995:protein', 'protein', {'genesymbol': 'TRPC1', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('P0DP24:protein', 'protein', {'genesymbol': 'CALM2', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('P14416:protein', 'protein', {'genesymbol': 'DRD2', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('Q13255:protein', 'protein', {'genesymbol': 'GRM1', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('Q99750:protein', 'protein', {'genesymbol': 'MDFI', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('P0DP23:protein', 'protein', {'genesymbol': 'CALM1', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('Q14571:protein', 'protein', {'genesymbol': 'ITPR2', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('P0DP25:protein', 'protein', {'genesymbol': 'CALM3', 'ncbi_tax_id': '9606', 'entity_type': 'protein'}),
    ('P29966:protein', 'protein', {'genesymbol': 'MARCKS', 'ncbi_tax_id': '9606', 'entity_type': 'protein'})]

    assert_edges = [('', 'P0DP23:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'Q14571:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '1', 'is_inhibition': '0'}),
    ('', 'P48995:protein', 'Q14573:protein', 'protein_protein_interaction', {'is_directed': '0', 'is_stimulation': '0', 'is_inhibition': '0'}),
    ('', 'Q03135:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '1', 'is_inhibition': '0'}),
    ('', 'P0DP24:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'P29966:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'P14416:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '1', 'is_inhibition': '0'}),
    ('', 'P48995:protein', 'Q13255:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'P48995:protein', 'Q86YM7:protein', 'protein_protein_interaction', {'is_directed': '0', 'is_stimulation': '0', 'is_inhibition': '0'}),
    ('', 'Q99750:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'P0DP25:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'P0DP23:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'Q14571:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '1', 'is_inhibition': '0'}),
    ('', 'P48995:protein', 'Q14573:protein', 'protein_protein_interaction', {'is_directed': '0', 'is_stimulation': '0', 'is_inhibition': '0'}),
    ('', 'Q03135:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '1', 'is_inhibition': '0'}),
    ('', 'P0DP24:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'P29966:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'P14416:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '1', 'is_inhibition': '0'}),
    ('', 'P48995:protein', 'Q13255:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'P48995:protein', 'Q86YM7:protein', 'protein_protein_interaction', {'is_directed': '0', 'is_stimulation': '0', 'is_inhibition': '0'}),
    ('', 'Q99750:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'}),
    ('', 'P0DP25:protein', 'P48995:protein', 'protein_protein_interaction', {'is_directed': '1', 'is_stimulation': '0', 'is_inhibition': '1'})]


    data_mapping = {"/Users/mbaric/ontoweaver/tests/final_type/data.tsv" : "/Users/mbaric/ontoweaver/tests/final_type/mapping.yaml" }

    nodes, edges = ontoweaver.extract(filename_to_mapping=data_mapping, affix="suffix", sep = '\t')

    fnodes, fedges = ontoweaver.fusion.reconciliate(nodes, edges, separator=",")

    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    assert_edge_set = testing_functions.convert_to_set(assert_edges)
    f_edge_set = testing_functions.convert_to_set(fedges)

    assert assert_edge_set == f_edge_set, "Edges are not equal."

if __name__ == "__main__":
    test_final_type()
