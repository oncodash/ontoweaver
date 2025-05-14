def test_final_type():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "final_type"

    assert_nodes = [('chair:aaaaaa', 'aaaaaa', {'localisation': 'Peterkitchen', 'blabla': 'blabla', 'source_columns': 'furniture'}),
                    ('Peter:dddddd', 'dddddd', {'blabla': 'blabla', 'source_columns': 'name'}),
                    ('kitchen:eeeeee', 'eeeeee', {'blabla': 'blabla', 'source_columns': 'localisation'}),
                    ('sofa:aaaaaa', 'aaaaaa', {'localisation': 'Paulbathroom', 'blabla': 'blabla', 'source_columns': 'furniture'}),
                    ('Paul:cccccc', 'cccccc', {'blabla': 'blabla', 'source_columns': 'name'}),
                    ('bathroom:eeeeee', 'eeeeee', {'blabla': 'blabla', 'source_columns': 'localisation'}),
                    ('fridge:aaaaaa', 'aaaaaa', {'localisation': 'Marykitchen', 'blabla': 'blabla', 'source_columns': 'furniture'}),
                    ('Mary:dddddd', 'dddddd', {'blabla': 'blabla', 'source_columns': 'name'}),
                    ('kitchen:eeeeee', 'eeeeee', {'blabla': 'blabla', 'source_columns': 'localisation'}),]

    assert_edges = [('', 'chair:aaaaaa', 'Peter:dddddd', 'will_not_sit', {'blabla': 'blabla'}),
                    ('', 'chair:aaaaaa', 'kitchen:eeeeee', 'has_localisation', {'blabla': 'blabla'}),
                    ('', 'sofa:aaaaaa', 'Paul:cccccc', 'will_sit', {'blabla': 'blabla'}),
                    ('', 'sofa:aaaaaa', 'bathroom:eeeeee', 'has_localisation', {'blabla': 'blabla'}),
                    ('', 'fridge:aaaaaa', 'Mary:dddddd', 'will_not_sit', {'blabla': 'blabla'}),
                    ('', 'fridge:aaaaaa', 'kitchen:eeeeee', 'has_localisation', {'blabla': 'blabla'}),]


    data_mapping = {f"tests/{directory_name}/data.csv" : f"tests/{directory_name}/mapping.yaml" }

    nodes, edges = ontoweaver.extract(filename_to_mapping=data_mapping, affix="suffix")

    fnodes, fedges = ontoweaver.fusion.reconciliate(nodes, edges, separator=",")

    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    assert_edge_set = testing_functions.convert_to_set(assert_edges)
    f_edge_set = testing_functions.convert_to_set(fedges)

    assert assert_edge_set == f_edge_set, "Edges are not equal."

if __name__ == "__main__":
    test_final_type()
