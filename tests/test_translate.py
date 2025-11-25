import logging
import yaml
import pandas as pd

import ontoweaver

def test_translate():

    directory_name = "simplest"

    logging.debug("Load mapping...")
    yaml_mapping = """
    row:
        rowIndex:
            to_subject: variant
    transformers:
        - translate:
            columns:
                - patient
            to_object: patient
            via_relation: patient_has_variant
            translations:
                A: a
                B: b
                C: c
    """

    mapping = yaml.safe_load(yaml_mapping)

    logging.debug("Load data...")
    csv_file = "tests/" + directory_name + "/data.csv"
    table = pd.read_csv(csv_file)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, mapping, affix="none")

    assert(nodes)
    assert(edges)

    for n in nodes:
        logging.info(n)


if __name__ == "__main__":
    test_translate()
