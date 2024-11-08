import logging
from abc import abstractmethod, ABCMeta
from typing import Optional

from . import base
from . import fuse
from . import merge
from . import congregate
from . import serialize

class Fusioner(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, congregater: congregate.Congregater):
        raise NotImplementedError


class Reduce(Fusioner):
    def __init__(self, fuser: fuse.Fuser):
        self.fuser = fuser

    def __call__(self, congregater: congregate.Congregater):
        fusioned = set()
        for key, elem_list in congregater.duplicates.items():
            self.fuser.reset()
            logging.debug(f"Fusion of {type(congregater).__name__} with {type(congregater.serializer).__name__} for key: `{key}`")
            assert(elem_list)
            assert(len(elem_list) > 0)

            # Manual functools.reduce without initial state.
            it = iter(elem_list)
            lhs = next(it)
            logging.debug(f"  Fuse `{lhs}`...")
            logging.debug(f"    with itself: {repr(lhs)}")
            self.fuser(key, lhs, lhs)
            logging.debug(f"      = {repr(self.fuser.get())}")
            for rhs in it:
                logging.debug(f"    with `{rhs}`: {repr(rhs)}")
                self.fuser(key, lhs, rhs)
                logging.debug(f"      = {repr(self.fuser.get())}")

            # Convert to final string.
            f = self.fuser.get()
            assert(issubclass(type(f), base.Element))
            fusioned.add(f)
        return fusioned


def remap_edges(edges, ID_mapping):
    assert(node_fuser.cls == base.Node)
    remaped_edges = []
    for et in edges:
        edge = base.GenericEdge.from_tuple(et, serialize.edge.All())

        s = ID_mapping.get(edge.id_source, None)
        if s:
            edge.id_source = s

        t = ID_mapping.get(edge.id_target, None)
        if t:
            edge.id_source = t

        remaped_edges.append(edge.as_tuple())

    return remaped_edges


def reconciliate_nodes(nodes):

    # NODES FUSION
    # Find duplicates
    on_ID = serialize.ID()
    nodes_congregater = congregate.Nodes(on_ID)
    nodes_congregater(nodes)

    # Fuse them
    use_key    = merge.string.UseKey()
    identicals = merge.string.EnsureIdentical()
    in_lists   = merge.dictry.Append()
    node_fuser = fuse.Members(base.Node,
            merge_ID    = use_key,
            merge_label = identicals,
            merge_prop  = in_lists,
        )

    nodes_fusioner = Reduce(node_fuser)
    fusioned_nodes = nodes_fusioner(nodes_congregater)
    # logging.debug("Fusioned nodes:")
    # for n in fusioned_nodes:
    #     logging.debug("\t"+repr(n))

    return fusioned_nodes, node_fuser.ID_mapping


def reconciliate_edges(edges):

    # EDGES FUSION
    # Find duplicates
    on_STL = serialize.edge.SourceTargetLabel()
    edges_congregater = congregate.Edges(on_STL)
    edges_congregater(edges)

    # Fuse them
    set_of_ID       = merge.string.OrderedSet(";")
    identicals      = merge.string.EnsureIdentical()
    in_lists        = merge.dictry.Append()
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
    # logging.debug("Fusioned edges:")
    # for n in fusioned_edges:
    #     logging.debug("\t"+repr(n))

    return fusioned_edges


def reconciliate(nodes, edges):

    fusioned_nodes, ID_mapping = reconciliate_nodes(nodes)

    # EDGES REMAP
    # If we use on_ID/use_key,
    # we shouldn't have any need to remap sources and target IDs in edges.
    assert(len(ID_mapping) == 0)
    # If one change this, you may want to remap like this:
    if len(ID_mapping) > 0:
        remaped_edges = remap_edges(edges, ID_mapping)
        # logging.debug("Remaped edges:")
        # for n in remaped_edges:
        #     logging.debug("\t"+repr(n))
    else:
        remaped_edges = edges

    fusioned_edges = reconciliate_edges(remaped_edges)

    # Return as tuples
    return [n.as_tuple() for n in fusioned_nodes], [e.as_tuple() for e in fusioned_edges]

