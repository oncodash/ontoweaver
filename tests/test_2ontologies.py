
def main():
    import yaml

    import pandas as pd
    import biocypher

    import ontoweaver

    bc = biocypher.BioCypher(
        biocypher_config_path = "test_2ontologies/biocypher.yaml",
        schema_config_path = "test_2ontologies/schema.yaml"
    )
    # bc.show_ontology_structure()

    table = pd.read_csv("oim.csv")

    with open("oim.yaml") as fd:
        mapping = yaml.full_load(fd)

    adapter = ontoweaver.tabular.extract_table(table, mapping)
    assert(adapter)

    assert(adapter.nodes)
    bc.write_nodes( adapter.nodes )

    assert(adapter.edges)
    bc.write_edges( adapter.edges )

    bc.write_import_call()

if __name__ == "__main__":
    main()
