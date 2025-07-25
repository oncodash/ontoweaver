def test_full_example():
    import logging
    import ontoweaver
    import biocypher
    import re
    import os

    logging.basicConfig(level=logging.DEBUG)

    dir = "full_example"

    data_mapping = {f"tests/{dir}/data.csv": f"tests/{dir}/mapping.yaml"}

    nodes, edges = ontoweaver.extract(filename_to_mapping=data_mapping, affix="none")

    fnodes, fedges = ontoweaver.fusion.reconciliate(nodes, edges, separator=",")

    bc = biocypher.BioCypher(
        biocypher_config_path = f"tests/{dir}/config.yaml",
        schema_config_path = f"tests/{dir}/schema.yaml"
    )
    bc.show_ontology_structure()

    bc.write_nodes( fnodes )
    bc.write_edges( fedges )
    path = bc.write_import_call()

    outdir = os.path.dirname(path)
    with open(f"{outdir}/biocypher.ttl", 'r') as fd:
        ttl = fd.read()

    assert("S1" in ttl)
    assert("S2" in ttl)
    assert("GA" in ttl)
    assert("GO" in ttl)
    assert(":myedge" in ttl)

if __name__ == "__main__":
    test_full_example()

