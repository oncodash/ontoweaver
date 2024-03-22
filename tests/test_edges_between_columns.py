import pytest
def test_edges_between_columns():
    import yaml
    import logging

    import pandas as pd
    import biocypher

    import tests.edges_between_columns.adapters as adapters
    import ontoweaver

    logging.debug("Load ontology...")

    directory_name = "edges_between_columns"

    nodes = []
    edges = []

    bc = biocypher.BioCypher(
        biocypher_config_path="tests/" + directory_name + "/biocypher_config.yaml",
        schema_config_path="tests/" + directory_name + "/schema_config.yaml"
    )
    # bc.show_ontology_structure()

    logging.debug("Load data...")
    csv_file = "tests/" + directory_name + "/data.csv"
    df = pd.read_csv(csv_file)

    logging.debug("Load mapping...")
    mapping_file = "tests/" + directory_name + "/mapping.yaml"
    with open(mapping_file) as fd:
        conf = yaml.full_load(fd)

    logging.debug("Run the adapter...")
    #adapter = ontoweaver.tabular.extract_all(table, mapping)

    manager = adapters.forColumnsEdges.ForColumnsEdges(df, conf)
    assert(manager)

    manager.run()
    assert(manager.nodes)
    assert(manager.edges)

    nodes += manager.nodes
    edges += manager.edges

    logging.debug("Write nodes...")
    bc.write_nodes(nodes)

    logging.debug("Write edges...")

    bc.write_edges(edges)

    logging.debug("Write import script...")
    bc.write_import_call()


if __name__ == "__main__":
    test_edges_between_columns()