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

    logging.debug(f"NODES: {nodes}")
    logging.debug(f"EDGES: {edges}")
    bc_nodes = [n.as_tuple() for n in nodes]
    bc_edges = [e.as_tuple() for e in edges]
    fnodes, fedges = ontoweaver.fusion.reconciliate(
        bc_nodes,
        bc_edges,
        reconciliate_sep=","
    )
    logging.debug(f"FNODES: {fnodes}")
    logging.debug(f"FEDGES: {fedges}")

    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    testing_functions.assert_edges(fedges, assert_edges)


if __name__ == "__main__":
    test_simplest()
