def test_affix_separator():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "affix_separator"

    assert_nodes = [('patient___A', 'patient', {}),
                    ('patient___B', 'patient', {}),
                    ('patient___C', 'patient', {}),
                    ('publication___publicationA', 'publication', {}),
                    ('publication___publicationB', 'publication', {}),
                    ('publication___publicationC', 'publication', {}),
                    ('variant___0', 'variant', {}),
                    ('variant___1', 'variant', {}),
                    ('variant___2', 'variant', {}),
                    ]

    assert_edges = [('', 'variant___0', 'patient___A', 'patient_has_variant', {}),
                    ('', 'variant___0', 'publication___publicationA', 'publication_to_variant', {}),
                    ('', 'variant___1', 'patient___B', 'patient_has_variant', {}),
                    ('', 'variant___1', 'publication___publicationB', 'publication_to_variant', {}),
                    ('', 'variant___2', 'patient___C', 'patient_has_variant', {}),
                    ('', 'variant___2', 'publication___publicationC', 'publication_to_variant', {}),
                    ]

    data_mapping = {f"tests/{directory_name}/data.csv": f"tests/{directory_name}/mapping.yaml"}

    nodes, edges = ontoweaver.extract(data_mapping, affix="prefix", type_affix_sep="___")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges))

    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)
    logging.debug(f_node_set)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    testing_functions.assert_edges(fedges, assert_edges)


if __name__ == "__main__":
    test_affix_separator()
