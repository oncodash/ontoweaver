
def main():
    import yaml

    import pandas as pd
    import biocypher

    import ontoweaver
    import preprocessing.preprocess_ontology as preprocess


    ontology_path = ""#"test_preprocessing_ontology/"
    ontology_file = "OIM_test_preprocessing.owl"


    #Preprocessing of the ontology so that it is compliant with biocypher requierements:
    preprocess.to_bc_ontology(ontology_path, ontology_file)

    bc = biocypher.BioCypher(
        biocypher_config_path = "biocypher.yaml",
        schema_config_path = "schema.yaml"
    )
    # bc.show_ontology_structure()

    table = pd.read_csv("oim.csv")

    with open("mapping.yaml") as fd:
        mapping = yaml.full_load(fd)

    adapter = ontoweaver.tabular.extract_all(table, mapping)
    assert(adapter)

    assert(adapter.nodes)
    bc.write_nodes( adapter.nodes )

    assert(adapter.edges)
    bc.write_edges( adapter.edges )

    bc.write_import_call()

if __name__ == "__main__":
    main()
