import yaml
import logging
import biocypher
import ontoweaver
import pandas as pd

logger =logging.getLogger("ontoweaver")


class Max(ontoweaver.merge.string.StringMerger):
        def merge(self, key, lhs: str, rhs: str) -> str:
            self.set( max(int(lhs), int(rhs)) )


def test_fusion():

    data_file = "tests/test_fusion/data.csv"

    # Test of the most generic common subtype fusion

    filename_to_mapping = {data_file : "tests/test_fusion/mapping.yaml"}

    logger.debug("Load data...")
    nodes, edges = ontoweaver.extract(filename_to_mapping)

    logger.debug("Convert OntoWeaver elements to BioCypher tuples...")
    bc_nodes, bc_edges = ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges)


    # If you want to add nodes and edges from a BioCypher "raw" adapter,
    # now is the time.


    reconciliate_sep = ";"

    logger.debug("NODES FUSION...")
    # Find duplicates
    on_ID = ontoweaver.serialize.ID()
    nodes_congregater = ontoweaver.congregate.Nodes(on_ID)

    for n in nodes_congregater(bc_nodes):
        pass

    # Fuse them
    use_key    = ontoweaver.merge.string.UseKey()
    identicals = ontoweaver.merge.string.EnsureIdentical()

    howto_merge = {
        "escat": Max(),  # Our own Merger
          "ref": ontoweaver.merge.string.OrderedSet(reconciliate_sep),
    }
    props_merger   = ontoweaver.merge.dictry.PerProperty(howto_merge)

    node_fuser = ontoweaver.fuse.Members(ontoweaver.base.Node,
            merge_ID    = use_key,
            merge_label = identicals,
            merge_prop  = props_merger,
        )

    nodes_fusioner = ontoweaver.fusion.Reduce(node_fuser)
    fusioned_nodes = set()
    for n in nodes_fusioner(nodes_congregater):
        fusioned_nodes.add(n)


    logger.debug("EDGES REMAP...")
    ID_mapping = node_fuser.ID_mapping

    if len(ID_mapping) > 0:
        remaped_edges = []
        for e in ontoweaver.fusion.remap_edges(bc_edges, ID_mapping):
            remaped_edges.append(e)
    else:
        # If we use on_ID/use_key,
        # we shouldn't have any need to remap sources and target IDs in edges.
        remaped_edges = bc_edges


    logger.debug("EDGES FUSION...")
    # Find duplicates
    on_STL = ontoweaver.serialize.edge.SourceTargetLabel()
    edges_congregater = ontoweaver.congregate.Edges(on_STL)

    for e in edges_congregater(remaped_edges):
        pass

    # Fuse them
    set_of_ID       = ontoweaver.merge.string.OrderedSet(reconciliate_sep)
    identicals      = ontoweaver.merge.string.EnsureIdentical()
    in_lists        = ontoweaver.merge.dictry.Append(reconciliate_sep)
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
    fusioned_edges = set()
    for e in edges_fusioner(edges_congregater):
        fusioned_edges.add(e)


    logger.debug('Convert back elements to BioCypher tuples...')
    fnodes = [n.as_tuple() for n in fusioned_nodes]
    fedges = [e.as_tuple() for e in fusioned_edges]


    logger.debug('Initialize Biocypher...')
    bc = biocypher.BioCypher(
        biocypher_config_path = "tests/test_fusion/config.yaml",
        schema_config_path = "tests/test_fusion/schema.yaml"
    )

    logger.debug('Write graph...')
    if nodes:
        bc.write_nodes(fnodes)
    if edges:
        bc.write_edges(fedges)

    import_file = bc.write_import_call()
    print(import_file)


if __name__ == "__main__":
    test_fusion()
