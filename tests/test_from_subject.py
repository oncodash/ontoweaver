import os
import sys
import logging
import subprocess

import pandas as pd
import pytest

import ontoweaver


@pytest.mark.parametrize("reverse_relation", [False, True])
def test_from_subject_skips_unknown_translation(reverse_relation):
    table = pd.DataFrame({
        "s": ["sA", "sB", "sC"],
        "x": ["known", "unknown", "known"],
        "y": ["y1", "y2", "y3"],
    })
    target = {
        "column": "y",
        "from_subject": "x",
        "to_object": "y",
        "via_relation": "x_y",
    }
    if reverse_relation:
        target["reverse_relation"] = "y_x"
    mapping = {
        "row": {"map": {"column": "s", "to_subject": "s"}},
        "transformers": [
            {"translate": {
                "column": "x",
                "to_object": "x",
                "via_relation": "s_x",
                "translations": {"known": "x1"},
                "on_unknown_value": "skip",
            }},
            {"map": target},
        ],
    }

    _, edges = ontoweaver.extract_table(table, mapping, affix="none")

    expected = {
        ("sA", "x1", "s_x"),
        ("sC", "x1", "s_x"),
        ("x1", "y1", "x_y"),
        ("x1", "y3", "x_y"),
    }
    if reverse_relation:
        expected.update({("y1", "x1", "y_x"), ("y3", "x1", "y_x")})
    assert {(edge.id_source, edge.id_target, edge.label) for edge in edges} == expected
    assert len(edges) == len(expected)


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

