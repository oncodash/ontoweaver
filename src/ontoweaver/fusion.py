import logging
from abc import abstractmethod, ABCMeta
from typing import Optional

from . import base
from . import fuse
from . import merge
from . import congregate
from . import serialize

logger = logging.getLogger("ontoweaver")

class Fusioner(metaclass=ABCMeta):
    """"Interface for classes going over a list of duplicates to decide how to fuse them.

    The contract is to be called on a congregate.Congregater object,
    which holds a `duplicates" member.
    This `Congregater.duplicates` variable is a dictionary mapping
    a key to a list of duplicates.
    The key takes the form of a string made from serializing some members of the targeted elements.

    Derived classes should implement the __call__ method.
    """
    @abstractmethod
    def __call__(self, congregater: congregate.Congregater) -> set[base.Element]:
        raise NotImplementedError


class Reduce(Fusioner):
    """A Fusioner that operates on the duplicates list by reducing it.

    This processes the given Congregater hosting the list of duplicates by
    iterating over each list of duplicates.
    Each merge processes by iterating over them as pairs of candidate `base.Element`s,
    like a classical "reduce" function.

    The given functor called to operate the fusion on a pair of Elements
    should honor the interface of a fuse.Fuser.

    It returns a set of unique (fused) Elements.
    """

    def __init__(self, fuser: fuse.Fuser):
        self.fuser = fuser

    def __call__(self, congregater: congregate.Congregater) -> set[base.Element]:
        fusioned = set()
        for key, elem_list in congregater.duplicates.items():
            self.fuser.reset()
            logger.debug(f"Fusion of {type(congregater).__name__} with {type(congregater.serializer).__name__} for key: `{key}`")
            assert(elem_list)
            assert(len(elem_list) > 0)

            # Manual functools.reduce without initial state.
            it = iter(elem_list)
            lhs = next(it)
            logger.debug(f"  Fuse element with key `{lhs}`...")
            logger.debug(f"    with itself: {repr(lhs)}")
            self.fuser(key, lhs, lhs)
            logger.debug(f"      = {repr(self.fuser.get())}")
            for rhs in it:
                logger.debug(f"    with `{rhs}`: {repr(rhs)}")
                self.fuser(key, lhs, rhs)
                logger.debug(f"      = {repr(self.fuser.get())}")

            # Convert to final string.
            f = self.fuser.get()
            logger.debug(f"  Fused: {repr(f)}")
            assert(issubclass(type(f), base.Element))
            fusioned.add(f)
        logger.debug(f"Fusioned {len(fusioned)} elements.")
        return fusioned


def remap_edges(edges, ID_mapping):
    """Changes the id_source and id_target of the edges in the given list,
    using the given dictionary, which is usually issued from a fuse.Fuser,
    after it has merged nodes.

    When a fusion occured on nodes, their ID way have changed,
    hence the need to remap the corresponding IDs in edges' sources and targets.

    Args:
        edges: a list of Biocypher tuples representing edges
        ID_mapping: a dictionary mapping old IDs to new Ids

    Returns:
        the list of remaped edges tuples
    """

    remaped_edges = []
    for et in edges:
        edge = base.GenericEdge.from_tuple(et, serialize.edge.All())

        s = ID_mapping.get(edge.id_source, None)
        if s:
            edge.id_source = s

        t = ID_mapping.get(edge.id_target, None)
        if t:
            edge.id_target = t

        remaped_edges.append(edge.as_tuple())

    return remaped_edges


