import logging
import yaml
import pandas as pd

import ontoweaver

def test_translate_file():

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
            translations_file: tests/translate/translations.tsv
            translate_from: From
            translate_to: To
            sep: TAB
    """

    mapping = yaml.safe_load(yaml_mapping)

    logging.debug("Load data...")
    csv_file = "tests/" + directory_name + "/data.csv"
    table = pd.read_csv(csv_file)

    logging.debug("Run the adapter...")
    adapter = ontoweaver.tabular.extract_table(table, mapping, affix="none")

    assert(adapter)
    assert(adapter.nodes)
    assert(adapter.edges)

    for n in adapter.nodes:
        logging.info(n)
        assert(n[0].isnumeric() or n[0].islower())


if __name__ == "__main__":
    test_translate_file()
