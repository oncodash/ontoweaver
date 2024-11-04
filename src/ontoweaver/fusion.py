import logging
from abc import abstractmethod, ABCMeta
from typing import Optional
import functools
from ontoweaver import base


class Fuse(metaclass=ABCMeta):

    def __init__(self, dict_duplicates, fuser: base.Fuser):
        self.dict_duplicates = dict_duplicates
        self.result = []
        self.fuser = fuser

    def __call__(self):
        for key_element, element_list in self.dict_duplicates.items():
            type_e = type(key_element)
            if issubclass(type_e, base.Edge):
                logging.debug(
                    f"Initiating property merging for: `{type_e}` from source: `{key_element._id_source}` to target: `{key_element._id_target}`.")
            elif issubclass(type_e, base.Node):
                logging.debug(f"Initiating property merging for: `{type_e}` with id: `{key_element.id}`.")
            # Only element_list is passed because the value of key_element is also stored in the list. Key is only used for indexing.
            merged_properties = functools.reduce(self.fuser, element_list, {})
            result_e = type_e(**key_element.serialize(properties=merged_properties))
            self.result.append(result_e.as_tuple())


class FuseID(Fuse):

    def __init__(self,
                 duplicates: Duplicates,
                 ):

        self.dict_duplicates = duplicates.dict_duplicates if duplicates else {}

    def __call__(self, id_conversion_dict):

        # FIXME add ASSERTS at beginnings and ends of fucntions to check if assumptions are correct .

        nodes_to_update = {}

        for node in self.dict_duplicates.keys():
            new_id = id_conversion_dict.get(node.id, None)
            if new_id:
                logging.debug(f"Converting node id `{node.id}` to `{id_conversion_dict[node.id]}`.")
                new_node = base.Node(new_id, node.properties, node.label, node.hash_rep)



                if new_node in self.duplicate_node_dict.keys():
                    for n in self.duplicate_node_dict[node]:
                        new_n = base.Node(new_id, n.properties, n.label, n.hash_rep)
                        self.duplicate_node_dict[new_node].extend([new_n])
                    del self.duplicate_node_dict[node]
                else:
                    nodes_to_update[new_node] = []
                    for n in self.duplicate_node_dict[node]:
                        new_n = base.Node(new_id, n.properties, n.label, n.hash_rep)
                        nodes_to_update[new_node].append(new_n)
                    del self.duplicate_node_dict[node]

                self._update_edges(node.id, new_id)


        self.duplicate_node_dict.update(nodes_to_update)

    def _update_edges(self, old_id, new_id):
        edges_to_update = {}
        edges_to_remove = []

        for edge in list(self.duplicate_edge_dict.keys()):
            if edge._id_source == old_id:
                logging.debug(f"Converting edge source id `{edge._id_source}` to `{new_id}`.")
                new_edge = base.Edge(edge.id, new_id, edge._id_target, edge.properties, edge.label, edge.hash_rep)
                if new_edge not in edges_to_update:
                    edges_to_update[new_edge] = []

                for value in self.duplicate_edge_dict[edge]:
                    new_e = base.Edge(value.id, new_id, value._id_target, value.properties, value.label, value.hash_rep)
                    edges_to_update[new_edge].append(new_e)

                edges_to_remove.append(edge)

            elif edge._id_target == old_id:
                logging.debug(f"Converting edge target id `{edge._id_target}` to `{new_id}`.")
                new_edge = base.Edge(edge.id, edge._id_source, new_id, edge.properties, edge.label, edge.hash_rep)
                if new_edge not in edges_to_update:
                    edges_to_update[new_edge] = []

                for value in self.duplicate_edge_dict[edge]:
                    new_e = base.Edge(value.id, value._id_source, new_id, value.properties, value.label, value.hash_rep)
                    edges_to_update[new_edge].append(new_e)

                edges_to_remove.append(edge)

        for edge in edges_to_remove:
            del self.duplicate_edge_dict[edge]

        self.duplicate_edge_dict.update(edges_to_update)



class FuseType(Fuse):

    # TODO: Implement this class with ontology access.

    def __init__(self, duplicate_node_dict, duplicate_edge_dict):
        self.duplicate_node_dict = duplicate_node_dict
        self.duplicate_edge_dict = duplicate_edge_dict
        self.result = []

    def __call__(self):
        pass
