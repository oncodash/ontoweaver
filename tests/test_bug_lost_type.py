import pytest
import yaml
import logging

import pandas as pd
import biocypher

import ontoweaver

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_bug_lost_type():

    directory_name = "bug_lost_type"
    log_path = "tests/" + directory_name + 'example.log'

    #logging.basicConfig(filename=log_path, encoding='utf-8', level=logging.DEBUG)
    logging.debug("Load ontology...")

    bc = biocypher.BioCypher(
        biocypher_config_path="tests/" + directory_name + "/biocypher_config.yaml",
        schema_config_path="tests/" + directory_name + "/schema_config.yaml"
    )
    # bc.show_ontology_structure()

    logging.debug("Load data...")
    csv_file = "tests/" + directory_name + "/data.csv"
    table = pd.read_csv(csv_file)

    logging.debug("Load mapping...")
    mapping_file = "tests/" + directory_name + "/mapping.yaml"
    with open(mapping_file) as fd:
        mapping = yaml.full_load(fd)

    logging.debug("Run the adapter...")
    adapter = ontoweaver.tabular.extract_all(table, mapping)
    assert (adapter)

    logging.debug("Write nodes...")
    assert (adapter.nodes)
    bc.write_nodes(adapter.nodes)

    logging.debug("Write edges...")
    assert (adapter.edges)
    bc.write_edges(adapter.edges)

    logging.debug("Write import script...")
    bc.write_import_call()

if __name__ == "__main__":
    test_bug_lost_type()
