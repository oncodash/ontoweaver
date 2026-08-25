import io
import yaml
import logging
import ontoweaver
import pandas as pd

def test_transformer_maths():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """eq,x,y,z
A,1,2,3
B,4,5,6
C,7,8,9"""
    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = """
row:
    map:
        column: eq
        to_subject: eq
transformers:
    - maths:
        columns:
            - x
            - y
            - z
        to_object: result
        via_relation: has_result
        operation: "{x}*{y}+{z}"
    """

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")

    assert len(nodes) == 3+3  # 3 eq, 3 result

    for node in nodes:
        logging.debug(node.as_tuple()[0])

    assert float(nodes[1].as_tuple()[0]) == 5
    assert float(nodes[3].as_tuple()[0]) == 26
    assert float(nodes[5].as_tuple()[0]) == 65


if __name__ == "__main__":
    test_transformer_maths()


