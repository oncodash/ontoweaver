def test_replace():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "replace"

    expected_nodes = [
        ('gene_hugo___<<_>>', 'gene_hugo', {}),
        ('gene_hugo___<<_>>123<<_>>123<<_>>', 'gene_hugo', {}),
        ('variant___2', 'variant', {}),
        ('variant___aAB.()C0w', 'variant', {}),
    ]

    expected_edges = [
        ('', 'variant___aAB.()C0w', 'gene_hugo___<<_>>123<<_>>123<<_>>', 'variant_in_gene', {})
    ]

    # "id","gene"
    # @a##AB.()C0w@,@#!123AA123@LK.
    # 2,@L!()[]/
    data_mapping = {f"tests/{directory_name}/data.csv" : f"tests/{directory_name}/mapping.yaml" }

    # variant: default config
    # gene:
    #   forbidden: '[^0-9]+'
    #   substitute: "<<_>>"
    nodes, edges = ontoweaver.extract(data_mapping, affix="prefix", type_affix_sep='___', raise_errors=False)

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), reconciliate_sep=",")

    for n in fnodes:
        logging.debug(n)

    for e in fedges:
        logging.debug(e)

    testing_functions.assert_equals(fnodes, expected_nodes)
    testing_functions.assert_equals(fedges, expected_edges)


if __name__ == "__main__":
    test_replace()
