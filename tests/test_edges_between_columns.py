

def test_edges_between_columns():
    import yaml
    import logging
    from . import testing_functions
    from tests.edges_between_columns import types
    import shutil
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

    assert (adapter)

    logging.debug("Write nodes...")
    assert (adapter.nodes)
    bc.write_nodes(adapter.nodes)

    logging.debug("Write edges...")
    assert (adapter.edges)
    bc.write_edges(adapter.edges)

    logging.debug("Write import script...")
    bc.write_import_call()

    output_dir = testing_functions.get_latest_directory("biocypher-out")

    assert_output_path = "tests/" + directory_name + "/assert_output"

    testing_functions.compare_csv_files(assert_output_path, output_dir)

    shutil.rmtree(output_dir)


if __name__ == "__main__":
    test_edges_between_columns()