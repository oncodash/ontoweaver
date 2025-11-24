def test_output_validation():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "output_validation"

    assert_nodes = [('1:variant', 'variant', {}),
                    ('2:variant', 'variant', {}),
                    ('3:variant', 'variant', {}),
                    ('A:patient', 'patient', {}),
                    ('B:patient', 'patient', {'version': 'Correct'}),
                    ]

    assert_edges = [('', '1:variant', 'B:patient', 'patient_has_variant', {}),
                    ('', '2:variant', 'A:patient', 'patient_has_variant', {}),
                    ]


    data_mapping = {f"tests/{directory_name}/data.csv" : f"tests/{directory_name}/mapping.yaml" }

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix", validate_output=True, raise_errors=False)

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), separator=",")


    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    assert_edge_set = testing_functions.convert_to_set(assert_edges)
    f_edge_set = testing_functions.convert_to_set(fedges)

    assert assert_edge_set == f_edge_set, "Edges are not equal."

if __name__ == "__main__":
    test_output_validation()
