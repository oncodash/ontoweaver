def test_reverse_edge():
    from . import testing_functions
    import logging
    import ontoweaver

    logger = logging.getLogger("ontoweaver")
    logger.setLevel(logging.DEBUG)

    directory_name = "reverse_edge"

    assert_nodes = [('0:variant', 'variant', {'whatever': 'A0', 'database_name': 'my_database'}),
                    ('A:disease', 'disease', {'whatever': 'A0', 'something': 'Whatever it is', 'database_name': 'my_database'}),
                    ('1:variant', 'variant', {'whatever': 'B1', 'database_name': 'my_database'}),
                    ('B:patient', 'patient', {'something': 'Whatever it is', 'database_name': 'my_database'}),
                    ('2:variant', 'variant', {'whatever': 'C2', 'database_name': 'my_database'}),
                    ('C:oncogenicity', 'oncogenicity', {'database_name': 'my_database'}),
                    ]

    assert_edges = [('', '0:variant', 'A:disease', 'variant_to_disease', {'something': 'Whatever it is', 'database_name': 'my_database'}),
                    ('', '1:variant', 'B:patient', 'patient_has_variant', {'database_name': 'my_database'}),
                    ('', 'B:patient', '1:variant', 'variant_of_patient', {'whatever': 'B1', 'database_name': 'my_database'}),
                    ('', '2:variant', 'C:oncogenicity', 'variant_to_oncogenicity', {'whatever': 'C2', 'database_name': 'my_database'}),
                    ('', 'C:oncogenicity', '2:variant', 'oncogenicity_of_variant', {'something': 'Whatever it is', 'database_name': 'my_database'}),
                    ]

    data_mapping = {f"tests/{directory_name}/data.csv": f"tests/{directory_name}/mapping.yaml"}

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    testing_functions.assert_edges(fedges, assert_edges)


if __name__ == "__main__":
    test_reverse_edge()
