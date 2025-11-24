def test_simplest():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "simplest"

    assert_nodes = [('0', 'variant', {}),
                    ('1', 'variant', {}),
                    ('2', 'variant', {}),
                    ('A', 'patient', {}),
                    ('B', 'patient', {}),
                    ('C', 'patient', {}),
                    ]

    assert_edges = [('', '0', 'A', 'patient_has_variant', {}),
                    ('', '1', 'B', 'patient_has_variant', {}),
                    ('', '2', 'C', 'patient_has_variant', {}),
                    ]

    data_mapping = {f"tests/{directory_name}/data.csv": f"tests/{directory_name}/mapping.yaml"}

    nodes, edges = ontoweaver.extract(data_mapping, affix="none")

    fnodes, fedges = ontoweaver.fusion.reconciliate(nodes, edges, separator=",")

    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    assert_edge_set = testing_functions.convert_to_set(assert_edges)
    f_edge_set = testing_functions.convert_to_set(fedges)

    assert assert_edge_set == f_edge_set, "Edges are not equal."


if __name__ == "__main__":
    test_simplest()
