from ontoweaver import base
from ontoweaver import types as owtypes

class path(base.Transformer):
    """Custom end-user transformer, used to create elements for OmniPath KG database."""

    def __init__(self, properties_of, **kwargs):

        super().__init__(properties_of, **kwargs)

        # First declare all nodes and edges used in the branching logic.
        self.declare_types.make_node_class("protein", self.branching_properties.get("protein", {}))
        self.declare_types.make_node_class("target_protein", self.branching_properties.get("target_protein", {}))
        self.declare_types.make_node_class("target_complex", self.branching_properties.get("target_complex", {}))
        self.declare_types.make_node_class("source_protein", self.branching_properties.get("source_protein", {}))
        self.declare_types.make_node_class("macromolecular_complex", self.branching_properties.get("macromolecular_complex", {}))

        possible_sources = ["protein", "source_protein", "macromolecular_complex"]
        possible_targets = ["protein", "macromolecular_complex"]

        for possible_source in possible_sources:
            for possible_target in possible_targets:
                self.declare_types.make_edge_class("undirected_molecular_interaction", getattr(owtypes, possible_source), getattr(owtypes, possible_target), self.branching_properties.get("undirected_molecular_interaction", {}))
                self.declare_types.make_edge_class("stimulation", getattr(owtypes, possible_source), getattr(owtypes, possible_target), self.branching_properties.get("stimulation", {}))
                self.declare_types.make_edge_class("inhibition", getattr(owtypes, possible_source), getattr(owtypes, possible_target), self.branching_properties.get("inhibition", {}))


    def __call__(self, row, i):

        self.final_type = None
        self.properties_of = None

        # Extract branching information from the current row, as well as node ID.

        node_id = row["target"]
        consensus_direction = row["consensus_direction"]
        consensus_stimulation = row["consensus_stimulation"]
        entity = row["entity_type_target"]

        # Create branching logic and return correct elements.

        if consensus_direction == 0:
            if entity == "protein":
                self.final_type = getattr(owtypes, "protein")
                self.properties_of = self.branching_properties.get("target_protein", {})
                yield node_id, getattr(owtypes, "undirected_molecular_interaction"), getattr(owtypes, "target_protein"), None

            elif entity == "complex":
                self.final_type = getattr(owtypes, "macromolecular_complex")
                self.properties_of = self.branching_properties.get("target_complex", {})
                yield node_id,  getattr(owtypes, "undirected_molecular_interaction"), getattr(owtypes, "target_complex"), None


        elif consensus_direction == 1 and consensus_stimulation == 1:
            if entity == "protein":
                self.final_type = getattr(owtypes, "protein")
                self.properties_of = self.branching_properties.get("target_protein", {})
                yield node_id, getattr(owtypes, "stimulation"), getattr(owtypes, "target_protein"), None

            elif entity == "complex":
                self.final_type = getattr(owtypes, "macromolecular_complex")
                self.properties_of = self.branching_properties.get("target_complex", {})
                yield node_id,  getattr(owtypes, "stimulation"), getattr(owtypes, "target_complex"), None

        elif consensus_direction == 1 and consensus_stimulation == 0:
            if entity == "protein":
                self.final_type = getattr(owtypes, "protein")
                self.properties_of = self.branching_properties.get("target_protein", {})
                yield node_id, getattr(owtypes, "inhibition"), getattr(owtypes, "target_protein"), None

            elif entity == "complex":
                self.final_type = getattr(owtypes, "macromolecular_complex")
                self.properties_of = self.branching_properties.get("target_complex", {})
                yield node_id,  getattr(owtypes, "inhibition"), getattr(owtypes, "target_complex"), None

