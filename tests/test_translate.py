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


def test_translate_on_unknown_value_skip():

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
                C: c
            on_unknown_value: skip
    """

    mapping = yaml.safe_load(yaml_mapping)

    logging.debug("Load data...")
    csv_file = "tests/" + directory_name + "/data.csv"
    table = pd.read_csv(csv_file)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, mapping, affix="none")

    assert(nodes)
    assert(edges)

    found = False
    for n in nodes:
        if n.id == "B":
            found = True

    assert not found


def test_translate_on_unknown_value_keep():

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
                C: c
            on_unknown_value: keep
    """

    mapping = yaml.safe_load(yaml_mapping)

    logging.debug("Load data...")
    csv_file = "tests/" + directory_name + "/data.csv"
    table = pd.read_csv(csv_file)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, mapping, affix="none")

    assert(nodes)
    assert(edges)

    found = False
    for n in nodes:
        if n.id == "B":
            found = True

    assert found


def test_translate_on_unknown_value_error():

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
                C: c
            on_unknown_value: error
    """

    mapping = yaml.safe_load(yaml_mapping)

    logging.debug("Load data...")
    csv_file = "tests/" + directory_name + "/data.csv"
    table = pd.read_csv(csv_file)

    logging.debug("Run the adapter...")

    caught = False
    try:
        nodes, edges = ontoweaver.extract_table(table, mapping, affix="none", raise_errors = True)
    except ontoweaver.exceptions.TransformerError as e:
        caught = True

    assert caught


if __name__ == "__main__":
    test_translate()
    test_translate_on_unknown_value_skip()
    test_translate_on_unknown_value_keep()
    test_translate_on_unknown_value_error()
