import logging
import yaml
import io
import pandas as pd

import ontoweaver

def test_transformer_split_string():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """Patient,Variant,Source
P1,V1-1,"S0,S1"
P1,V1-2,S1
P2,V2-1,"S2,S4"
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
        - map:
            column: Patient
            to_object: patient
            via_relation: patient_has_variant
        - split:
            column: Source
            separator: ","
            to_object: source
            via_relation: has_source
    """

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")
    fnodes, fedges = ontoweaver.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges))

    for n in fnodes:
        logging.debug(n)
    assert len(fnodes) == 11


def test_transformer_split_list():

    logging.debug("Load data...")

    table = pd.DataFrame({
        'Patient': ['P1', 'P1', 'P2', 'P2'],
        'Variant': ['V1-1', 'V1-2', 'V2-1', 'V2-2'],
        'Source' : [['S0', 'S1'], 'S1', ['S2', 'S4'], 'S3']
    })

    logging.debug("Load mappings...")

    mapping = """
    row:
        map:
            column: Variant
            to_subject: variant
    transformers:
        - map:
            column: Patient
            to_object: patient
            via_relation: patient_has_variant
        - split:
            column: Source
            separator: ","
            to_object: source
            via_relation: has_source
    """

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")
    fnodes, fedges = ontoweaver.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges))

    for n in fnodes:
        logging.debug(n)
    assert len(fnodes) == 11


if __name__ == "__main__":
    test_transformer_split_string()



