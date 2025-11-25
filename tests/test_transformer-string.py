import logging
import yaml
import io
import pandas as pd

import ontoweaver

def test_transformer_string():

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
            columns:
                - Variant
            to_subject: variant
    transformers:
        - map:
            columns:
                - Patient
            to_object: patient
            via_relation: patient_has_variant
        - map:
            columns:
                - Source
            to_properties:
                - source
            for_objects:
                - patient
                - variant
        - string:
            value: "Whatever it is"
            to_properties:
                - something
            for_objects:
                - patient
                - variant
    """

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")

    for node in nodes:
        assert(node.as_tuple()[2]["something"] == "Whatever it is")

if __name__ == "__main__":
    test_transformer_string()


