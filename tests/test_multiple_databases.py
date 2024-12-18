import time


def test_multiple_databases():
    import yaml
    import logging
    import pandas as pd
    import biocypher
    from . import testing_functions
    import shutil
    import ontoweaver

    logging.debug("Load ontology...")

    directory_name = "multiple_databases"

    bc = biocypher.BioCypher(
        biocypher_config_path="tests/" + directory_name + "/biocypher_config.yaml",
        schema_config_path="tests/" + directory_name + "/schema_config.yaml"
    )

    nodes = []
    edges = []

    logging.debug("Load CGI data...")
    csv_file_cgi = "tests/" + directory_name + "/data_cgi_article.csv"

    table = pd.read_csv(csv_file_cgi)

    logging.debug("Load mapping CGI database ...")
    mapping_file_cgi = "tests/" + directory_name + "/cgi.yaml"

    with open(mapping_file_cgi) as fd:
        mapping = yaml.full_load(fd)

    logging.debug("Run the adapter (CGI)...")
    adapter_cgi = ontoweaver.tabular.extract_table(table, mapping)
    assert (adapter_cgi)

    logging.debug("Add CGI nodes...")
    assert (adapter_cgi.nodes)
    nodes += adapter_cgi.nodes

    logging.debug("Add CGI edges...")
    assert (adapter_cgi.edges)
    edges += adapter_cgi.edges

    logging.debug("Load OncoKB data...")
    csv_file_oncokb = "tests/" + directory_name + "/data_oncokb_article.csv"

    table = pd.read_csv(csv_file_oncokb)
    mapping_file_oncokb = "tests/" + directory_name + "/oncokb.yaml"

    with open(mapping_file_oncokb) as fd:
        mapping = yaml.full_load(fd)

    logging.debug("Run the adapter (OncoKB)...")
    adapter_oncokb = ontoweaver.tabular.extract_table(table, mapping)
    assert (adapter_oncokb)

    time.sleep(1) # Sleep for 1 second to allow the previous csv outputs to be removed. Test otherwise fails because
                  # the directory contains the BioCypher output of previous tests.

    logging.debug("Add OncoKB nodes...")
    assert (adapter_oncokb.nodes)
    nodes += adapter_oncokb.nodes

    logging.debug("Add OncoKB edges...")
    assert (adapter_oncokb.edges)
    edges += adapter_oncokb.edges

    bc.write_nodes( nodes )
    bc.write_edges( edges )

    logging.debug("Write import script...")
    bc.write_import_call()

    output_dir = testing_functions.get_latest_directory("biocypher-out")

    assert_output_path = "tests/" + directory_name + "/assert_output"

    testing_functions.compare_csv_files(assert_output_path, output_dir)

    shutil.rmtree(output_dir)


if __name__ == "__main__":
    test_multiple_databases()