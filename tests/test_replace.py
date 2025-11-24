def test_replace():
    from . import testing_functions
    import logging
    import ontoweaver

    logging.basicConfig(level=logging.DEBUG)

    directory_name = "replace"

    assert_nodes = [('gene_hugo___123<<_>><<_>>123', 'gene_hugo', {}),
                    ('variant___2', 'variant', {}),
                    ('variant___aAB.()C0w', 'variant', {}),
                    ]

    assert_edges = [('', 'variant___aAB.()C0w', 'gene_hugo___123<<_>><<_>>123', 'variant_in_gene', {})
                    ]


    data_mapping = {f"tests/{directory_name}/data.csv" : f"tests/{directory_name}/mapping.yaml" }

    nodes, edges = ontoweaver.extract(data_mapping, affix="prefix", type_affix_sep='___', raise_errors=False)

    fnodes, fedges = ontoweaver.fusion.reconciliate(ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges), separator=",")


    assert_node_set = testing_functions.convert_to_set(assert_nodes)
    f_node_set = testing_functions.convert_to_set(fnodes)

    assert assert_node_set == f_node_set, "Nodes are not equal."

    assert_edge_set = testing_functions.convert_to_set(assert_edges)
    f_edge_set = testing_functions.convert_to_set(fedges)

    assert assert_edge_set == f_edge_set, "Edges are not equal."

if __name__ == "__main__":
    test_replace()
