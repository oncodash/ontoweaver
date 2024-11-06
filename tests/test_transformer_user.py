import logging
import yaml
import pandas as pd

import ontoweaver

class user_transformer(ontoweaver.base.Transformer):
    def __init__(self, target, properties_of, edge=None, columns=None, **kwargs):
        super().__init__(target, properties_of, edge, columns, **kwargs)

    def __call__(self, row, i):
        for key in self.columns:
            yield str(row[key])

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
adapter = ontoweaver.tabular.extract_all(table, mapping, affix="none")


