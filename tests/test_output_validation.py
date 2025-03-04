def test_output_validation():
    import yaml
    import logging
    from . import testing_functions
    import pandas as pd
    import biocypher
    import ontoweaver
    import tempfile

    directory_name = "output_validation"

    with tempfile.TemporaryDirectory() as temp_dir:
        logging.debug(f"Using temporary directory at: {temp_dir}")

        bc = biocypher.BioCypher(
            biocypher_config_path=f"tests/{directory_name}/biocypher_config.yaml",
            schema_config_path=f"tests/{directory_name}/schema_config.yaml",
            output_directory=temp_dir
        )

        logging.debug("Load data...")
        csv_file = f"tests/{directory_name}/data.csv"
        table = pd.read_csv(csv_file)

        logging.debug("Load mapping...")
        mapping_file = f"tests/{directory_name}/mapping.yaml"
        with open(mapping_file) as fd:
            mapping = yaml.full_load(fd)

        logging.debug("Run the adapter...")
        adapter = ontoweaver.tabular.extract_table(table, mapping, raise_errors=False)

        assert adapter
        assert adapter.nodes
        assert adapter.edges

        nodes = []
        edges = []

        nodes += adapter.nodes
        edges += adapter.edges

        fnodes, fedges = ontoweaver.fusion.reconciliate(nodes, edges, separator=None)

        fnodes.sort()
        fedges.sort()

        bc.write_nodes(fnodes)
        bc.write_edges(fedges)

        logging.debug("Write import script...")
        bc.write_import_call()

        output_dir = temp_dir
        assert_output_path = f"tests/{directory_name}/assert_output"

        testing_functions.compare_csv_files(assert_output_path, output_dir)

if __name__ == "__main__":
    test_output_validation()