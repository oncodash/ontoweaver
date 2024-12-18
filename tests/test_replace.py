import time


def test_replace():
    import yaml
    import logging
    import pandas as pd
    import biocypher
    import shutil
    from . import testing_functions

    import ontoweaver

    logging.debug("Load ontology...")

    directory_name = "replace"

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

    adapter = ontoweaver.tabular.extract_table(table, mapping, affix="prefix", separator="___")

    time.sleep(1) # Sleep for 1 second to allow the previous csv outputs to be removed. Test otherwise fails because
                  # the directory contains the BioCypher output of previous tests.

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
    test_replace()
