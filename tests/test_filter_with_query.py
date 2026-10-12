def test_filter_with_query():
    import os
    import sys
    import logging
    from alive_progress import alive_bar

    import ontoweaver


    logging.basicConfig(level=logging.DEBUG)

    dir = "test_filter_with_query"

    data_mapping = (f"tests/{dir}/data.csv", f"tests/{dir}/mapping.yaml", {"dtype":{"Wind_max_speed":"Float64"}, "decimal":","})
    # data_mapping = [
    #     f"tests/{dir}/data.csv:tests/{dir}/mapping.yaml"
    # ]
    schema = f"tests/{dir}/schema.yaml"
    if os.path.exists(schema):
        os.remove(schema)
    schema = ontoweaver.autoschema(
        data_file_to_mapping_file = data_mapping,
        extended_schema_filename = f"tests/{dir}/schema.yaml"
    )
    
    # CLI args management
    # appname = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    # config_files = list(ontoweaver.ontoweave.config_paths(appname))
    # logging.debug(f"config files: {config_files}")
    # do = ontoweaver.ontoweave.make_cli_parser(appname, config_files)
    # asked = do.parse_args()

    # Call mappings
    # bc_nodes, bc_edges = ontoweaver.ontoweave.extract(asked)
    nodes, edges = ontoweaver.extract(data_mapping, affix="prefix")
    bc_nodes = ontoweaver.ow2bc(nodes)
    bc_edges = ontoweaver.ow2bc(edges)


    ###################################################
    # Fusion.
    ###################################################

    logging.info(f"Reconciliate properties in elements...")
    # NODES FUSION
    fusion_separator = ","

    # Find duplicates
    on_ID = ontoweaver.serialize.ID()
    nodes_congregater = ontoweaver.congregate.Nodes(on_ID)

    logging.info(f" | Congregate nodes")
    with alive_bar(len(bc_nodes), file=sys.stderr) as progress:
        for n in nodes_congregater(bc_nodes):
            progress()

    # Fuse them
    use_key    = ontoweaver.merge.string.UseKey()
    identicals = ontoweaver.merge.string.EnsureIdentical()
    #Define a merger that uses a specific fusion function depending
    # on the properties names
    howtomerge = {
        "begin_date": ontoweaver.merge.date.Earliest(),
        "end_date": ontoweaver.merge.date.Latest(),
        # "name": ontoweaver.merge.string.OrderedSet(),
        # "name": ontoweaver.merge.dictry.Append(),
        # "reporting_date": ontoweaver.merge.string.OrderedSet(),
        # "sighting_date": ontoweaver.merge.string.OrderedSet(),
        # "comment": ontoweaver.merge.string.OrderedSet(),
        # "comment_en": ontoweaver.merge.string.OrderedSet(),
        "*": ontoweaver.merge.string.OrderedSet()
    }
    props_merger = ontoweaver.merge.dictry.PerProperty(howtomerge)
    #Create the node fuser
    node_fuser = ontoweaver.fuse.Members(ontoweaver.base.Node,
            merge_ID    = use_key,
            merge_label = identicals,
            merge_prop  = props_merger,
        )

    nodes_fusioner = ontoweaver.fusion.Reduce(node_fuser)
    fnodes = set()
    logging.info(f" | Fuse nodes")
    with alive_bar(len(nodes_congregater), file=sys.stderr) as progress:
        for n in nodes_fusioner(nodes_congregater):
            fnodes.add(n)
            progress()

    ID_mapping = node_fuser.ID_mapping

    # EDGES REMAP
    # If we use on_ID/use_key,
    # we shouldn't have any need to remap sources and target IDs in edges.
    assert(len(ID_mapping) == 0)
    if len(ID_mapping) > 0:
        remaped_edges = []
        logging.info(f" | Remap edges")
        with alive_bar(len(bc_edges), file=sys.stderr) as progress:
            for e in ontoweaver.fusion.remap_edges(bc_edges, ID_mapping):
                remaped_edges.append(e)
                progress()
        logging.debug("Remaped edges:")
        for n in remaped_edges:
            logging.debug("\t"+repr(n))
    else:
        remaped_edges = bc_edges

    # EDGES FUSION
    # Find duplicates
    on_STL = ontoweaver.serialize.edge.SourceTargetLabel()
    edges_congregater = ontoweaver.congregate.Edges(on_STL)

    logging.info(f" | Congregate edges")
    with alive_bar(len(bc_edges), file=sys.stderr) as progress:
        for e in edges_congregater(remaped_edges):
            progress()

    # Fuse them
    set_of_ID       = ontoweaver.merge.string.OrderedSet(fusion_separator)
    identicals      = ontoweaver.merge.string.EnsureIdentical()
    in_lists        = ontoweaver.merge.dictry.Append(fusion_separator)
    use_last_source = ontoweaver.merge.string.UseLast()
    use_last_target = ontoweaver.merge.string.UseLast()
    edge_fuser = ontoweaver.fuse.Members(ontoweaver.base.GenericEdge,
            merge_ID     = set_of_ID,
            merge_label  = identicals,
            merge_prop   = in_lists,
            merge_source = use_last_source,
            merge_target = use_last_target
        )

    edges_fusioner = ontoweaver.fusion.Reduce(edge_fuser)
    fedges = set()
    logging.info(f" | Fuse edges")
    with alive_bar(len(edges_congregater), file=sys.stderr) as progress:
        for e in edges_fusioner(edges_congregater):
            fedges.add(e)
            progress()

    f_nodes = ontoweaver.ow2bc(fnodes)
    f_edges = ontoweaver.ow2bc(fedges)

    logging.info(f"Fused into {len(f_nodes)} nodes and {len(f_edges)} edges.")

    ###################################################
    # Export the final SKG.
    ###################################################

    logging.info("Done.")

    
if __name__ == "__main__":
    test_filter_with_query()
