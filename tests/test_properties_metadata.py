def test_properties_metadata():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "properties_metadata"

    assert_nodes = [('0:variant', 'variant', {'version': '1.1', 'database_name': 'my_database'}),
                    ('1:variant', 'variant', {'version': '2.2', 'database_name': 'my_database'}),
                    ('2:variant', 'variant', {'version': '3.3', 'database_name': 'my_database'}),
                    ('A:patient', 'patient', {'database_name': 'my_database', 'source_columns': 'patient'}),
                    ('B:patient', 'patient', {'database_name': 'my_database', 'source_columns': 'patient'}),
                    ('C:patient', 'patient', {'database_name': 'my_database', 'source_columns': 'patient'}),
                    ('publicationA:publication', 'publication', {'journal': 'journalA', 'database_name': 'my_database', 'source_columns': 'publication'}),
                    ('publicationB:publication', 'publication', {'journal': 'journalB', 'database_name': 'my_database', 'source_columns': 'publication'}),
                    ('publicationC:publication', 'publication', {'journal': 'journalC', 'database_name': 'my_database', 'source_columns': 'publication'}),
                    ]

    assert_edges = [('', '0:variant', 'A:patient', 'patient_has_variant', {'database_name': 'my_database'}),
                    ('', '0:variant', 'publicationA:publication', 'publication_to_variant', {'database_name': 'my_database'}),
                    ('', '1:variant', 'B:patient', 'patient_has_variant', {'database_name': 'my_database'}),
                    ('', '1:variant', 'publicationB:publication', 'publication_to_variant', {'database_name': 'my_database'}),
                    ('', '2:variant', 'C:patient', 'patient_has_variant', {'database_name': 'my_database'}),
                    ('', '2:variant', 'publicationC:publication', 'publication_to_variant', {'database_name': 'my_database'}),
                    ]


    data_mapping = {f"tests/{directory_name}/data.csv" : f"tests/{directory_name}/mapping.yaml" }

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    for node in fnodes:
        print(f"{node},")

    for edge in fedges:
        print(f"{edge},")

    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    testing_functions.assert_edges(fedges, assert_edges)


if __name__ == "__main__":
    test_properties_metadata()
