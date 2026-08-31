import io
import sys
import yaml
import logging
import biocypher
import ontoweaver
import pandas as pd
from alive_progress import alive_bar

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


def test_fusion_remap_source():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """Last,First,Diploma
Dreo,J.,Ph.D.
Dreo,Johann,Ph.D.
Dreo,Johann,Ph.D."""

    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = r"""
row:
    compose:
        columns:
            - Last
            - First
        to_subject: person
        call:
            - cat_format:
                format_string: "{Last}, {First}"
            - western_name
transformers:
    - map:
        column: Diploma
        to_object: diploma
        via_relation: has_diploma
"""

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")

    for e in edges:
        logging.debug(e.id)

    assert len(nodes) == (len(data.split("\n"))-1)*2
    assert len(edges) == (len(data.split("\n"))-1)

    bc_nodes = ontoweaver.ow2bc(nodes)
    bc_edges = ontoweaver.ow2bc(edges)

    ###################################################
    # Nodes Fusion.
    ###################################################

    logging.info(f"Fusion...")
    fusion_separator = ","

    # Find duplicates
    on_short_name = ontoweaver.serialize.PerType({
        "person": ontoweaver.serialize.node.IDWesternNameInitials(),
        "*": ontoweaver.serialize.ID(),
    })
    nodes_congregater = ontoweaver.congregate.Nodes(on_short_name)

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

    assert len(fnodes) == 2
    assert len(fedges) == 1


def test_fusion_remap_both():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """Last,First,Diploma
Dreo,J.,PhD
Dreo,Johann,Ph.D.
Dreo,Johann,Ph.D.
Dreo,Johann,PhD
Dreo,J.,Ph.D."""

    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    mapping = r"""
row:
    compose:
        columns:
            - Last
            - First
        to_subject: person
        call:
            - cat_format:
                format_string: "{Last}, {First}"
            - western_name
transformers:
    - map:
        column: Diploma
        to_object: diploma
        via_relation: has_diploma
"""

    map = yaml.safe_load(mapping)

    logging.debug("Run the adapter...")
    nodes, edges = ontoweaver.extract_table(table, map, affix="none")

    for e in edges:
        logging.debug(e.id)

    assert len(nodes) == (len(data.split("\n"))-1)*2
    assert len(edges) == (len(data.split("\n"))-1)

    bc_nodes = ontoweaver.ow2bc(nodes)
    bc_edges = ontoweaver.ow2bc(edges)

    ###################################################
    # Nodes Fusion.
    ###################################################

    logging.info(f"Fusion...")
    fusion_separator = ","

    # Find duplicates
    on_shorts = ontoweaver.serialize.PerType({
        "person": ontoweaver.serialize.node.IDWesternNameInitials(),
        "diploma": ontoweaver.serialize.FromTransformer(
            ontoweaver.transformer.replace,
                fields = ["id"],
                forbidden = r'\.',
                substitute = '',
        ),
        "*": ontoweaver.serialize.ID(),
    })
    nodes_congregater = ontoweaver.congregate.Nodes(on_shorts)

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

    for v in ID_mapping.values():
        # Not cycles.
        assert v not in ID_mapping.keys(), f"Value `{v}` is also a key"

    logging.info("IDs remapping:")
    for k,v in ID_mapping.items():
        logging.debug(f"├ `{k}` => `{v}`")

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

    assert len(fnodes) == 2
    assert len(fedges) == 1

if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    test_fusion_remap_both()
