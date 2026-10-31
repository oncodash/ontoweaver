import os
import sys
import logging
import subprocess

import ontoweaver
import pandas as pd
import yaml


def test_from_subject():
    logging.debug(f"From: {os.getcwd()}")
    d = "./tests/from_subject"
    cmd=f"ontoweave {d}/path.csv:{d}/path.yaml --type-affix suffix --biocypher-schema {d}/schema.yaml --biocypher-config {d}/biocypher_config.yaml --register {d}/path.py --debug --log-level DEBUG"
    logging.debug(f"Run: {cmd}")

    proc = subprocess.run(cmd.split(), capture_output=True)
    logging.error(proc.stderr.decode())
    assert proc.returncode == 0

    import_file = proc.stdout.decode()
    logging.debug(import_file)

    # assert os.path.isfile(import_file)
    # with open(import_file) as fd:
    #     assert fd.readlines()

    # dir = os.path.dirname(import_file)

    # for f in [
    #     # f"{dir}/inhibition.csv",
    #     f"{dir}/stimulation.csv",
    #     f"{dir}/transcript_to_gene_relationship.csv",
    #     f"{dir}/undirected_molecular_interaction.csv"
    # ]:
    #     assert os.path.isfile(f)
    #     with open(f) as fd:
    #         assert fd.readlines()


def test_from_subject_skips_when_subject_transformer_skips():
    table = pd.DataFrame(
        {
            "variant_id": ["variant-a", "variant-b"],
            "patient": ["known", "unknown"],
        }
    )
    mapping = yaml.safe_load(
        """
        row:
            rowIndex:
                to_subject: row
        transformers:
            - translate:
                column: patient
                translations:
                    known: translated-patient
                on_unknown_value: skip
                to_object: patient
                via_relation: row_has_patient
            - map:
                column: variant_id
                from_subject: patient
                to_object: variant
                via_relation: patient_has_variant
        """
    )

    nodes, edges = ontoweaver.extract_table(table, mapping, affix="none")

    assert {node.id for node in nodes if node.label == "variant"} == {"variant-a"}
    assert {
        (edge.id_source, edge.id_target)
        for edge in edges
        if edge.label == "patient_has_variant"
    } == {("translated-patient", "variant-a")}
