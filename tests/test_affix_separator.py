import pytest
from tests.testing_functions import get_latest_directory, compare_csv_files
import shutil
def test_edge_direction():
    import yaml
    import logging

    import pandas as pd
    import biocypher

    import ontoweaver

    logging.debug("Load ontology...")

    directory_name = "affix_separator"

    bc = biocypher.BioCypher(
        biocypher_config_path="tests/" + directory_name + "/biocypher_config.yaml",
        schema_config_path="tests/" + directory_name + "/schema_config.yaml"
    )

    logging.debug("Load data...")
    csv_file = "tests/" + directory_name + "/data.csv"
    table = pd.read_csv(csv_file)

    logging.debug("Load mapping...")
    mapping_file = "tests/" + directory_name + "/mapping.yaml"
    with open(mapping_file) as fd:
        mapping = yaml.full_load(fd)

    logging.debug("Run the adapter...")

    adapter = ontoweaver.tabular.extract_all(table, mapping, affix="prefix", separator="___")

    assert (adapter)

    logging.debug("Write nodes...")
    assert (adapter.nodes)
    bc.write_nodes(adapter.nodes)

    logging.debug("Write edges...")
    assert (adapter.edges)
    bc.write_edges(adapter.edges)

    logging.debug("Write import script...")
    bc.write_import_call()

    output_dir = get_latest_directory("biocypher-out")

    assert_output_path = "tests/" + directory_name + "/assert_output"

    compare_csv_files(assert_output_path, output_dir)

    shutil.rmtree(output_dir)



if __name__ == "__main__":
    test_edge_direction()