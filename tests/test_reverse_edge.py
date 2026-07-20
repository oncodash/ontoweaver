import io
import yaml
import logging
import ontoweaver
import pandas as pd
from . import testing_functions

logger = logging.getLogger("ontoweaver")
logger.setLevel(logging.DEBUG)


def test_reverse_edge():
    directory_name = "reverse_edge"

    expected_nodes = [
        ('0:variant', 'variant', {'whatever': 'A0', 'database_name': 'my_database'}),
        ('A:disease', 'disease', {'whatever': 'A0', 'something': 'Whatever it is', 'database_name': 'my_database'}),
        ('1:variant', 'variant', {'whatever': 'B1', 'database_name': 'my_database'}),
        ('B:patient', 'patient', {'something': 'Whatever it is', 'database_name': 'my_database'}),
        ('2:variant', 'variant', {'whatever': 'C2', 'database_name': 'my_database'}),
        ('C:oncogenicity', 'oncogenicity', {'database_name': 'my_database'}),
    ]

    expected_edges = [
        ('', '0:variant', 'A:disease', 'variant_to_disease', {'something': 'Whatever it is', 'database_name': 'my_database'}),
        ('', '1:variant', 'B:patient', 'patient_has_variant', {'database_name': 'my_database'}),
        ('', 'B:patient', '1:variant', 'variant_of_patient', {'whatever': 'B1', 'database_name': 'my_database'}),
        ('', '2:variant', 'C:oncogenicity', 'variant_to_oncogenicity', {'whatever': 'C2', 'database_name': 'my_database'}),
        ('', 'C:oncogenicity', '2:variant', 'oncogenicity_of_variant', {'something': 'Whatever it is', 'database_name': 'my_database'}),
    ]

    data_mapping = {f"tests/{directory_name}/data.csv": f"tests/{directory_name}/mapping.yaml"}

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    logger.debug(fnodes)
    logger.debug(fedges)
    testing_functions.assert_equals(fnodes, expected_nodes)
    testing_functions.assert_equals(fedges, expected_edges)


def test_reverse_edges_from_subject():

    logger.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """s,x,y
sA,x1,y1
sB,x2,y2"""
    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logger.debug("Load mappings...")

    mapping = """
row:
    map:
        column: s
        to_subject: s
transformers:
    - map:
        columns: x
        to_object: x
        via_relation: s_x
        reverse_relation: x_s
    - map:
        column: y
        from_subject: x
        to_object: y
        via_relation: x_y
        reverse_relation: y_x
    """

    map = yaml.safe_load(mapping)

    logger.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")

    for node in nodes:
        logger.debug(node.as_tuple()[0])

    for edge in edges:
        logger.debug(edge.as_tuple()[0])

    assert len(nodes) == 2*3  # 2 s, 2 x, 2 y
    assert len(edges) == 2*2*2


if __name__ == "__main__":
    test_reverse_edge()
    test_reverse_edges_from_subject()

