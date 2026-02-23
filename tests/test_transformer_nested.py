import logging
import yaml
import io
import pandas as pd

import ontoweaver

def test_transformer_nested():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """,name,aspects
0,A,{"is":"a"}
1,B,{"is":"b"}
2,C,{"is":"c"}
3,D,{"is":"d"}
"""
    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = """
row:
    map:
        column: name
        to_subject: Subject
transformers:
    - nested:
        keys:
            - aspects
            - is
        to_object: Aspect
        via_relation: is
    """

    ymap = yaml.full_load(mapping)

    logging.debug(ymap)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, ymap, affix="none")

    assert(len(nodes)==8)
    assert(len(edges)==4)


if __name__ == "__main__":
    test_transformer_nested()

