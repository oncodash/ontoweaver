import logging
import io
import yaml
import pandas as pd

import ontoweaver

class simplest(ontoweaver.base.Transformer):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.declare_types.make_node_class("patient")
        self.declare_types.make_node_class("variant")

        self.declare_types.make_edge_class("patient_has_variant", "patient", "variant")

    def __call__(self, row, i):
        yield self.create(str(row["patient"]), row)


def test_transformer_simplest():
    # Add the passed transformer to the list available to OntoWeaver.
    ontoweaver.transformer.register(simplest)

    logging.debug("Load mapping...")
    yaml_mapping = """
    row:
        map:
            column: variant
            to_subject: variant
    transformers:
        - simplest:
            to_object: patient
            via_relation: patient_has_variant
    """

    mapping = yaml.safe_load(yaml_mapping)

    logging.debug("Load data...")
    data = """variant,patient
A,P1
B,P2
"""
    table = pd.read_csv(io.StringIO(data))

    logging.debug("Run the adapter...")
    adapter = ontoweaver.extract_table(table, mapping)


if __name__ == "__main__":
    test_transformer_iftypes()

