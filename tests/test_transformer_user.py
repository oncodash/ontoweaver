import logging
import yaml
import pandas as pd

import ontoweaver

class user_transformer(ontoweaver.base.Transformer):
    def __init__(self, properties_of, branching_properties=None, columns=None, **kwargs):
        super().__init__(properties_of, branching_properties, columns, **kwargs)

    def __call__(self, row, i):
        for key in self.columns:
            res, edge, node = self.create(row[key], self.multi_type_transformer)
            if res:
                yield res, edge, node
            else:
                pass

def test_transformer_user():
    # Add the passed transformer to the list available to OntoWeaver.
    ontoweaver.transformer.register(user_transformer)

    directory_name = "simplest"

    logging.debug("Load mapping...")
    yaml_mapping = """
    row:
        rowIndex:
            to_subject: variant
    transformers:
        - user_transformer:
            columns:
                - patient
            to_object: patient
            via_relation: patient_has_variant
    """

    mapping = yaml.safe_load(yaml_mapping)

    logging.debug("Load data...")
    csv_file = "tests/" + directory_name + "/data.csv"
    table = pd.read_csv(csv_file)

    logging.debug("Run the adapter...")
    adapter = ontoweaver.tabular.extract_table(table, mapping, affix="none")


if __name__ == "__main__":
    test_transformer_user()
