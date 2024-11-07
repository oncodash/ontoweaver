import logging
from abc import abstractmethod, ABCMeta
from typing import Optional

from . import base
from . import fuse
from . import merge
from . import congregate
from . import serialize

class Fusioner(metaclass=ABCMeta):
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


def remap_edges(edges, node_fuser):
    assert(node_fuser.cls == base.Node)
    remaped_edges = []
    for et in edges:
        edge = base.GenericEdge.from_tuple(et, serialize.edge.All())

        s = node_fuser.ID_mapping.get(edge.id_source, None)
        if s:
            edge.id_source = s

        t = node_fuser.ID_mapping.get(edge.id_target, None)
        if t:
            edge.id_source = t

        remaped_edges.append(edge.as_tuple())

    return remaped_edges


def reconciliate(nodes, edges):

    # NODES FUSION
    # Find duplicates
    on_ID = serialize.ID()
    nodes_congregater = congregate.Nodes(on_ID)
    nodes_congregater(nodes)

    # Fuse them
    as_keys    = merge.string.UseKey()
    identicals = merge.string.EnsureIdentical()
    in_lists   = merge.dictry.Append()
    node_fuser = fuse.Members(base.Node,
            merge_ID    = as_keys,
            merge_label = identicals,
            merge_prop  = in_lists,
        )

    nodes_fusioner = Fusioner(node_fuser)
    fusioned_nodes = nodes_fusioner(nodes_congregater)
    logging.debug("Fusioned nodes:")
    for n in fusioned_nodes:
        logging.debug("\t"+repr(n))

    # EDGES REMAP
    remaped_edges = remap_edges(edges, node_fuser)
    logging.debug("Remaped edges:")
    for n in remaped_edges:
        logging.debug("\t"+repr(n))

    # EDGES FUSION
    # Find duplicates
    on_STL = serialize.edge.SourceTargetLabel()
    edges_congregater = congregate.Edges(on_STL)
    edges_congregater(remaped_edges)

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

    edges_fusioner = Fusioner(edge_fuser)
    fusioned_edges = edges_fusioner(edges_congregater)
    logging.debug("Fusioned edges:")
    for n in fusioned_edges:
        logging.debug("\t"+repr(n))

    # Return as tuples
    return [n.as_tuple() for n in fusioned_nodes], [e.as_tuple() for e in fusioned_edges]

