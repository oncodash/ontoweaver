def test_edges_between_columns():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "edges_between_columns"

    expected_nodes = [
        ('0:variant', 'variant', {}),
        ('1:variant', 'variant', {}),
        ('2:variant', 'variant', {}),
        ('3:variant', 'variant', {}),
        ('patient1:patient', 'patient', {}),
        ('patient2:patient', 'patient', {}),
        ('patient3:patient', 'patient', {}),
        ('patient4:patient', 'patient', {}),
        ('sample1:sample', 'sample', {}),
        ('sample2:sample', 'sample', {}),
        ('sample3:sample', 'sample', {}),
        ('sample4:sample', 'sample', {})
    ]

    expected_edges = [
        ('', '0:variant', 'patient1:patient', 'patient_has_variant', {}),
        ('', '0:variant', 'sample1:sample', 'variant_in_sample', {}),
        ('', '1:variant', 'patient2:patient', 'patient_has_variant', {}),
        ('', '1:variant', 'sample2:sample', 'variant_in_sample', {}),
        ('', '2:variant', 'patient3:patient', 'patient_has_variant', {}),
        ('', '2:variant', 'sample3:sample', 'variant_in_sample', {}),
        ('', '3:variant', 'patient4:patient', 'patient_has_variant', {}),
        ('', '3:variant', 'sample4:sample', 'variant_in_sample', {}),
        ('', 'sample1:sample', 'patient1:patient', 'sample_to_patient', {}),
        ('', 'sample2:sample', 'patient2:patient', 'sample_to_patient', {}),
        ('', 'sample3:sample', 'patient3:patient', 'sample_to_patient', {}),
        ('', 'sample4:sample', 'patient4:patient', 'sample_to_patient', {})
    ]


    data_mapping = {f"tests/{directory_name}/data.csv" : f"tests/{directory_name}/mapping.yaml" }

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    logging.debug(fnodes)
    logging.debug(fedges)
    testing_functions.assert_equals(fnodes, expected_nodes)
    testing_functions.assert_equals(fedges, expected_edges)

if __name__ == "__main__":
    test_edges_between_columns()
