def test_properties_metadata():
    import yaml
    import logging
    from . import testing_functions
    import pandas as pd
    import biocypher
    import ontoweaver
    import tempfile

    directory_name = "properties_metadata"

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
        adapter = ontoweaver.tabular.extract_table(table, mapping, affix="suffix")

        assert adapter

        logging.debug("Write nodes...")
        assert adapter.nodes
        bc.write_nodes(adapter.nodes)

        logging.debug("Write edges...")
        assert adapter.edges
        bc.write_edges(adapter.edges)

        logging.debug("Write import script...")
        bc.write_import_call()

        output_dir = temp_dir
        assert_output_path = f"tests/{directory_name}/assert_output"

        testing_functions.compare_csv_files(assert_output_path, output_dir)

if __name__ == "__main__":
    test_properties_metadata()