def reconciliate_nodes(nodes, separator = None):
    """Operates a simple fusion on a list of nodes.

    A "reconciliation" finds nodes with duplicated IDs,
    and merge their properties without losing information.
    If nodes with the same IDs have different types,
    a ValueError is raised.

    More precisely:
        - the node Congregater uses serialize.ID,
        - nodes are merged members by members with fuse.Members, which uses:
            - merge.string.UseKey for IDs,
            - merge.string.EnsureIdentical for labels,
            - merge.dictry.Append for properties.

    Args:
        nodes: a list of base.Node

    Returns:
        the list of fused nodes and the ID mapping dictionary
    """

    # NODES FUSION
    # Find duplicates
    on_ID = serialize.ID()
    nodes_congregater = congregate.Nodes(on_ID)
    nodes_congregater(nodes)

    # Fuse them
    use_key    = merge.string.UseKey()
    identicals = merge.string.EnsureIdentical()
    in_lists   = merge.dictry.Append(separator)
    node_fuser = fuse.Members(base.Node,
            merge_ID    = use_key,
            merge_label = identicals,
            merge_prop  = in_lists,
        )

    nodes_fusioner = Reduce(node_fuser)
    fusioned_nodes = nodes_fusioner(nodes_congregater)
    # logger.debug("Fusioned nodes:")
    # for n in fusioned_nodes:
    #     logger.debug("\t"+repr(n))

    return fusioned_nodes, node_fuser.ID_mapping


def reconciliate_edges(edges, separator = None):
    """Operates a simple fusion on a list of edges.

    A "reconciliation" finds edges with duplicated source/target IDs & labels,
    and merge their properties without losing information.

    More precisely:
        - the edge Congregater uses serialize.SourceTargetLabel,
        - edges are merged members by members with fuse.Members, which uses:
            - merge.string.OrderedSet for IDs,
            - merge.string.EnsureIdentical for labels,
            - merge.dictry.Append for properties,
            - merge.string.UseLast for both id_source and id_target.

    Args:
        edges: a list of base.Edge

    Returns:
        the list of fused edges
    """

    # EDGES FUSION
    # Find duplicates
    on_STL = serialize.edge.SourceTargetLabel()
    edges_congregater = congregate.Edges(on_STL)
    edges_congregater(edges)

    # Fuse them
    set_of_ID       = merge.string.OrderedSet(separator)
    identicals      = merge.string.EnsureIdentical()
    in_lists        = merge.dictry.Append(separator)
    use_last_source = merge.string.UseLast()
    use_last_target = merge.string.UseLast()
    edge_fuser = fuse.Members(base.GenericEdge,
            merge_ID     = set_of_ID,
            merge_label  = identicals,
            merge_prop   = in_lists,
            merge_source = use_last_source,
            merge_target = use_last_target
        )

    edges_fusioner = Reduce(edge_fuser)
    fusioned_edges = edges_fusioner(edges_congregater)
    # logger.debug("Fusioned edges:")
    # for n in fusioned_edges:
    #     logger.debug("\t"+repr(n))

    return fusioned_edges


def reconciliate(nodes, edges, separator = None):
    """Operates a simple fusion on the given lists of elements.

    A "reconciliation" finds nodes with duplicated IDs
    (within source & target for the related edges),
    and merge their properties without losing information.

    Args:
        nodes: a list of Biocypher's node tuples
        edges: a list of Biocypher's edge tuples

    Returns:
        the list of fused node tuples and the list of fused edge tuples

    See reconciliate_nodes and reconciliate_edges for details.
    """

    fusioned_nodes, ID_mapping = reconciliate_nodes(nodes, separator = separator)

    # EDGES REMAP
    # If we use on_ID/use_key,
    # we shouldn't have any need to remap sources and target IDs in edges.
    assert(len(ID_mapping) == 0)
    # If one change this, you may want to remap like this:
    if len(ID_mapping) > 0:
        remaped_edges = remap_edges(edges, ID_mapping)
        # logger.debug("Remaped edges:")
        # for n in remaped_edges:
        #     logger.debug("\t"+repr(n))
    else:
        remaped_edges = edges

    fusioned_edges = reconciliate_edges(remaped_edges, separator = separator)

    # Return as tuples
    return [n.as_tuple() for n in fusioned_nodes], [e.as_tuple() for e in fusioned_edges]

