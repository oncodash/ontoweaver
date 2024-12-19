import logging
import yaml
import io
import pandas as pd

import ontoweaver

def test_singular_plural():

    logging.debug("Load data...")

    # Do not add newlines or spaces here
    # or else the parsing will be wrong.
    data = """Patient,Variant,Source
P1,V1-1,S0
P1,V1-2,S1
P2,V2-1,S2
P2,V2-2,S3"""
    csv = io.StringIO(data)
    table = pd.read_csv(csv)

    logging.debug("Load mappings...")

    plural_mapping = """
    row:
        map:
            columns:
                - Variant
            to_subject: variant
    transformers:
        - map:
            columns:
                - Patient
            to_object: patient
            via_relation: patient_has_variant
        - map:
            columns:
                - Source
            to_properties:
                - source
            for_objects:
                - variant
    """

    singular_mapping = """
    row:
        map:
            column: Variant
            to_subject: variant
    transformers:
        - map:
            column: Patient
            to_object: patient
            via_relation: patient_has_variant
        - map:
            column: Source
            to_property: source
            # Attach to subject by default.
    """

    plural_map = yaml.safe_load(plural_mapping)
    singular_map = yaml.safe_load(singular_mapping)


    logging.debug("Run the plural adapter...")
    plural_adapter = ontoweaver.tabular.extract_table(table, plural_map, affix="none")

    logging.debug("Run the singular adapter...")
    singular_adapter = ontoweaver.tabular.extract_table(table, singular_map, affix="none")

    assert(list(plural_adapter.nodes) == list(singular_adapter.nodes))
    assert(list(plural_adapter.edges) == list(singular_adapter.edges))

if __name__ == "__main__":
    test_singular_plural()

