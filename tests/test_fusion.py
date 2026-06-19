import yaml
import logging
import biocypher
import ontoweaver
import pandas as pd

logger =logging.getLogger("ontoweaver")

# You may define your own "merger",
# which here indicates how to merge two strings
# (for instance two property values).
class MyMax(ontoweaver.merge.string.StringMerger):
    def merge(self, key, lhs: str, rhs: str) -> str:
        self.set( max(int(lhs), int(rhs)) )


def test_fusion():

    logger.debug("Load data...")

    data_file = "tests/test_fusion/data.csv"
    filename_to_mapping = {data_file : "tests/test_fusion/mapping.yaml"}
    nodes, edges = ontoweaver.extract(filename_to_mapping)

    # Convert OntoWeaver elements to BioCypher tuples.
    bc_nodes, bc_edges = ontoweaver.ow2bc(nodes), ontoweaver.ow2bc(edges)


    # If you want to add nodes and edges from a BioCypher "raw" adapter,
    # now is the time.


    logger.debug("NODES FUSION...")

    # Instantiate functors managing how to find duplicates.
    # Here, we consider elements to be duplicates if they have the same ID.
    on_ID = ontoweaver.serialize.ID()
    nodes_congregater = ontoweaver.congregate.Nodes(on_ID)

    # Actually build the dictionary of duplicates.
    for n in nodes_congregater(bc_nodes):
        pass

    # Instantiate functors managing how to merge variable members
    # (i.e. ID, label, properties) of element classes.
    use_key    = ontoweaver.merge.string.UseKey()
    identicals = ontoweaver.merge.string.EnsureIdentical()

    # This is a parameter of several mnergers below.
    reconciliate_sep = ";"

    # To merge property values, we will use a merger per specific property.
    # Here we need a dictioanry mapping the property name
    # to the merger instance we want to use to merge the values of this property.
    howto_merge = {
        "escat": MyMax(),  # Our own Merger define above.
          "ref": ontoweaver.merge.string.OrderedSet(reconciliate_sep),
    }
    # Instantiate the merger managing merges per property,
    # with the dictionary configuration.
    props_merger   = ontoweaver.merge.dictry.PerProperty(howto_merge)

    # Assemble a node fuser that proceeds members by members.
    node_fuser = ontoweaver.fuse.Members(ontoweaver.base.Node,
            merge_ID    = use_key,
            merge_label = identicals,
            merge_prop  = props_merger,
        )

    # Instantiate the fusion that will proceeds on pairs of nodes.
    nodes_fusioner = ontoweaver.fusion.Reduce(node_fuser)
    fusioned_nodes = set()

    # Actually run the fusion.
    for n in nodes_fusioner(nodes_congregater):
        fusioned_nodes.add(n)


    logger.debug("EDGES REMAP...")

    # If the fusion merged nodes with different IDs,
    # then the existing edges will have deprecated sources and targets.
    # We need to "remap" them to the new IDs.

    # The fusion kepts track of theses changes (if any)
    # in the following dictionary:
    ID_mapping = node_fuser.ID_mapping

    if len(ID_mapping) > 0:
        # If there is a need to remap.
        remaped_edges = []
        # The remap_edge() function apply the ID_mapping onto the previous edges.
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
    # Another way to convert back elements, this is equivalent
    # to the ontoweaver.ow2bc() function that we saw above.
    fnodes = [n.as_tuple() for n in fusioned_nodes]
    fedges = [e.as_tuple() for e in fusioned_edges]

    # We can finally export through BioCypher.
    logger.debug('Initialize BioCypher...')
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
