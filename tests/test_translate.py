import logging
import yaml
import pandas as pd

import ontoweaver

directory_name = "simplest"

logging.debug("Load mapping...")
yaml_mapping = """
row:
    rowIndex:
        to_subject: variant
transformers:
    - translate:
        columns:
            - patient
        to_object: patient
        via_relation: patient_has_variant
        translations:
            A: a
            B: b
            C: c
"""

mapping = yaml.safe_load(yaml_mapping)

logging.debug("Load data...")
csv_file = "tests/" + directory_name + "/data.csv"
table = pd.read_csv(csv_file)

logging.debug("Run the adapter...")
adapter = ontoweaver.tabular.extract_all(table, mapping, affix="none")

assert(adapter)
assert(adapter.nodes)
assert(adapter.edges)

for n in adapter.nodes:
    logging.info(n)
