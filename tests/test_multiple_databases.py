def test_multiple_databases():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "multiple_databases"

    assert_nodes = [('0:variant', 'variant', {}),
                    ('1:variant', 'variant', {}),
                    ('2:variant', 'variant', {}),
                    ('ENST00000380956:transcript', 'transcript', {}),
                    ('ENST00000523534:transcript', 'transcript', {}),
                    ('ENST00000651671:transcript', 'transcript', {}),
                    ('IRF4:gene_hugo', 'gene_hugo', {}),
                    ('NOTCH1:gene_hugo', 'gene_hugo', {}),
                    ('NRG1:gene_hugo', 'gene_hugo', {}),
                    ('Olaparib:drug', 'drug', {}),
                    ('PM_1:publication', 'publication', {}),
                    ('PM_2:publication', 'publication', {}),
                    ('PM_3:publication', 'publication', {}),
                    ('Palbociclib:drug', 'drug', {}),
                    ('Tazemetostat:drug', 'drug', {}),
                    ('non-oncogenic:disease', 'disease', {}),
                    ('oncogenic:disease', 'disease', {}),
                    ('patient_1:patient', 'patient', {}),
                    ('patient_2:patient', 'patient', {}),
                    ('patient_3:patient', 'patient', {}),
                    ]

    assert_edges = [('', '0:variant', 'NRG1:gene_hugo', 'variant_in_gene', {}),
                    ('', '0:variant', 'Palbociclib:drug', 'variant_affected_by_drug', {}),
                    ('', '0:variant', 'non-oncogenic:disease', 'variant_to_disease', {}),
                    ('', '0:variant', 'patient_1:patient', 'patient_has_variant', {}),
                    ('', '1:variant', 'IRF4:gene_hugo', 'variant_in_gene', {}),
                    ('', '1:variant', 'Tazemetostat:drug', 'variant_affected_by_drug', {}),
                    ('', '1:variant', 'non-oncogenic:disease', 'variant_to_disease', {}),
                    ('', '1:variant', 'patient_2:patient', 'patient_has_variant', {}),
                    ('', '2:variant', 'NOTCH1:gene_hugo', 'variant_in_gene', {}),
                    ('', '2:variant', 'NRG1:gene_hugo', 'variant_in_gene', {}),
                    ('', '2:variant', 'Olaparib:drug', 'variant_affected_by_drug', {}),
                    ('', '2:variant', 'oncogenic:disease', 'variant_to_disease', {}),
                    ('', '2:variant', 'patient_3:patient', 'patient_has_variant', {}),
                    ('', 'IRF4:gene_hugo', 'ENST00000380956:transcript', 'transcript_to_gene_relationship', {}),
                    ('', 'NOTCH1:gene_hugo', 'ENST00000651671:transcript', 'transcript_to_gene_relationship', {}),
                    ('', 'NRG1:gene_hugo', 'ENST00000523534:transcript', 'transcript_to_gene_relationship', {}),
                    ('', 'Olaparib:drug', 'PM_3:publication', 'treatment_has_citation', {}),
                    ('', 'Palbociclib:drug', 'PM_1:publication', 'treatment_has_citation', {}),
                    ('', 'Tazemetostat:drug', 'PM_2:publication', 'treatment_has_citation', {}),
                    ]

    list_nodes = []
    list_edges = []

    data_mapping = {f"tests/{directory_name}/data_cgi_article.csv": f"tests/{directory_name}/cgi.yaml"}

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix", raise_errors=False)

    list_nodes += nodes
    list_edges += edges

    data_mapping = {f"tests/{directory_name}/data_oncokb_article.csv": f"tests/{directory_name}/oncokb.yaml"}

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix", raise_errors=False)

    list_nodes += nodes
    list_edges += edges

    fnodes, fedges = ontoweaver.fusion.reconciliate(list_nodes, list_edges, separator=",")

    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    assert_edge_set = testing_functions.convert_to_set(assert_edges)
    f_edge_set = testing_functions.convert_to_set(fedges)

    assert assert_edge_set == f_edge_set, "Edges are not equal."

if __name__ == "__main__":
    test_multiple_databases()
