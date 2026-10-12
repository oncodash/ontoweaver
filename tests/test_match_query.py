def test_match_query_example():
    import logging
    import ontoweaver
    import biocypher
    import re
    import os

    logging.basicConfig(level=logging.DEBUG)

    dir = "test_match_query"

    data_mapping = (f"tests/{dir}/data.csv", f"tests/{dir}/mapping.yaml")
    # data_mapping = [
    #     f"tests/{dir}/data.csv:tests/{dir}/mapping.yaml"
    # ]
    schema = f"tests/{dir}/schema.yaml"
    if os.path.exists(schema):
        os.remove(schema)
    schema = ontoweaver.autoschema(
        data_file_to_mapping_file = data_mapping,
        extended_schema_filename = f"tests/{dir}/schema.yaml"
    )

    nodes, edges = ontoweaver.extract(data_mapping, affix="none")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    bc = biocypher.BioCypher(
        biocypher_config_path = f"tests/{dir}/config.yaml",
        schema_config_path = schema
    )
    bc.show_ontology_structure()

    bc.write_nodes( fnodes )
    bc.write_edges( fedges )
    path = bc.write_import_call()

    # outdir = os.path.dirname(path)
    # with open(f"{outdir}/biocypher.ttl", 'r') as fd:
    #     ttl = fd.read()

    # assert("S1" in ttl)
    # assert("S2" in ttl)
    # assert("GA" in ttl)
    # assert("GO" in ttl)
    # assert(":myedge" in ttl)

if __name__ == "__main__":
    test_match_query_example()

