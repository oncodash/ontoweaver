def test_final_type():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "final_type"

    expected_nodes = [
        ('chair:aaaaaa', 'aaaaaa', {'localisation': 'Peterkitchen', 'blabla': 'blabla', 'source_columns': 'furniture'}),
        ('kitchen:eeeeee', 'eeeeee', {'blabla': 'blabla', 'source_columns': 'localisation'}),
        ('Paul:cccccc', 'cccccc', {'blabla': 'blabla', 'source_columns': 'name'}),
        ('bathroom:eeeeee', 'eeeeee', {'blabla': 'blabla', 'source_columns': 'localisation'}),
        ('Mary:dddddd', 'dddddd', {'blabla': 'blabla', 'source_columns': 'name'}),
        ('sofa:aaaaaa', 'aaaaaa', {'localisation': 'Paulbathroom', 'blabla': 'blabla', 'source_columns': 'furniture'}),
        ('fridge:aaaaaa', 'aaaaaa', {'localisation': 'Marykitchen', 'blabla': 'blabla', 'source_columns': 'furniture'}),
        ('Peter:dddddd', 'dddddd', {'blabla': 'blabla', 'source_columns': 'name'})
    ]

    expected_edges = [
        ('(chair:aaaaaa)--[has_localisation]->(kitchen:eeeeee)', 'chair:aaaaaa', 'kitchen:eeeeee', 'has_localisation', {'blabla': 'blabla'}),
        ('(chair:aaaaaa)--[will_not_sit]->(Peter:dddddd)', 'chair:aaaaaa', 'Peter:dddddd', 'will_not_sit', {'blabla': 'blabla'}),
        ('(fridge:aaaaaa)--[will_not_sit]->(Mary:dddddd)', 'fridge:aaaaaa', 'Mary:dddddd', 'will_not_sit', {'blabla': 'blabla'}),
        ('(sofa:aaaaaa)--[will_sit]->(Paul:cccccc)', 'sofa:aaaaaa', 'Paul:cccccc', 'will_sit', {'blabla': 'blabla'}),
        ('(sofa:aaaaaa)--[has_localisation]->(bathroom:eeeeee)', 'sofa:aaaaaa', 'bathroom:eeeeee', 'has_localisation', {'blabla': 'blabla'}),
        ('(fridge:aaaaaa)--[has_localisation]->(kitchen:eeeeee)', 'fridge:aaaaaa', 'kitchen:eeeeee', 'has_localisation', {'blabla': 'blabla'})
    ]

    data_mapping = {f"tests/{directory_name}/data.csv" : f"tests/{directory_name}/mapping.yaml" }

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    logging.debug(fnodes)
    logging.debug(fedges)
    testing_functions.assert_equals(fnodes, expected_nodes)
    testing_functions.assert_equals(fedges, expected_edges)


if __name__ == "__main__":
    test_final_type()
