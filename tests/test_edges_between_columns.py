from tests.testing_functions import get_latest_directory, compare_csv_files
from tests.edges_between_columns import types
import shutil

def test_edges_between_columns():
    import yaml
    import logging

    import pandas as pd
    import biocypher
    import ontoweaver

    logging.debug("Load ontology...")

    directory_name = "edges_between_columns"

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
    adapter.add_edge(ontoweaver.types.sample, ontoweaver.types.patient, types.sample_to_patient)

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
    test_edges_between_columns()