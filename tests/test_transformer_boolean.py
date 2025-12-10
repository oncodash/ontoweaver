import logging
import yaml
import io
import pandas as pd

import ontoweaver

def test_transformer_boolean():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """Patient,Variant,Source
P1,V1-1,S0
P1,V1-2,S1
P2,V2-1,S2
P2,V2-2,S3"""
    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = """
row:
    map:
        column: Variant
        to_subject: variant
transformers:
    - boolean:
        column: Source
        to_object: source_quality
        via_relation: has_source_quality
        consider_true:
            - S0
            - S1
        consider_false:
            - S2
            - S3
        output_true: good
        output_false: not_good
    """

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")

    for node in nodes:
        print(node.as_tuple())
        if node.as_tuple()[1] == "source_quality":
            assert node.as_tuple()[0] in ["good", "not_good"]


if __name__ == "__main__":
    test_transformer_boolean()

