def test_final_type():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "final_type"

    assert_nodes = [('chair:aaaaaa', 'aaaaaa', (('blabla', 'blabla'), ('localisation', 'Peterkitchen'), ('source_columns', 'furniture'))),
                    ('Peter:dddddd', 'dddddd', (('blabla', 'blabla'), ('source_columns', 'name'))),
                    ('kitchen:eeeeee', 'eeeeee', (('blabla', 'blabla'), ('source_columns', 'localisation'))),
                    ('sofa:aaaaaa', 'aaaaaa', (('blabla', 'blabla'), ('localisation', 'Paulbathroom'), ('source_columns', 'furniture'))),
                    ('Paul:cccccc', 'cccccc', (('blabla', 'blabla'), ('source_columns', 'name'))),
                    ('bathroom:eeeeee', 'eeeeee', (('blabla', 'blabla'), ('source_columns', 'localisation'))),
                    ('fridge:aaaaaa', 'aaaaaa', (('blabla', 'blabla'), ('localisation', 'Marykitchen'), ('source_columns', 'furniture'))),
                    ('Mary:dddddd', 'dddddd', (('blabla', 'blabla'), ('source_columns', 'name'))),
                    ('kitchen:eeeeee', 'eeeeee', (('blabla', 'blabla'), ('source_columns', 'localisation')))]

    assert_edges = [('', 'chair:aaaaaa', 'Peter:dddddd', 'will_not_sit', (('blabla', 'blabla'))),
                    ('', 'chair:aaaaaa', 'kitchen:eeeeee', 'has_localisation', (('blabla', 'blabla'))),
                    ('', 'sofa:aaaaaa', 'Paul:cccccc', 'will_sit', (('blabla', 'blabla'))),
                    ('', 'sofa:aaaaaa', 'bathroom:eeeeee', 'has_localisation', (('blabla', 'blabla'))),
                    ('', 'fridge:aaaaaa', 'Mary:dddddd', 'will_not_sit', (('blabla', 'blabla'))),
                    ('', 'fridge:aaaaaa', 'kitchen:eeeeee', 'has_localisation', (('blabla', 'blabla')))]


    data_mapping = {f"tests/{directory_name}/data.csv" : f"tests/{directory_name}/mapping.yaml" }

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    f_node_set = testing_functions.convert_to_set(fnodes)

    for n in f_node_set:
        assert n in assert_nodes

    testing_functions.assert_edges(fedges, assert_edges)


if __name__ == "__main__":
    test_final_type()
