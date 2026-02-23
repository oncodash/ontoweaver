def test_multi_type_transformer():
    from . import testing_functions
    import logging
    import ontoweaver

    logger = logging.getLogger("ontoweaver")
    logger.setLevel(logging.DEBUG)

    directory_name = "multi_type_transformer"

    expected_nodes = [
        ('A:disease', 'disease', {'whatever': 'A0', 'something': 'Whatever it is'}),
        ('1:variant', 'variant', {'whatever': 'B1'}),
        ('0:variant', 'variant', {'whatever': 'A0'}),
        ('C:oncogenicity', 'oncogenicity', {}),
        ('2:variant', 'variant', {'whatever': 'C2'}),
        ('B:patient', 'patient', {'something': 'Whatever it is'}),
    ]

    expected_edges = [
        ('', '1:variant', 'B:patient', 'patient_has_variant', {}),
        ('', '0:variant', 'A:disease', 'variant_to_disease', {'something': 'Whatever it is'}),
        ('', '2:variant', 'C:oncogenicity', 'variant_to_oncogenicity', {'whatever': 'C2'}),
    ]

    data_mapping = {f"tests/{directory_name}/data.csv": f"tests/{directory_name}/mapping.yaml"}

    nodes, edges = ontoweaver.extract(data_mapping, affix="suffix")

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    logging.debug(fnodes)
    logging.debug(fedges)
    testing_functions.assert_equals(fnodes, expected_nodes)
    testing_functions.assert_equals(fedges, expected_edges)


if __name__ == "__main__":
    test_multi_type_transformer()
