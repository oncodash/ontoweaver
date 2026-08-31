import io
import yaml
import logging
import pandas as pd

import ontoweaver

def test_append():

    sep = ";"
    merge = ontoweaver.merge.dictry.Append(sep)

    k = ontoweaver.base.Node()

    merge(k, {"p1":"x"},{"p2":"y"} )
    assert( merge.get() == {"p1":"x", "p2":"y"} )

    merge.reset()
    merge(k, {"p1":"x"},{} )
    assert( merge.get() == {"p1":"x"} )

    merge.reset()
    merge(k, {"p1":"x", "p2":"y"},{} )
    assert( merge.get() == {"p1":"x", "p2":"y"} )

    merge.reset()
    merge(k, {"p1":"x"},{"p1":"y"} )
    assert( "y" in merge.get()["p1"].split(sep) )
    assert( "x" in merge.get()["p1"].split(sep) )

    merge.reset()
    merge(k, {"p1":"x"},{"p1":"x"} )
    assert( "x;x" not in merge.get()["p1"] )
    assert( "xx" not in merge.get()["p1"] )
    assert( len(merge.get()["p1"].split(sep)) == 1 )
    assert( "x" in merge.get()["p1"].split(sep) )

    merge.reset()
    merge(k, {"p1":"abcd"},{"p1":"efgh"} )
    m = merge.get()
    assert( "abcd" in m["p1"].split(sep) )
    assert( "efgh" in m["p1"].split(sep) )

    merge.reset()
    merge(k, {"p1":"[abcd]"},{"p1":"[efgh]"} )
    m = merge.get()
    assert( "[abcd]" in m["p1"].split(sep) )
    assert( "[efgh]" in m["p1"].split(sep) )


def test_uselonger_useshorter():
    longer  = ontoweaver.merge.string.UseLonger()
    shorter = ontoweaver.merge.string.UseShorter()

    k = ontoweaver.base.Node()

    longer.reset()
    longer(k, "short", "but longer")
    assert longer.get() == "but longer"

    shorter.reset()
    shorter(k, "short", "but longer")
    assert shorter.get() == "short"


def test_merge_complete():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """Name,Diploma,Date,Source
Johann,PhD,2004,CV
Johann,PhD,2004,CV
Johann,PhD,2004,Homepage
Matthieu,PhD,2023,Web
Matthieu,PhD,2023,Homepage
Matthieu,PhD,2023,CV
Johann,DEA,2001,CV
Johann,Master,2000,Homepage
Johann,Master,2000,Homepage
Johann,DEA,2001,CV"""

    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = r"""
row:
    map:
        column: Name
        to_object: person
transformers:
    - map:
        column: Diploma
        to_object: diploma
        via_relation: has_diploma
    - map:
        column: Date
        to_property: date
        for_object: diploma
    - map:
        column: Source
        to_property: source
        for_object: diploma
"""

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")

    bc_nodes = ontoweaver.ow2bc(nodes)
    bc_edges = ontoweaver.ow2bc(edges)

    ###################################################
    # Nodes Fusion.
    ###################################################

    logging.info(f"Fusion...")
    fusion_separator = ","

    # Find duplicates
    on_id = ontoweaver.serialize.ID()
    nodes_congregater = ontoweaver.congregate.Nodes(on_id)

    logging.info(f" | Congregate nodes")
    for n in nodes_congregater(bc_nodes):
        logging.info(f"Node congregation of: {n}")

    # Fuse them
    use_longer = ontoweaver.merge.string.UseLonger()
    identicals = ontoweaver.merge.string.EnsureIdentical()
    in_lists   = ontoweaver.merge.dictry.Append(fusion_separator)
    node_fuser = ontoweaver.fuse.Members(ontoweaver.base.Node,
            merge_ID    = use_longer,
            merge_label = identicals,
            merge_prop  = in_lists,
        )

    nodes_fusioner = ontoweaver.fusion.Reduce(node_fuser)
    fnodes = set()
    logging.info(f" | Fuse nodes")
    for n in nodes_fusioner(nodes_congregater):
        logging.info(f"Node fusion of: {n}")
        fnodes.add(n)

    logging.info(f"Nodes fusion result {len(fnodes)} nodes:")
    for n in fnodes:
        logging.debug(n.as_tuple())

    ###################################################
    # Edges remapping.
    ###################################################

    ID_mapping = node_fuser.ID_mapping

    # EDGES REMAP
    if len(ID_mapping) > 0:
        remaped_edges = []
        logging.info(f" | Remap edges")
        for e in ontoweaver.fusion.remap_edges(bc_edges, ID_mapping):
            logging.info(f"Edge remaping of: {e}")
            remaped_edges.append(e)
        logging.debug("Remaped edges:")
        for n in remaped_edges:
            logging.debug("\t"+repr(n))
    else:
        remaped_edges = bc_edges

    ###################################################
    # Edges Fusion.
    ###################################################

    # Find duplicates
    on_STL = ontoweaver.serialize.edge.SourceTargetLabel()
    edges_congregater = ontoweaver.congregate.Edges(on_STL)

    logging.info(f" | Congregate edges")
    for e in edges_congregater(remaped_edges):
        logging.info(f"Edge congregation of: {e}")

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
    for e in edges_fusioner(edges_congregater):
        logging.info(f"Edge fusion of: {e}")
        fedges.add(e)

    logging.info(f"Edges fusion result {len(fedges)} edges:")
    for e in fedges:
        logging.debug(e.as_tuple())

    ###################################################
    # Checks.
    ###################################################

    logging.debug(f"Final result {len(fedges)} edges:")
    for e in fedges:
        logging.info(e.id)
    for n in fnodes:
        if n.label == "diploma":
            for k in n.properties:
                v = n.properties[k].split(fusion_separator)
                assert len(v) == len(set(v)), v
        logging.info(n)

    assert len(fnodes) == 5
    assert len(fedges) == 4


if __name__ == "__main__":
    test_append()
