def test_ontology_subtypes():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "ontology_subtypes"

    assert_nodes = [('0:variant', 'variant', {}),
                    ('1:variant', 'variant', {}),
                    ('2:variant', 'variant', {}),
                    ('3:variant', 'variant', {}),
                    ('fda1:fda_evidence_level', 'fda_evidence_level', {}),
                    ('fda2:fda_evidence_level', 'fda_evidence_level', {}),
                    ('fda3:fda_evidence_level', 'fda_evidence_level', {}),
                    ('oncokb1:oncokb_evidence_level', 'oncokb_evidence_level', {}),
                    ('oncokb2:oncokb_evidence_level', 'oncokb_evidence_level', {}),
                    ('oncokb3:oncokb_evidence_level', 'oncokb_evidence_level', {}),
                    ('patient1:patient', 'patient', {}),
                    ('patient2:patient', 'patient', {}),
                    ('patient3:patient', 'patient', {}),
                    ('patient4:patient', 'patient', {}),
                    ]

    assert_edges = [('', '0:variant', 'fda1:fda_evidence_level', 'variant_to_evidence', {}),
                    ('', '0:variant', 'oncokb1:oncokb_evidence_level', 'variant_to_evidence', {}),
                    ('', '0:variant', 'patient1:patient', 'patient_has_variant', {}),
                    ('', '1:variant', 'fda2:fda_evidence_level', 'variant_to_evidence', {}),
                    ('', '1:variant', 'oncokb2:oncokb_evidence_level', 'variant_to_evidence', {}),
                    ('', '1:variant', 'patient2:patient', 'patient_has_variant', {}),
                    ('', '2:variant', 'fda3:fda_evidence_level', 'variant_to_evidence', {}),
                    ('', '2:variant', 'oncokb3:oncokb_evidence_level', 'variant_to_evidence', {}),
                    ('', '2:variant', 'patient3:patient', 'patient_has_variant', {}),
                    ('', '3:variant', 'fda3:fda_evidence_level', 'variant_to_evidence', {}),
                    ('', '3:variant', 'oncokb3:oncokb_evidence_level', 'variant_to_evidence', {}),
                    ('', '3:variant', 'patient4:patient', 'patient_has_variant', {}),
                    ]

    data_mapping = {f"tests/{directory_name}/data.csv": f"tests/{directory_name}/mapping.yaml"}

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    testing_functions.assert_edges(fedges, assert_edges)


if __name__ == "__main__":
    test_ontology_subtypes()
