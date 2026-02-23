def test_custom_transformer():
    from . import testing_functions
    import logging
    import ontoweaver
    from tests.custom_transformer.custom import OmniPath

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "custom_transformer"

    expected_nodes = [
        ('Q9JMA7:protein', 'protein', {'genesymbol': 'Cyp3a41a; Cyp3a41b', 'ncbi_tax_id': '10090'}),
        ('P48281:protein', 'protein', {'genesymbol': 'Vdr', 'ncbi_tax_id': '10090'})
    ]

    expected_edges = [
        ('(P48281:protein)--[transcriptional]->(Q9JMA7:protein)', 'P48281:protein', 'Q9JMA7:protein', 'transcriptional',
            {'is_directed': 'True', 'is_stimulation': 'True', 'is_inhibition': 'False', 'consensus_direction': 'True', 'consensus_stimulation': 'True', 'consensus_inhibition': 'False', 'sources': 'ExTRI_CollecTRI;HTRI_CollecTRI;HTRIdb;HTRIdb_DoRothEA;NTNU.Curated_CollecTRI;SIGNOR_CollecTRI;TRRUST;TRRUST_CollecTRI;TRRUST_DoRothEA', 'references': 'CollecTRI:11723248;CollecTRI:11991950;CollecTRI:12147248;', 'omnipath': 'False', 'kinaseextra': 'False', 'ligrecextra': 'False', 'pathwayextra': 'False', 'mirnatarget': 'False', 'dorothea': 'True', 'collectri': 'True', 'tf_target': 'True', 'lncrna_mrna': 'False', 'tf_mirna': 'False', 'small_molecule': 'False', 'dorothea_curated': 'True', 'dorothea_chipseq': 'False', 'dorothea_tfbs': 'False', 'dorothea_coexp': 'False', 'dorothea_level': 'A;D', 'type': 'transcriptional', 'curation_effort': '21', 'extra_attrs': 'blabla', 'evidences': 'blabli'})
    ]

    ontoweaver.transformer.register(OmniPath)

    data_mapping = {f"tests/{directory_name}/data.tsv": f"tests/{directory_name}/mapping.yaml"}

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix", raise_errors=False, sep = "\t")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges))

    logging.debug(fnodes)
    logging.debug(fedges)
    testing_functions.assert_equals(fnodes, expected_nodes)
    testing_functions.assert_equals(fedges, expected_edges)


if __name__ == "__main__":
    test_custom_transformer()
