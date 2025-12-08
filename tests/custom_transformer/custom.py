
from ontoweaver import transformer, validate
import types

class OmniPath(transformer.Transformer):
    """Custom end-user transformer, used to create elements for OmniPath KG database."""

    def __init__(self, properties_of, value_maker = None, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, **kwargs):

        super().__init__(properties_of, value_maker, label_maker, branching_properties, columns, output_validator,
                         multi_type_dict, raise_errors=raise_errors, **kwargs)

        # First declare all nodes and edges used in the branching logic.
        self.declare_types.make_node_class("protein", self.branching_properties.get("protein", {}))
        self.declare_types.make_node_class("target_protein", self.branching_properties.get("target_protein", {}))
        self.declare_types.make_node_class("target_complex", self.branching_properties.get("target_complex", {}))
        self.declare_types.make_node_class("source_protein", self.branching_properties.get("source_protein", {}))
        self.declare_types.make_node_class("mirna", self.branching_properties.get("mirna", {}))
        self.declare_types.make_node_class("lncrna", self.branching_properties.get("lncrna", {}))
        self.declare_types.make_node_class("drug", self.branching_properties.get("drug", {}))
        self.declare_types.make_node_class("macromolecular_complex", self.branching_properties.get("macromolecular_complex", {}))

        possible_sources = ["protein", "source_protein", "mirna", "lncrna", "drug", "macromolecular_complex"]
        possible_targets = ["protein", "macromolecular_complex", "mirna"]

        for possible_source in possible_sources:
            for possible_target in possible_targets:
                self.declare_types.make_edge_class("transcriptional", getattr(types, possible_source), getattr(types, possible_target), self.branching_properties.get("transcriptional", {}))
                self.declare_types.make_edge_class("post_translational", getattr(types, possible_source), getattr(types, possible_target), self.branching_properties.get("post_translational", {}))
                self.declare_types.make_edge_class("post_transcriptional", getattr(types, possible_source), getattr(types, possible_target), self.branching_properties.get("post_transcriptional", {}))
                self.declare_types.make_edge_class("drug_has_target", getattr(types, possible_source), getattr(types, possible_target), self.branching_properties.get("drug_has_target", {}))
                self.declare_types.make_edge_class("mirna_transcriptional", getattr(types, possible_source), getattr(types, possible_target), self.branching_properties.get("mirna_transcriptional", {}))
                self.declare_types.make_edge_class("lncrna_post_transcriptional", getattr(types, possible_source), getattr(types, possible_target), self.branching_properties.get("lncrna_post_transcriptional", {}))


    def __call__(self, row, i):

        self.final_type = None
        self.properties_of = None

        # Extract branching information from the current row, as well as node ID.

        node_id = row["target"]
        relationship_type = row["type"]
        entity = row["entity_type_target"]

        # Create branching logic and return correct elements.

        if relationship_type == "transcriptional":
            if entity == "protein":
                self.final_type = getattr(types, "protein")
                self.properties_of = self.branching_properties.get("target_protein", {})
                yield node_id, getattr(types, "transcriptional"), getattr(types, "target_protein"), None

            elif entity == "complex":
                self.final_type = getattr(types, "macromolecular_complex")
                self.properties_of = self.branching_properties.get("target_complex", {})
                yield node_id,  getattr(types, "transcriptional"), getattr(types, "target_complex"), None

            elif entity == "mirna":
                self.properties_of = self.branching_properties.get("mirna", {})
                yield node_id,   getattr(types, "transcriptional"), getattr(types, "mirna"), None


        elif relationship_type == "post_translational":
            if entity == "protein":
                self.final_type = getattr(types, "protein")
                self.properties_of = self.branching_properties.get("target_protein", {})
                yield node_id, getattr(types, "post_translational"), getattr(types, "target_protein"), None

            elif entity == "complex":
                self.final_type = getattr(types, "macromolecular_complex")
                self.properties_of = self.branching_properties.get("target_complex", {})
                yield node_id, getattr(types, "post_translational"), getattr(types, "target_complex"), None


        elif relationship_type == "post_transcriptional":
            self.final_type = getattr(types, "protein")
            self.properties_of = self.branching_properties.get("target_protein", {})
            yield node_id, getattr(types, "post_transcriptional"), getattr(types, "target_protein"), None

        elif relationship_type == "small_molecule_protein":
            if entity == "protein":
                self.final_type = getattr(types, "protein")
                self.properties_of = self.branching_properties.get("target_protein", {})
                yield node_id, getattr(types, "drug_has_target"), getattr(types, "target_protein"), None

            elif entity == "complex":
                self.final_type = getattr(types, "macromolecular_complex")
                self.properties_of = self.branching_properties.get("target_complex", {})
                yield node_id, getattr(types, "drug_has_target"), getattr(types, "target_complex"), None

        elif relationship_type == "mirna_transcriptional":
            self.properties_of = self.branching_properties.get("mirna", {})
            yield node_id, getattr(types, "mirna_transcriptional"), getattr(types, "mirna"), None

        elif relationship_type == "lncrna_post_transcriptional":
            self.final_type = getattr(types, "protein")
            self.properties_of = self.branching_properties.get("target_protein", {})
            yield node_id, getattr(types, "lncrna_post_transcriptional"), getattr(types, "target_protein"), None
